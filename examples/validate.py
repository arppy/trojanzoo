#!/usr/bin/env python3

# CUDA_VISIBLE_DEVICES=0 python examples/validate.py --color --verbose 1 --dataset cifar10 --pretrain --model resnet18_comp

import trojanvision
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    trojanvision.environ.add_argument(parser)
    trojanvision.datasets.add_argument(parser)
    trojanvision.models.add_argument(parser)
    args = parser.parse_args()

    env = trojanvision.environ.create(**args.__dict__)
    dataset = trojanvision.datasets.create(**args.__dict__)
    model = trojanvision.models.create(dataset=dataset, **args.__dict__)

    if env['verbose']:
        trojanvision.summary(env=env, dataset=dataset, model=model)
    loss, acc1 = model._validate()
