#!/usr/bin/env python3

from trojanzoo.datasets import Dataset
from trojanvision.environ import env
from trojanvision.utils.transform import (get_transform_bit,
                                          get_transform_imagenet,
                                          get_transform_cifar,
                                          RandomMixup,
                                          RandomCutmix)

import torch
import torchvision.transforms as transforms
from torch.utils.data.dataloader import default_collate
import argparse
import os

from typing import TYPE_CHECKING
from typing import Iterable
from torchvision.datasets import VisionDataset  # TODO: python 3.10
import PIL.Image as Image
from collections import Callable
if TYPE_CHECKING:
    import torch.utils.data


class ImageSet(Dataset):

    name: str = 'imageset'
    data_type: str = 'image'
    num_classes = 1000
    data_shape = [3, 224, 224]

    @classmethod
    def add_argument(cls, group: argparse._ArgumentGroup):
        super().add_argument(group)
        group.add_argument(
            '--dataset_normalize', dest='normalize', action='store_true',
            help='use transforms.Normalize in dataset transform. '
            '(It\'s used in model as the first layer by default.)')
        group.add_argument('--transform', choices=[None, 'none', 'bit', 'pytorch'])
        group.add_argument('--auto_augment', action='store_true',
                           help='use auto augment')
        group.add_argument('--mixup', action='store_true', help='use mixup')
        group.add_argument('--mixup_alpha', type=float, help='mixup alpha (default: 0.0)')
        group.add_argument('--cutmix', action='store_true', help='use cutmix')
        group.add_argument('--cutmix_alpha', type=float, help='cutmix alpha (default: 0.0)')
        group.add_argument('--cutout', action='store_true', help='use cutout')
        group.add_argument('--cutout_length', type=int, help='cutout length')
        return group

    def __init__(self, norm_par: dict[str, list[float]] = None,
                 default_model: str = 'resnet18_comp',
                 normalize: bool = False, transform: str = None,
                 auto_augment: bool = False,
                 mixup: bool = False, mixup_alpha: float = 0.0,
                 cutmix: bool = False, cutmix_alpha: float = 0.0,
                 cutout: bool = False, cutout_length: int = None,
                 **kwargs):
        self.norm_par: dict[str, list[float]] = norm_par
        self.normalize = normalize
        self.transform = transform
        self.auto_augment = auto_augment
        self.mixup = mixup
        self.mixup_alpha = mixup_alpha
        self.cutmix = cutmix
        self.cutmix_alpha = cutmix_alpha
        self.cutout = cutout
        self.cutout_length = cutout_length

        self.collate_fn: Callable[[Iterable[torch.Tensor]], Iterable[torch.Tensor]] = None
        mixup_transforms = []
        if mixup:
            mixup_transforms.append(RandomMixup(self.num_classes, p=1.0, alpha=mixup_alpha))
        if cutmix:
            mixup_transforms.append(RandomCutmix(self.num_classes, p=1.0, alpha=cutmix_alpha))
        if len(mixup_transforms):
            mixupcutmix = mixup_transforms[0] if len(mixup_transforms) == 1 \
                else transforms.RandomChoice(mixup_transforms)

            def collate_fn(batch: Iterable[torch.Tensor]) -> Iterable[torch.Tensor]:
                return mixupcutmix(*default_collate(batch))  # noqa: E731
            self.collate_fn = collate_fn

        super().__init__(default_model=default_model, **kwargs)
        self.param_list['imageset'] = ['data_shape', 'norm_par',
                                       'normalize', 'transform',
                                       'auto_augment']
        if cutout:
            self.param_list['imageset'].append('cutout_length')

        if mixup:
            self.param_list['imageset'].append('mixup_alpha')
        if cutmix:
            self.param_list['imageset'].append('cutmix_alpha')

    def get_transform(self, mode: str, normalize: bool = None
                      ) -> transforms.Compose:
        normalize = normalize if normalize is not None else self.normalize
        if self.transform == 'bit':
            return get_transform_bit(mode, self.data_shape)
        elif self.data_shape == [3, 224, 224]:
            transform = get_transform_imagenet(
                mode, use_tuple=self.transform != 'pytorch',
                auto_augment=self.auto_augment)
        elif self.transform != 'none' and self.data_shape in ([3, 16, 16], [3, 32, 32]):
            transform = get_transform_cifar(
                mode, auto_augment=self.auto_augment,
                cutout=self.cutout, cutout_length=self.cutout_length,
                data_shape=self.data_shape)
        else:
            transform = transforms.Compose([transforms.ToTensor()])
        if normalize and self.norm_par is not None:
            transform.transforms.append(transforms.Normalize(
                mean=self.norm_par['mean'], std=self.norm_par['std']))
        return transform

    def get_dataloader(self, mode: str = None, dataset: Dataset = None,
                       batch_size: int = None, shuffle: bool = None,
                       num_workers: int = None, pin_memory=True,
                       drop_last=False, collate_fn=None,
                       **kwargs) -> torch.utils.data.DataLoader:
        if batch_size is None:
            batch_size = self.test_batch_size if mode == 'test' \
                else self.batch_size
        if shuffle is None:
            shuffle = True if mode == 'train' else False
        if num_workers is None:
            num_workers = self.num_workers
        if dataset is None:
            dataset = self.get_dataset(mode, **kwargs)
        if env['num_gpus'] == 0:
            pin_memory = False
        collate_fn = collate_fn or self.collate_fn
        return torch.utils.data.DataLoader(
            dataset, batch_size=batch_size, shuffle=shuffle,
            num_workers=num_workers, pin_memory=pin_memory,
            drop_last=drop_last, collate_fn=collate_fn)

    @staticmethod
    def get_data(data: tuple[torch.Tensor, torch.Tensor],
                 **kwargs) -> tuple[torch.Tensor, torch.Tensor]:
        return (data[0].to(env['device'], non_blocking=True),
                data[1].to(env['device'], dtype=torch.long, non_blocking=True))

    def get_class_to_idx(self, **kwargs) -> dict[str, int]:
        if hasattr(self, 'class_to_idx'):
            return getattr(self, 'class_to_idx')
        return {str(i): i for i in range(self.num_classes)}

    def make_folder(self, img_type: str = '.png', **kwargs):
        mode_list: list[str] = [
            'train', 'valid'] if self.valid_set else ['train']
        class_to_idx = self.get_class_to_idx(**kwargs)
        idx_to_class = {v: k for k, v in class_to_idx.items()}
        for mode in mode_list:
            dataset: VisionDataset = self.get_org_dataset(mode, transform=None)
            class_counters = [0] * self.num_classes
            for image, target_class in list(dataset):
                image: Image.Image
                target_class: int
                class_name = idx_to_class[target_class]
                _dir = os.path.join(
                    self.folder_path, self.name, mode, class_name)
                if not os.path.exists(_dir):
                    os.makedirs(_dir)
                image.save(os.path.join(
                    _dir, f'{class_counters[target_class]}{img_type}'))
                class_counters[target_class] += 1
