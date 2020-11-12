# Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the Mycovirus Website.

import os
import django
from django import forms, template
from django.core.exceptions import ValidationError
from .models import FileInfo, FileListInfo, PredictInfo
from crispy_forms.helper import FormHelper

class MyNumberInput(forms.NumberInput):
    template_name = os.path.join('widgets', 'number.html')

class MySelect(forms.Select):
    template_name = os.path.join('widgets', 'select.html')

class MyClearableFileInput2(forms.ClearableFileInput):
    template_name = os.path.join('widgets', 'clearable_file_input2.html')

class MyClearableFileInput3(forms.ClearableFileInput):
    template_name = os.path.join('widgets', 'clearable_file_input3.html')

class FileInfoForm(forms.ModelForm):
    filepath = forms.FileField(required=True, widget=MyClearableFileInput2(attrs={'labelName': 'Upload a sequence file'}))
    labelpath = forms.FileField(required=False, widget=MyClearableFileInput3(attrs={'labelName': 'Upload a label file'}))
    # filepath = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': })
    class Meta:
        model = FileInfo
        fields = ('filepath', 'labelpath')

class MyCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = os.path.join('widgets', 'checkbox_select_filelist.html')

class MyModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.filepath.name[10:] + "||" + obj.labelpath.name[10:]

class FileListInfoForm(forms.ModelForm):
    filelist = MyModelMultipleChoiceField(queryset=FileInfo.objects.all(), 
                                        widget=MyCheckboxSelectMultiple(attrs={'class':'table table-sm table-hover table-bordered'}),
                                        error_messages={'required': 'The filelist is empty. Please select at least one file before making prediction.'})
    class Meta:
        model = FileListInfo
        fields = ('filelist', )

    def __init__(self, *args, **kwargs):
        super(FileListInfoForm, self).__init__(*args, **kwargs)

class PredictInfoForm(forms.ModelForm):

    class Meta:
        model = PredictInfo
        # fields = ('predict_model', 'kmer', 'email', 'sendbyemail')
        exclude = ['parameters']

class ParametersInfoForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        k_min = cleaned_data.get('k_min')
        k_max = cleaned_data.get('k_max')
        if k_min and k_max:
            if k_min > k_max:
                raise forms.ValidationError({'k_min': ['Ensure this value is smaller than K max.'], 'k_max': ['Ensure this value is greater than K min.']})
    

