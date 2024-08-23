# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class VM(models.Model):
    name= models.CharField(max_length =255)
    node = models.CharField(max_length =255)
    vmid = models.CharField(max_length =255)
    memory = models.IntegerField()
    cores = models.IntegerField()
    disk = models.CharField(max_length=255)
    bridge= models.CharField(max_length =255)
    cpu = models.CharField(max_length=255)
    ostype = models.CharField(max_length=255)
    ip_adress = models.CharField(max_length =255)





