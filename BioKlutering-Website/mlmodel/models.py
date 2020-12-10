# Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the BioKlustering Website.

from django.conf import settings
from django.db import models

class FileInfo(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    filepath = models.FileField('File', upload_to="userfiles/" )
    labelpath = models.FileField('File', upload_to="userfiles/", blank=True)

    def __str__(self):
        return self.filepath.name
    
    def getFilePaths(self):
        return self.filepath

    def getLabelPaths(self):
        return self.labelpath
    
    def delete(self, *args, **kwargs):
        self.filepath.delete()
        if self.labelpath:
            self.labelpath.delete()
        super().delete(*args, **kwargs)

class FileListInfo(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True
    )

    filelist = models.ManyToManyField(FileInfo, blank=True)

    def __str__(self):
        filelist_str = ", ".join(str(f.filepath.name) for f in self.filelist.all())
        return filelist_str
    
    def getLabelPaths(self):
        labelpaths_str = ", ".join(str(f.labelpath.name) for f in self.filelist.all())
        return labelpaths_str
    
    # delete filelist
    def delete(self, *args, **kwargs):
        if self.filelist:
            self.filelist.clear()
        super().delete(*args, **kwargs)
    
    # delete files in file list
    def delete_files(self, *args, **kwargs):
        if self.filelist:
            for file in self.filelist.all():
                file.delete()
        super().delete(*args, **kwargs)


class PredictInfo(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    mlmodels_choices = [
        ("K-Means Clustering", (
                ('unsupervisedKmeans', 'Unsupervised K-Means'),
                ('semisupervisedKmeans', 'Semi-supervised K-Means'),
            )
        ),
        ("Gaussian Mixture Model", (
                ('unsupervisedGMM', 'Unsupervised GMM'),
                ('semisupervisedGMM', 'Semi-supervised GMM'),
        )),
        ("Spectral Clustering", (
                ('unsupervisedSpectralClustering', 'Unsupervised Spectral Clustering'),
                ('semisupervisedSpectralClustering', 'Semi-supervised Spectral Clustering'),
        ))]
    mlmodels = models.CharField('Model',max_length=100, choices=mlmodels_choices, default="unsupervisedKmeans")
    sendbyemail = models.BooleanField('Send prediction to email?', default=False)
    email = models.EmailField('Email', max_length = 254, blank=True, null=True, help_text="If you want to send the result via email, please enter a valid email address here. E.g. xxxxx@gmail.com")
    parameters = models.CharField(max_length=1024)
    
    def __str__(self):
        return self.mlmodels
    
    def delete(self, *args, **kwargs):
        if self.mlmodels:
            self.mlmodels = None
        if self.email:
            self.email = None
        if self.parameters:
            self.parameters = None
        super().delete(*args, **kwargs)