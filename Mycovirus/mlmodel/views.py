import os 
import pandas as pd
import json
from .models import FileInfo, FileListInfo
from .parser.parseFasta import *
from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as ug
from django.core.exceptions import ValidationError
from django.core.mail import send_mail, EmailMessage
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.generic.edit import FormView
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from mlmodel.forms import FileInfoForm, FileListInfoForm, PredictInfoForm, ParametersInfoForm
from mlmodel.parser import kmeans, GMM
from mlmodel.models import PredictInfo
from django.core.validators import MinValueValidator
from django.utils.translation import gettext as _

class PredictionView(FormView):
    template = 'predict.html'
        
    def get(self, request, *args, **kwargs):
        upload_form = FileInfoForm(prefix = "upload_form")
        predict_form = PredictInfoForm(prefix = "predict_form")
        filelist_form = FileListInfoForm(prefix="filelist_form")
        parameters_form = get_parameters_form("kmeansPCA", {"temp": 1})
        files = FileInfo.objects.all()
        filelists = FileListInfo.objects.all()
        context = {
            'upload_form': upload_form,
            'predict_form': predict_form,
            'filelist_form': filelist_form,
            'parameters_form': parameters_form,
            'files': files,
            'filelists': filelists,
        }
        path = os.path.join('mlmodel', self.template)
        return render(self.request, path, context)
    
    def post(self, request, *args, **kwargs):
        if self.request.method=='POST':
            upload_form = FileInfoForm(self.request.POST, files=self.request.FILES, prefix="upload_form")
            filelist_form = FileListInfoForm(self.request.POST, prefix="filelist_form")
            predict_form = PredictInfoForm(self.request.POST, prefix="predict_form")
            
            upload_form_isalid = upload_form.is_valid()
            filelist_form_isvalid = filelist_form.is_valid()
            predict_form_isvalid = predict_form.is_valid()

            if upload_form_isalid and not predict_form_isvalid and not filelist_form_isvalid:
                upload_form.save()
                #  process the uploaded file before writing it to database
                f = upload_form['filepath'].value() # actual file
                filepath = os.path.join("media", "resultfiles", f.name)
                handle_uploaded_file(f, filepath)
            elif filelist_form_isvalid and not upload_form_isalid and not predict_form_isvalid:
                filelist_form.save()
                path = os.path.join('mlmodel', self.template)
                if 'add_filelist' in self.request.POST:
                    pass
                elif 'delete_filelist' in self.request.POST:
                    filelist = FileListInfo.objects.last()
                    filelist.delete_files()
                    # filelist.delete()
            else:
                context = {}
                content = {}
                
                predict_info = PredictInfo.objects.last()
                if predict_info == None:
                    predict_info = PredictInfo.objects.create()
                    predict_info.mlmodels = "kmeansPCA"
                if self.request.method == 'POST':
                    if 'mlmodels' in self.request.POST: # choose model
                        predict_info.mlmodels = self.request.POST['mlmodels']
                        predict_info.email = self.request.POST.get('email', '')
                        predict_info.sendbyemail = True if self.request.POST.get('sendbyemail', 'off')=='on' else False
                        predict_info.save()
                        content = {}
                    elif 'predict_form-mlmodels' in self.request.POST: # choose model
                        predict_info.mlmodels = self.request.POST['predict_form-mlmodels']
                        predict_info.email = self.request.POST.get('predict_form-email', '')
                        predict_info.sendbyemail = True if self.request.POST.get('predict_form-sendbyemail', 'off')=='on' else False
                        predict_info.save()
                        content = {}
                    else: # submit params
                        for key in self.request.POST.keys():
                            if key != 'csrfmiddlewaretoken':
                                content[key] = self.request.POST[key]

                parameters_form = get_parameters_form(predict_info.mlmodels, content)
                upload_form = FileInfoForm(prefix="upload_form")
                predict_form = PredictInfoForm(instance=predict_info)
                filelist_form = FileListInfoForm(prefix="filelist_form")
                files = FileInfo.objects.all()
                filelists = FileListInfo.objects.all()
                if parameters_form.is_valid():
                    predict_info.parameters = json.dumps(content)
                    predict_info.save()
                    # submit params or predict
                    if 'submit_params' in self.request.POST and not 'choose_model' in self.request.POST:
                        # reset form fields
                        predict_form = PredictInfoForm(prefix="predict_form")
                        content = {
                            # 'temp': 1,
                        }
                        parameters_form = get_parameters_form("kmeansPCA", content)
                        return redirect('result')
                path = os.path.join('mlmodel', self.template)
                return render(self.request, path, {
                    'upload_form': upload_form,
                    # 'predict_form': predict_form,
                    'filelist_form': filelist_form,
                    'files': files,
                    'filelists': filelists,
                    'parameters_form': parameters_form,
                    'predict_form': predict_form,
                    # 'content': content,
                    # "last_predict_info": predict_info,
                    # "last_predict_info_id": predict_info.id,
                    # "last_predict_info_parameters": predict_info.parameters,
                    # "all_filelist": FileListInfo.objects.all(),
                    # "all_predictinfo": PredictInfo.objects.all()
                })

            # preserve data in form
            predict_info = PredictInfo.objects.last()
            if predict_info == None:
                predict_info = PredictInfo.objects.create()
                predict_info.mlmodels = "kmeansPCA"
            parameters_form = get_parameters_form(predict_info.mlmodels, getattr(predict_info, "content", {}))
            upload_form = FileInfoForm(prefix = "upload_form")
            predict_form = PredictInfoForm(instance=predict_info)
            filelist_form = FileListInfoForm(prefix="filelist_form")
            files = FileInfo.objects.all()
            filelists = FileListInfo.objects.all()
            path = os.path.join('mlmodel', self.template)
            return render(self.request, path, {
                'upload_form': upload_form,
                'predict_form': predict_form,
                'filelist_form': filelist_form,
                'files': files,
                'filelists': filelists,
                'parameters_form': parameters_form
            })

        # reset data in form
        upload_form = FileInfoForm(prefix = "upload_form")
        predict_form = PredictInfoForm(prefix = "predict_form")
        filelist_form = FileListInfoForm(prefix="filelist_form")
        parameters_form = get_parameters_form("kmeansPCA", {"temp": 2})
        files = FileInfo.objects.all()
        filelists = FileListInfo.objects.all()
        path = os.path.join('mlmodel', self.template)
        return render(self.request, path, {
            'upload_form': upload_form,
            'predict_form': predict_form,
            'filelist_form': filelist_form,
            'files': files,
            'filelists': filelists,
            'parameters_form': parameters_form
        })

