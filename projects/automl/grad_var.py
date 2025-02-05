#!/usr/bin/env python3

import trojanvision

import torch
import numpy as np
import argparse

import time

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
    # loss, acc1 = model._validate()

    model.activate_params(model.parameters())
    model.zero_grad()

    torch.random.manual_seed(int(time.time()))
    grad_x = None
    grad_xx = None
    n_sample = 512

    loader = dataset.get_dataloader('valid', shuffle=True,
                                    batch_size=1, drop_last=True)
    for i, data in enumerate(loader):
        if i >= n_sample:
            break
        _input, _label = model.get_data(data)
        loss = model.loss(_input, _label)
        loss.backward()
        grad_temp_list = []
        for param in model.parameters():
            grad_temp_list.append(param.grad.flatten())
        grad = torch.cat(grad_temp_list)
        grad = grad if grad.norm(p=2) <= 5.0 else grad / grad.norm(p=2) * 5.0
        grad_temp = grad.detach().cpu().clone()
        if grad_x is None:
            grad_x = grad_temp / n_sample
            grad_xx = grad_temp.square() / n_sample
        else:
            grad_x += grad_temp / n_sample
            grad_xx += grad_temp.square() / n_sample
        model.zero_grad()

    model.eval()
    model.activate_params([])

    grad_tensor = trojanvision.to_numpy(grad_xx - grad_x.square())
    grad_tensor[grad_tensor < 0] = 0
    var = float(np.sum(np.sqrt(grad_tensor)))

    print(f'{model.name:20}  {var:f}')
