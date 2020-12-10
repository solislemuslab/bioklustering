# Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
#   All rights reserved.
#   This file is part of the BioKlustering Website. 
from django import template

register = template.Library()

@register.filter(name='split')
def split(value, key):
    labels = value.split(key)
    if labels[1] == '':
        labels[1] = 'None'
    return labels