def result(request):
    path = os.path.join('mlmodel', 'result.html')
    return render(request, path)

# actual predict 
def process(request):
    files = FileInfo.objects.all()
    if len(files) == 0:
        return redirect('index')
    form = FileInfoForm(prefix='upload_form')
    label = "<div>Fail to predict labels.</div>"
    if request.method == 'POST':
        # filenames = FileInfo.objects.values_list('filepath', flat=True)
        filenames = str(FileListInfo.objects.last()).split(sep=", ")
        mlmethod = getattr(PredictInfo.objects.last(), "mlmodels")
        senbyemail = getattr(PredictInfo.objects.last(), "sendbyemail")
        email = getattr(PredictInfo.objects.last(), "email")
        result = []
        # if(mlmethod == "kmeans"):
        #     result = kmeans.websiteScriptKmeans(filenames)
        if(mlmethod == "kmeansPCA"):
            result = kmeans.kmeansPCA(filenames)
        elif(mlmethod == "kmeansTSNE"):
            result = kmeans.kmeansTSNE(filenames)
        elif(mlmethod == "kmeansMeanshiftPCA"):
            result = kmeans.kmeansMeanshiftPCA(filenames)
        elif(mlmethod == "kmeansMeanshiftTSNE"):
            result = kmeans.kmeansMeanshiftTSNE(filenames)
        elif(mlmethod == "gmm"):
            result = GMM.get_predictions(filenames,2,3,2,"full")
        list_of_df = result[0]
        all_df = pd.concat(list_of_df)
        # make the index and other column labels to be on same line
        all_df.columns.name = all_df.index.name
        all_df.index.name = None
        label = all_df.to_html(col_space=110, justify='left')
        # write to csv
        path = os.path.join("media", "resultfiles", "result.csv")
        all_df.to_csv(path, index_label='ID')
        if email and len(email) > 0 : # send the result as long as email addr is entered
            from_email = os.environ.get('MYCOVIRUS_EMAIL_USER')
            to_email = email
            template_path = os.path.join("email", "email_template.txt")
            email_msg = EmailMessage(
                '[Mycovirus Website] Here is your prediction result.',
                render_to_string(template_path, {}),
                from_email,
                [to_email],
                reply_to=[from_email],
            )
            email_msg.attach_file(path)
            for image in result[1]:
                email_msg.attach_file(image)
            email_msg.send()
        elif senbyemail == False: # if select sendbyemail but not enter email addr
            # TODO:
            email = 1
    # return JsonResponse({'label': lable})    
    return JsonResponse({'label': label, 'image': result[1]})
    # return JsonResponse({'label': result[0].to_html(), 'image': "media"})


