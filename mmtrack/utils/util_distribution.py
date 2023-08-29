# Copyright (c) OpenMMLab. All rights reserved.
import torch
from mmengine.model import MMDataParallel, MMDistributedDataParallel

dp_factory = {'cuda': MMDataParallel, 'cpu': MMDataParallel}

ddp_factory = {'cuda': MMDistributedDataParallel}


def build_dp(model, device='cuda', dim=0, *args, **kwargs):
    """build DataParallel module by device type.

    if device is cuda, return a MMDataParallel model; if device is npu,
    return a NPUDataParallel model.
    Args:
        model (:class:`nn.Module`): model to be parallelized.
        device (str): device type, cuda, cpu or npu. Defaults to cuda.
        dim (int): Dimension used to scatter the data. Defaults to 0.
    Returns:
        nn.Module: the model to be parallelized.
    """
    if device == 'npu':
        from mmcv.device.npu import NPUDataParallel
        dp_factory['npu'] = NPUDataParallel
        torch.npu.set_device(kwargs['device_ids'][0])
        torch.npu.set_compile_mode(jit_compile=False)
        model = model.npu()
    elif device == 'cuda':
        model = model.cuda(kwargs['device_ids'][0])

    return dp_factory[device](model, dim=dim, *args, **kwargs)


def build_ddp(model, device='cuda', *args, **kwargs):
    """Build DistributedDataParallel module by device type.
    If device is cuda, return a MMDistributedDataParallel model;
    if device is npu, return a NPUDistributedDataParallel model.
    Args:
        model (:class:`nn.Module`): module to be parallelized.
        device (str): device type, npu or cuda.
    Returns:
        :class:`nn.Module`: the module to be parallelized
    References:
        .. [1] https://pytorch.org/docs/stable/generated/torch.nn.parallel.
                     DistributedDataParallel.html
    """
    assert device in ['cuda', 'npu'], 'Only available for cuda or npu devices.'
    if device == 'npu':
        from mmcv.device.npu import NPUDistributedDataParallel
        torch.npu.set_compile_mode(jit_compile=False)
        ddp_factory['npu'] = NPUDistributedDataParallel
        model = model.npu()
    elif device == 'cuda':
        model = model.cuda()

    return ddp_factory[device](model, *args, **kwargs)


def is_npu_available():
    """Returns a bool indicating if NPU is currently available."""
    return hasattr(torch, 'npu') and torch.npu.is_available()


def get_device():
    """Returns an available device, cpu, cuda or npu."""
    is_device_available = {
        'npu': is_npu_available(),
        'cuda': torch.cuda.is_available()
    }
    device_list = [k for k, v in is_device_available.items() if v]
    return device_list[0] if len(device_list) >= 1 else 'cpu'
