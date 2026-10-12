"""Resize only the live embedding parameter; keep trained weights and AdamW history."""
from __future__ import annotations

import copy
from dataclasses import asdict,replace

import torch
from torch import nn

from bilqis_logic.geometry import tensor_hash
from bilqis_micro.graph import validate_catalog,compile_embeddings
from bilqis_micro.model import MicroStudent
from bilqis_micro.run import optimizer_receipt
from bilqis_ref.model import ModelConfig,state_hash

VERSION='development-checkpoint-0.1.0'


def expand(model,optimizer,prior,graph):
    validate_catalog(prior);validate_catalog(graph)
    count=len(prior['tokens'])
    if (model.config.vocab_size!=count or graph['tokens'][:count]!=prior['tokens']
            or graph['nodes'][:count]!=prior['nodes'] or len(graph['tokens'])<=count):
        raise ValueError('trained semantic ABI cannot change')
    before_weights={k:tensor_hash(v) for k,v in model.state_dict().items()}
    before_optimizer=optimizer_receipt(optimizer)
    old=model.embedding.weight
    if old not in optimizer.state or not optimizer.state[old]: raise ValueError('missing trained embedding optimizer state')
    old_state=copy.deepcopy(optimizer.state_dict())
    table,manifest=compile_embeddings(model.config.width,graph)
    rng=torch.get_rng_state()
    embedding=nn.Embedding(len(graph['tokens']),model.config.width,padding_idx=0)
    torch.set_rng_state(rng)
    with torch.no_grad():
        embedding.weight[:count].copy_(old)
        embedding.weight[count:].copy_(table[count:])
    for group in optimizer.param_groups:
        group['params']=[embedding.weight if p is old else p for p in group['params']]
    moments=optimizer.state.pop(old)
    resized={}
    for key,value in moments.items():
        if isinstance(value,torch.Tensor) and value.shape==old.shape:
            z=torch.zeros_like(embedding.weight);z[:count].copy_(value);resized[key]=z
        else: resized[key]=value
    optimizer.state[embedding.weight]=resized
    model.embedding=embedding;model.config=replace(model.config,vocab_size=len(graph['tokens']))
    for name,value in model.state_dict().items():
        preserved=value[:count] if name=='embedding.weight' else value
        if tensor_hash(preserved)!=before_weights[name]:raise ValueError('trained weight changed during expansion')
    current=optimizer.state_dict()
    if current['param_groups']!=old_state['param_groups']: raise ValueError('optimizer hyperparameters changed')
    for p,s in old_state['state'].items():
        for key,value in s.items():
            new=current['state'][p][key]
            if new.shape!=value.shape:
                if new.shape!=embedding.weight.shape or value.shape!=old.shape or not torch.equal(new[:count],value) or bool(new[count:].any()):
                    raise ValueError('optimizer row migration distorted')
            elif not torch.equal(new,value):raise ValueError('optimizer state changed')
    return {'old_vocab':count,'new_vocab':len(graph['tokens']),'trained_weights_preserved':True,'old_moments_preserved':True,
            'new_moments_zero':True,'old_tensor_sha256':before_weights,'optimizer_before':before_optimizer,
            'optimizer_steps_before':before_optimizer['steps'],'optimizer_after':optimizer_receipt(optimizer),
            'new_row_sha256':{s:tensor_hash(model.embedding.weight[i]) for i,s in enumerate(graph['tokens']) if i>=count},
            'new_rows_initializer':manifest,'pretrained_neural_transfer':False,'rng_preserved':True}


def save(path,model,optimizer,graph,metadata):
    payload={'version':VERSION,'config':asdict(model.config),'model':model.state_dict(),'optimizer':optimizer.state_dict(),
             'graph':graph,'metadata':metadata,'state_sha256':state_hash(model),'optimizer_receipt':optimizer_receipt(optimizer),
             'torch_rng':torch.get_rng_state()}
    with path.open('xb') as f:torch.save(payload,f)


def load(path):
    payload=torch.load(path,map_location='cpu',weights_only=True)
    if payload['version']!=VERSION:raise ValueError('continuation checkpoint version')
    validate_catalog(payload['graph'])
    cfg=ModelConfig(**payload['config'])
    if cfg.vocab_size!=len(payload['graph']['tokens']):raise ValueError('checkpoint token binding')
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    model=MicroStudent(cfg);model.load_state_dict(payload['model'],strict=True)
    groups=payload['optimizer']['param_groups']
    if len(groups)!=1:raise ValueError('single AdamW group required')
    g=groups[0]
    optimizer=torch.optim.AdamW(model.parameters(),lr=g['lr'],betas=g['betas'],eps=g['eps'],weight_decay=g['weight_decay'],foreach=False)
    optimizer.load_state_dict(payload['optimizer'])
    if state_hash(model)!=payload['state_sha256'] or optimizer_receipt(optimizer)!=payload['optimizer_receipt']:
        raise ValueError('checkpoint numerical binding')
    torch.set_rng_state(payload['torch_rng'])
    return model,optimizer,payload
