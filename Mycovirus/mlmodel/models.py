from django.db import models
from django import forms
from django.core.validators import EmailValidator

# Create your models here.

class FileInfo(models.Model):
    filepath = models.FileField('File', upload_to="userfiles/" )

    def __str__(self):
        return self.filepath
    
    def delete(self, *args, **kwargs):
        # if(self.kmer):
        #     self.kmer = None
        # if(self.email):
        #     self.email = None
        # if(self.sendbyemail):
        #     self.sendbyemail = False
        self.filepath.delete()
        super().delete(*args, **kwargs)

class FileListInfo(models.Model):
    A = "aligned"
    B = "unaligned"
    alignment_choices = [(A, "aligned"), (B, "unaligned")]
    alignment = models.CharField(max_length=30, choices=alignment_choices, default=B)
    filelist = models.ManyToManyField(FileInfo, blank=True)

    def __str__(self):
        filelist_str = ", ".join(str(f.filepath.name) for f in self.filelist.all())
        return filelist_str
        # return self.alignment

class PredictInfo(models.Model):
    A = "kmeans"
    B = "kmeansPCA"
    C = "kmeansTSNE"
    D = "kmeansMeanshiftPCA"
    E = "kmeansMeanshiftTSNE"
    mlmodels_choices = [(A, "kmeans"), (B, "kmeansPCA"), (C, "kmeansTSNE"), (D, "kmeansMeanshiftPCA"), (E, "kmeansMeanshiftTSNE")]
    mlmodels = models.CharField(max_length=30, choices=mlmodels_choices, default=A)
    kmer = models.CharField('Kmer size', max_length=200, blank=True, null=True, help_text = "Enter one or more kmer sizes here if you want to train the model with specific kmer size. Please separate each kmer size by a comma.")    
    sendbyemail = models.BooleanField('Send prediction to email?', default=False)
    email = models.EmailField('Email', max_length = 254, blank=True, null=True, help_text="If you want to send the result via email, please enter a valid email address here. E.g. xxxxx@gmail.com")
    
    def __str__(self):
        return self.mlmodels
    
