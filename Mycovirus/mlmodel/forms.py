from django import forms
from .models import FileInfo, PredictInfo

class FileInfoForm(forms.ModelForm):
    filepath = forms.FileField(required=True)
    class Meta:
        model = FileInfo
        fields = ('filepath', )

class PredictInfoForm(forms.ModelForm):
    class Meta:
        model = PredictInfo
        fields = ('mlmodels', 'kmer', 'email', 'sendbyemail')


    
    