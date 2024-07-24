#implementation of a simple unet
import equinox as eqx
import jax
import jax.numpy as jnp
import jax.random as jr
from einops import rearrange

from collections.abc import Callable
from typing import Optional, Union
import math

#position embedding
class sinusoidalPositionEmbeddngs(eqx.Module):
    _embedding: jax.Array
    
    def __init__(self,dim):
        half_dim = dim//2
        embedding = math.log(10000)/(half_dim -1)
        self._embedding = jnp.exp(jnp.arange(half_dim)*-embedding)
        
    def __call__(self,x):
        embedding = x*self._embedding
        embedding = jnp.concatenate((jnp.sin(embedding),jnp.cos(embedding)),axis=-1)
        return embedding


class Block(eqx.Module):
    _transform: eqx.nn.Conv2d
    _up: bool
    _time_mlp: eqx.nn.Linear
    _conv1: eqx.nn.Conv2d
    _conv2: eqx.nn.Conv2d
    _bnorm1: eqx.nn.BatchNorm
    _bnorm2: eqx.nn.BatchNorm

    
    def __init__(self, in_channels,out_channels,time_embed_dim,up=False,*,key):
        self._time_mlp = eqx.nn.Linear(time_embed_dim,out_channels,key=key)
        self._conv1 = eqx.nn.Conv2d(in_channels,out_channels,3,padding=1,key=key)
        if up:
            # self._conv1 = eqx.nn.Conv2d(2*in_channels,out_channels,3,padding=1,key=key)
            self._transform = eqx.nn.ConvTranspose2d(out_channels, out_channels, 4,2,1,key=key)
        else:
            self._transform = eqx.nn.Conv2d(out_channels,out_channels,4,2,1,key=key)
        self._conv2 = eqx.nn.Conv2d(out_channels,out_channels,3,padding=1,key=key)
        self._bnorm1 = eqx.nn.BatchNorm(out_channels)
        self._bnorm2 = eqx.nn.BatchNorm(out_channels)
        
    def __call__(self,x,t):
        h = self._bnorm1(jax.nn.relu(self._conv1(x)))   #bcwh
        time_embedding = jax.nn.relu(self._time_mlp(t)) #dim [batch,outchannels]
        time_embedding = time_embedding[(...,)+[None,]*2] #prep for broadcasting
        h = h + time_embedding
        h = self._bnorm2(jax.nn.relu(self._conv2(h)))
        return self._transform(h)
        
        
    
    