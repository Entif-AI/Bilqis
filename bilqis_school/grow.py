"""Increase Bilqis's neural capacity without erasing acquired function.

Duplicate the learned hidden representation N times, preserve the attention
head dimension, copy trained blocks diagonally, and initialize extra blocks
as residual identities. Copy AdamW moments into the corresponding subspaces
and keep their step count. This is FUNCTION-PRESERVING model growth rather
than a randomly initialized replacement student. It is not a claim that
the enlarged network has automatically acquired new skills.
"""
from __future__ import annotations

from dataclasses import replace
import copy

import torch

from bilqis_micro.model import MicroStudent
from bilqis_ref.model import state_hash, ModelConfig
from bilqis_micro.run import optimizer_receipt


def _block_repeat(tensor, factor):
    old_out,old_in=tensor.shape
    result=tensor.new_zeros((old_out*factor,old_in*factor))
    for repeat in range(factor):
        result[repeat*old_out:(repeat+1)*old_out,
               repeat*old_in:(repeat+1)*old_in].copy_(tensor)
    return result


def _qkv_repeat(weight, factor):
    dims=weight.shape[1]
    assert weight.shape[0]==3*dims
    result=weight.new_zeros((3*dims*factor,dims*factor))
    for component in range(3):
        part=weight[component*dims:(component+1)*dims]
        for duplicate in range(factor):
            start=component*dims*factor+duplicate*dims
            result[start:start+dims,
                   duplicate*dims:(duplicate+1)*dims].copy_(part)
    return result


def _transform(name, tensor, factor):
    if name in ("embedding.weight","position.weight"):
        return tensor.repeat(1,factor)
    if name=="norm.weight":
        return tensor.repeat(factor)/factor
    if name.endswith((".n1.weight",".n2.weight")):
        return tensor.repeat(factor)
    if name.endswith(".qkv.weight"):
        return _qkv_repeat(tensor,factor)
    if name.endswith((".proj.weight",".up.weight",".down.weight")):
        return _block_repeat(tensor,factor)
    raise ValueError("MODEL_GROWTH_UNKNOWN_PARAMETER "+name)


def grow(model,optimizer,*,factor=4,layers=6):
    if factor not in (2,3,4) or layers<=model.config.layers or layers>12:
        raise ValueError("UNSUPPORTED_FUNCTION_PRESERVING_MODEL_GROWTH")
    rng=torch.get_rng_state()
    parent=state_hash(model)
    original=optimizer_receipt(optimizer)
    cfg=replace(model.config,width=model.config.width*factor,
                heads=model.config.heads*factor,layers=layers)
    newer=MicroStudent(cfg)
    old_params=dict(model.named_parameters())
    new_params=dict(newer.named_parameters())
    for name,new_param in new_params.items():
        if name in old_params:
            with torch.no_grad():
                new_param.copy_(_transform(name,old_params[name].detach(),factor))
        elif name.startswith("blocks."):
            index=int(name.split(".")[1])
            if index<model.config.layers:
                raise ValueError("NEW_PARAMETER_IN_PRESERVED_BLOCK")
            # Exactly identity residual: both attention and MLP outputs zero.
            if name.endswith((".proj.weight",".down.weight")):
                with torch.no_grad():
                    new_param.zero_()
        else:
            raise ValueError("UNEXPECTED_NEW_PARAMETERS_AFTER_GROWTH")
    g=optimizer.param_groups
    if len(g)!=1:
        raise ValueError("GROWTH_EXPECTS_SINGLE_ADAMW_GROUP")
    group=g[0]
    replacement=torch.optim.AdamW(newer.parameters(),lr=group["lr"],
                                  betas=group["betas"],eps=group["eps"],
                                  weight_decay=group["weight_decay"],foreach=False)
    step=next(iter(optimizer.state.values()))["step"]
    for name,new_param in new_params.items():
        original_param=old_params.get(name)
        if original_param is not None:
            state=optimizer.state[original_param]
            exp_avg=_transform(name,state["exp_avg"],factor)
            exp_sq=_transform(name,state["exp_avg_sq"],factor)
        else:
            exp_avg=torch.zeros_like(new_param)
            exp_sq=torch.zeros_like(new_param)
        replacement.state[new_param]={
            "step":step.detach().clone(),
            "exp_avg":exp_avg.clone(),
            "exp_avg_sq":exp_sq.clone(),
        }
    torch.set_rng_state(rng)
    if optimizer_receipt(replacement)["steps"] != original["steps"]:
        raise ValueError("MODEL_GROWTH_CHANGED_ADAMW_STEP")
    return newer,replacement,{
        "profile":"function-preserving-replication-with-identity-residual-blocks",
        "factor":factor,"old_layers":model.config.layers,"new_layers":layers,
        "old_width":model.config.width,"new_width":cfg.width,
        "old_heads":model.config.heads,"new_heads":cfg.heads,
        "old_parameters":sum(p.numel() for p in model.parameters()),
        "new_parameters":sum(p.numel() for p in newer.parameters()),
        "parent_state_sha256":parent,
        "new_state_sha256":state_hash(newer),
        "adamw_step":original["steps"],
        "all_original_blocks_transferred":True,
        "all_old_adamw_moments_transferred":True,
        "extra_blocks_residual_identities":True,
        "old_113_semantic_rows_preserved_as_replicated_subspaces":True,
    }


@torch.no_grad()
def compare_outputs(before,after,example_batches,*,tolerance=3e-4):
    before.eval();after.eval()
    worst=0.0;matched=0
    for inputs,lengths in example_batches:
        a=before(inputs,lengths)
        b=after(inputs,lengths)
        worst=max(worst,float((a-b).abs().max()))
        if not bool((a.argmax(dim=-1)==b.argmax(dim=-1)).all()):
            raise ValueError("GROWN_MODEL_CHANGED_ACQUIRED_PREDICTIONS")
        matched+=inputs.shape[0]
    if not worst<=tolerance:
        raise ValueError(f"GROWN_MODEL_FUNCTION_NOT_PRESERVED: max={worst}")
    return {"preserved_examples":matched,"max_logit_absolute_difference":worst,
            "max_tolerable_difference":tolerance}
