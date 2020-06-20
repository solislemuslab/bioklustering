from django import forms, template
from .models import FileInfo, PredictInfo
import os
import django

class MyClearableFileInput(forms.ClearableFileInput):
    # template_name= os.path.join( 'django', 'forms', 'widgets', 'clearable_file_input.html')
    # template_name = 'django/forms/widgets/clearable_file_input.html'
    template_name = os.path.join('widgets', 'clearable_file_input.html')
    # template_name = template.loader.get_template(os.path.join('widgets', 'clearable_file_input.html'))

class FileInfoForm(forms.ModelForm):
    filepath = forms.FileField(required=True, widget=MyClearableFileInput)
    class Meta:
        model = FileInfo
        fields = ('filepath', )
        # widgets = {
        #     # 'filepath': forms.ClearableFileInput(attrs={'label':})
        # }

class PredictInfoForm(forms.ModelForm):
    class Meta:
        model = PredictInfo
        fields = ('mlmodels', 'kmer', 'email', 'sendbyemail')


