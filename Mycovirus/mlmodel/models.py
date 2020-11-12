# Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the Mycovirus Website.
from django.db import models
from django import forms
from django.core.validators import EmailValidator

class FileInfo(models.Model):
    filepath = models.FileField('File', upload_to="userfiles/" )
    labelpath = models.FileField('File', upload_to="userfiles/", blank=True)

    def __str__(self):
        return self.filepath
    
    def getFilePaths(self):
        return self.labelpath

    def getLabelPaths(self):
        return self.labelpath
    
    def delete(self, *args, **kwargs):
        self.filepath.delete()
        if(self.labelpath):
            self.labelpath.delete()
        super().delete(*args, **kwargs)

class FileListInfo(models.Model):
    filelist = models.ManyToManyField(FileInfo, blank=True)

    def __str__(self):
        filelist_str = ", ".join(str(f.filepath.name) for f in self.filelist.all())
        return filelist_str
    
    # delete filelist
    def delete(self, *args, **kwargs):
        if(self.filelist):
            self.filelist.clear()
        super().delete(*args, **kwargs)
    
    # delete files in file list
    def delete_files(self, *args, **kwargs):
        if(self.filelist):
            for file in self.filelist.all():
                file.delete()
        super().delete(*args, **kwargs)


class PredictInfo(models.Model):
    mlmodels_choices = [
        ("K-Means Clustering", (
                ("kmeansPCA", "PCA"), 
                ("kmeansTSNE", "TSNE"), 
                ("kmeansMeanshiftPCA", "Meanshift PCA"), 
                ("kmeansMeanshiftTSNE", "Meanshift TSNE")
            )
        ),
        ("Gaussian Mixture Model", (
                ('gmm', 'GMM'),
        )),
        ("Spectral Clustering", (
                ('unsupervisedSpectralClustering', 'Unsupervised Spectral Clustering'),
                ('semisupervisedSpectralClustering', 'Semi-supervised Spectral Clustering'),
        ))]
    mlmodels = models.CharField('Model',max_length=100, choices=mlmodels_choices, default="kmeansPCA")
    sendbyemail = models.BooleanField('Send prediction to email?', default=False)
    email = models.EmailField('Email', max_length = 254, blank=True, null=True, help_text="If you want to send the result via email, please enter a valid email address here. E.g. xxxxx@gmail.com")
    parameters = models.CharField(max_length=1024)
    
    def __str__(self):
        return self.mlmodels
    
    def delete(self, *args, **kwargs):
        if(self.mlmodels):
            self.mlmodels = None
        if(self.email):   
            self.email = None
        if(self.parameters):
            self.parameters = None
        super().delete(*args, **kwargs)