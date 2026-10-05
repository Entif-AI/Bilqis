"""Causal transformer with a restricted answer-token readout; FP32 or W1.58A8 emulation."""
from __future__ import annotations
from dataclasses import dataclass,asdict
import hashlib, json
import torch
from torch import nn
from torch.nn import functional as F
from .codec import TOKEN_TO_ID

@dataclass(frozen=True)
class ModelConfig:
    vocab_size:int=512
    context:int=384
    width:int=192
    layers:int=6
    heads:int=6
    expansion:int=4
    precision:str="ternary"

class QLinear(nn.Linear):
    def __init__(self,a:int,b:int,precision:str):
        super().__init__(a,b,bias=False);self.precision=precision
    def forward(self,x:torch.Tensor)->torch.Tensor:
        if self.precision=="fp32":return F.linear(x,self.weight)
        # All stored tensors, arithmetic, master weights and optimizer state remain FP32.
        scale=self.weight.detach().abs().mean().clamp_min(1e-8)
        wq=(self.weight/scale).round().clamp(-1,1)*scale
        w=self.weight+(wq-self.weight).detach()
        a=x.detach().abs().amax(dim=-1,keepdim=True).clamp_min(1e-8)/127
        xq=(x/a).round().clamp(-127,127)*a
        z=x+(xq-x).detach()
        return F.linear(z,w)

class Block(nn.Module):
    def __init__(self,c:ModelConfig):
        super().__init__();self.heads=c.heads;self.width=c.width
        self.n1=nn.LayerNorm(c.width,bias=False);self.n2=nn.LayerNorm(c.width,bias=False)
        self.qkv=QLinear(c.width,3*c.width,c.precision);self.proj=QLinear(c.width,c.width,c.precision)
        self.up=QLinear(c.width,c.expansion*c.width,c.precision);self.down=QLinear(c.expansion*c.width,c.width,c.precision)
    def forward(self,x:torch.Tensor)->torch.Tensor:
        b,t,d=x.shape;q,k,v=self.qkv(self.n1(x)).chunk(3,dim=-1)
        q,k,v=(z.reshape(b,t,self.heads,d//self.heads).transpose(1,2) for z in (q,k,v))
        y=F.scaled_dot_product_attention(q,k,v,is_causal=True,dropout_p=0).transpose(1,2).contiguous().reshape(b,t,d)
        x=x+self.proj(y);return x+self.down(F.relu(self.up(self.n2(x))).square())

class Student(nn.Module):
    def __init__(self,c:ModelConfig):
        super().__init__()
        if c.vocab_size!=512 or c.width%c.heads or c.precision not in ("fp32","ternary"):
            raise ValueError("model ABI / width / precision")
        self.config=c;self.embedding=nn.Embedding(c.vocab_size,c.width,padding_idx=0)
        self.position=nn.Embedding(c.context,c.width);self.blocks=nn.ModuleList(Block(c) for _ in range(c.layers));self.norm=nn.LayerNorm(c.width,bias=False)
        self.apply(self._initialize)
    @staticmethod
    def _initialize(m):
        if isinstance(m,(nn.Linear,nn.Embedding)):nn.init.normal_(m.weight,mean=0,std=0.02)
    def forward(self,ids:torch.Tensor,lengths:torch.Tensor)->torch.Tensor:
        if ids.ndim!=2 or ids.shape[1]>self.config.context:raise ValueError("CONTEXT_OVERFLOW")
        if bool((lengths<1).any()) or bool((lengths>ids.shape[1]).any()):raise ValueError("sequence lengths")
        x=self.embedding(ids)+self.position(torch.arange(ids.shape[1],device=ids.device))[None,:,:]
        for layer in self.blocks:x=layer(x)
        h=self.norm(x)[torch.arange(ids.shape[0],device=ids.device),lengths-1]
        # Four reserved answer rows of the same embedding table are the readout.
        answers=torch.tensor([TOKEN_TO_ID[s] for s in ("TRUE","FALSE","UNKNOWN","CONFLICT")],device=ids.device)
        return F.linear(h,self.embedding(answers))

def batch(inputs:list[list[int]],device:str="cpu")->tuple[torch.Tensor,torch.Tensor]:
    lengths=torch.tensor([len(x) for x in inputs],device=device,dtype=torch.long)
    t=int(lengths.max());ids=torch.zeros((len(inputs),t),dtype=torch.long,device=device)
    for i,x in enumerate(inputs):ids[i,:len(x)]=torch.tensor(x,device=device)
    return ids,lengths

def state_hash(model:Student)->str:
    h=hashlib.sha256()
    for k,v in sorted(model.state_dict().items()):
        h.update(k.encode());h.update(str(tuple(v.shape)).encode());h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()

def initialize(c:ModelConfig,seed:int)->Student:
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True);torch.manual_seed(seed)
    return Student(c)