def delete(request, pk):
    if request.method == 'POST':
        delete_file = FileInfo.objects.get(pk=pk)
        delete_file.delete()
    return redirect('index')

def delete_filelists(request, pk):
    if request.method == 'POST':
        delete_filelist = FileListInfo.objects.get(pk=pk)
        delete_filelist.delete()
    return redirect('index')

def download_pdf(request):
    filepath = os.path.join('media', 'resultfiles')
    filename = 'result.pdf'
    fs = FileSystemStorage(filepath)
    response = FileResponse(fs.open(filename, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

def download_csv(request):
    filepath = os.path.join('media', 'resultfiles')
    filename = 'result.csv'
    fs = FileSystemStorage(filepath)
    response = FileResponse(fs.open(filename, 'rb'), content_type='application/csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

# a function to ensure that large files don’t overwhelm system’s memory
def handle_uploaded_file(f, filepath):
    with open(filepath, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

#TODO: remember delete the current predictInfo object or reset fields after prediction

def resetData(request):
    # if request.method == 'POST':
    #     all_predict_info = PredictInfo.objects.all()
    #     all_file_list = FileListInfo.objects.all()

    #     for predict_info in all_predict_info:
    #         predict_info.delete()
    #     for file_list in all_file_list:
    #         file_list.delete()
    
    return JsonResponse({'msg': 'success'}) 

def get_parameters_form(mlmodels, content):
    if mlmodels == "gmm":
        cov_types = [
            ('spherical', 'Spherical'),
            ('diag', 'Diag'),
            ('tied', 'Tied'),
            ('full', 'Full'),
        ]
        new_fields = {
            'k_min': forms.IntegerField(validators=[MinValueValidator(1)]),
            'k_max': forms.IntegerField(validators=[MinValueValidator(1)]),
            'num_class': forms.IntegerField(validators=[MinValueValidator(2)]),
            'cov_type': forms.ChoiceField(choices=cov_types)
        }
        if not bool(content):
            content = {
                'k_min': 2,
                'k_max': 3,
                'num_class': 2,
                'cov_type': 'full',
                # 'action': 
            }
    else:
        new_fields = {
            # 'temp': forms.IntegerField()
        }
        if not bool(content):
            content = {
                # 'temp': 10,
                # 'action': request.POST['action'],
            }
    DynamicParametersInfoForm = type('DynamicParametersInfoForm', (ParametersInfoForm,), new_fields)
    parameters_form = DynamicParametersInfoForm(content)
    return parameters_form