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
from mlmodel.forms import MyNumberInput, MySelect, FileInfoForm, FileListInfoForm, PredictInfoForm, ParametersInfoForm
from mlmodel.parser import kmeans, GMM, spectralClustering
from mlmodel.models import PredictInfo
from django.core.validators import MinValueValidator
from django.utils.translation import gettext as _
from django.contrib import messages


class PredictionView(FormView):

    def __init__(self, *args, **kwargs):
        super(FormView, self).__init__(*args, **kwargs)
        self.path = os.path.join('mlmodel', self.template_name)
        
    def get(self, request, *args, **kwargs):
        upload_form = FileInfoForm(prefix = "upload_form")
        filelist_last = FileListInfo.objects.last()
        filelist_form = FileListInfoForm(prefix="filelist_form", initial={'filelist': getattr(filelist_last, 'filelist').all()})
        
        predict_info = PredictInfo.objects.last()
        if predict_info == None:
            predict_info = PredictInfo.objects.create()
            predict_info.mlmodels = "kmeansPCA"
        predict_form = PredictInfoForm(prefix = "predict_form", instance=predict_info)
        parameters_form = self.get_parameters_form(predict_info.mlmodels, getattr(predict_info, "content", {}))
        
        return render(self.request, self.path, {
            'upload_form': upload_form,
            'filelist_form': filelist_form,
            'filelist': FileListInfo.objects.last(),
            'predict_form': predict_form,
            'parameters_form': parameters_form,
        })
    
    def post(self, request, *args, **kwargs):
        if self.request.method=='POST':
            upload_form = FileInfoForm(self.request.POST, files=self.request.FILES, prefix="upload_form")
            filelist_form = FileListInfoForm(self.request.POST, prefix="filelist_form")
            predict_form = PredictInfoForm(self.request.POST, prefix="predict_form")
            
            upload_form_isalid = upload_form.is_valid()
            filelist_form_isvalid = filelist_form.is_valid()
            predict_form_isvalid = predict_form.is_valid()

            # upload a file
            if upload_form_isalid and not predict_form_isvalid and not filelist_form_isvalid:
                upload_form.save()
                #  process the uploaded file before writing it to database
                fileval = upload_form['filepath'].value() # actual file
                filepath = os.path.join("media", "resultfiles", fileval.name)
                self.handle_uploaded_file(fileval, filepath) 
            # save the filelist
            elif filelist_form_isvalid and not upload_form_isalid and not predict_form_isvalid:
                filelist = FileListInfo.objects.last()
                if filelist == None:
                    filelist = FileListInfo.objects.create()
                if 'add_filelist' in self.request.POST: # update filelist for prediction
                    filelist_form.instance = filelist
                    filelist_form.save()
                elif 'delete_filelist' in self.request.POST: # delete files from file list
                    filelist = filelist_form.cleaned_data['filelist']
                    for item in filelist:
                        item.delete()
            # choose a model or fill in parameters
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
                    else: # submit params (or handle other invalid forms)
                        for key in self.request.POST.keys():
                            if key != 'csrfmiddlewaretoken':
                                content[key] = self.request.POST[key]

                upload_form = FileInfoForm(prefix="upload_form")
                filelist_last = FileListInfo.objects.last()
                if filelist_form_isvalid or 'add_filelist' not in content:
                    if filelist_last:
                        filelist_form = FileListInfoForm(prefix="filelist_form", initial={'filelist': getattr(filelist_last, 'filelist').all()})

                predict_form = PredictInfoForm(instance=predict_info)
                parameters_form = self.get_parameters_form(predict_info.mlmodels, content)
                if parameters_form.is_valid():
                    predict_info.parameters = json.dumps(content)
                    predict_info.save()
                    # submit params or predict
                    if 'submit_params' in self.request.POST and not 'choose_model' in self.request.POST:
                        # make a prediction
                        return redirect('result')

                return render(self.request, self.path, {
                    'upload_form': upload_form,
                    'filelist_form': filelist_form,
                    'filelist': FileListInfo.objects.last(),
                    'predict_form': predict_form,
                    'parameters_form': parameters_form,
                })
            
            return redirect('index')

        return redirect('index')
    
    # a function to ensure that large files don’t overwhelm system’s memory
    def handle_uploaded_file(self, fileval, filepath):
        with open(filepath, 'wb+') as destination:
            for chunk in fileval.chunks():
                destination.write(chunk)
    
    def get_parameters_form(self, mlmodels, content):
        if mlmodels == "gmm":
            cov_types = [
                ('spherical', 'Spherical'),
                ('diag', 'Diag'),
                ('tied', 'Tied'),
                ('full', 'Full'),
            ]
            cov_type_img = os.path.join("media", "models", "images", "gmm_cov_type.png")
            new_fields = {
                'k_min': forms.IntegerField(validators=[MinValueValidator(2)], 
                    widget=MyNumberInput(attrs={
                        "class":"form-control", 
                        "label":"K-min", 
                        "help_text":"The minimum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 2."
                })),
                'k_max': forms.IntegerField(validators=[MinValueValidator(2)], 
                    widget=MyNumberInput(attrs={
                        "class":"form-control", 
                        "label":"K-max", 
                        "help_text":"The maximum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 3."
                })),
                'num_class': forms.IntegerField(validators=[MinValueValidator(2)], 
                    widget=MyNumberInput(attrs={
                        "class":"form-control", 
                        "label":"Number of classes", 
                        "help_text":"The number of predicted labels. You can choose starting from 2. Default is set to be 2."
                })),
                'cov_type': forms.ChoiceField(choices=cov_types, 
                    widget=MySelect(attrs={
                        "class": "custom-select", 
                        "label":"Covariance type",
                        "help_text": "Type of covariance. There are four types of covariances: spherical, diagonal, tied, and full. Default is set to be full. More details see <u>Learn More about GMM</u> above.",
                        "isHtml": True
                })),
                'description': {
                    'Gaussian Mixture Model (GMM)': 'GMM is a probabilistic model that estimates the underlying multiple Gaussian distributions behind the seemingly chaotic observations. Input will be gene sequences, aligned or unaligned, and output will be predicted label for each virus: 0,1, etc. A k-mer table will be created to transfer the input data for analysis. When using this model, the following parameters are predetermined.',
                    'K-mer': 'Consecutive genes of length k that can be important for classification. The range of length of k-mer can be adjusted. For instance, if you set the minimum length to be 3 and maximum length 3 for gene sequence ATGG, two k-mers ATG and TGG are considered.',
                    'K-min': 'The minimum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 2.',
                    'K-max': 'The maximum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 3.',
                    'Number of classes': 'The number of predicted labels. Default is set to be 2.',
                    'Covariance type': 'The type of covariance. There are four types of covariances: spherical, diagonal, tied, and full. Default is set to be full. See the following figure of how they work: <br><img src="%s">' % cov_type_img
                }
            }
            # set up default values
            if not bool(content) or 'k_min' not in content: 
                content = {
                    'k_min': 2,
                    'k_max': 3,
                    'num_class': 2,
                    'cov_type': 'full',
                }
        elif mlmodels == "spectralClustering":
            assignLabels = [
                ('kmeans', 'kmeans'),
                ('discretize', 'discretize')
            ]
            new_fields = {
                'k_min': forms.IntegerField(validators=[MinValueValidator(2)], 
                    widget=MyNumberInput(attrs={
                        "class":"form-control", 
                        "label":"K-min", 
                        "help_text":"The minimum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 2."
                })),
                'k_max': forms.IntegerField(validators=[MinValueValidator(2)], 
                    widget=MyNumberInput(attrs={
                        "class":"form-control", 
                        "label":"K-max", 
                        "help_text":"The maximum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 3."
                })),
                'num_cluster': forms.IntegerField(validators=[MinValueValidator(2)], 
                    widget=MyNumberInput(attrs={
                        "class":"form-control", 
                        "label":"Number of Clusters", 
                        "help_text":"The number of predicted labels. You can choose starting from 2. Default is set to be 2."
                })),
                'assignLabels': forms.ChoiceField(choices=assignLabels, 
                    widget=MySelect(attrs={
                        "class": "custom-select", 
                        "label":"Assign Labels",
                        "help_text": "Type of covariance. There are four types of covariances: spherical, diagonal, tied, and full. Default is set to be full. More details see <u>Learn More about GMM</u> above.",
                        "isHtml": True
                }))
            }
            # set up default values
            if not bool(content) or 'k_min' not in content: 
                content = {
                    'k_min': 2,
                    'k_max': 3,
                    'num_cluster': 2,
                    'assignLabels': 'kmeans',
                }
        else:
            new_fields = {}
            if not bool(content):
                content = {}
        
        DynamicParametersInfoForm = type('DynamicParametersInfoForm', (ParametersInfoForm,), new_fields)
        parameters_form = DynamicParametersInfoForm(content)
        return parameters_form


class ResultView(FormView):

    def __init__(self, *args, **kwargs):
        super(FormView, self).__init__(*args, **kwargs)
        self.path = os.path.join('mlmodel', self.template_name)
        
    # render the result page and it will make the prediction using ajax
    def get(self, request, *args, **kwargs):
        return render(self.request, self.path)
    
    # actual predict 
    def process(request):
        context = {}
        files = FileInfo.objects.all()
        if len(files) == 0:
            return redirect('index')
        form = FileInfoForm(prefix='upload_form')
        label = "<div>Fail to predict labels.</div>"
        if request.method == 'POST':
            filenames = str(FileListInfo.objects.last()).split(sep=", ")
            mlmethod = getattr(PredictInfo.objects.last(), "mlmodels")
            senbyemail = getattr(PredictInfo.objects.last(), "sendbyemail")
            email = getattr(PredictInfo.objects.last(), "email")
            result = []
            if(mlmethod == "kmeansPCA"):
                result = kmeans.kmeansPCA(filenames)
            elif(mlmethod == "kmeansTSNE"):
                result = kmeans.kmeansTSNE(filenames)
            elif(mlmethod == "kmeansMeanshiftPCA"):
                result = kmeans.kmeansMeanshiftPCA(filenames)
            elif(mlmethod == "kmeansMeanshiftTSNE"):
                result = kmeans.kmeansMeanshiftTSNE(filenames)
            elif(mlmethod == "gmm"):
                params_str = getattr(PredictInfo.objects.last(), "parameters")
                params_obj = json.loads(params_str)
                k_min = int(params_obj['k_min'])
                k_max = int(params_obj['k_max'])
                num_class = int(params_obj['num_class'])
                cov_type = str(params_obj['cov_type'])
                result = GMM.get_predictions(filenames,k_min, k_min, num_class, cov_type)
            elif(mlmethod == "spectralClustering"):
                params_str = getattr(PredictInfo.objects.last(), "parameters")
                params_obj = json.loads(params_str)
                k_min = int(params_obj['k_min'])
                k_max = int(params_obj['k_max'])
                num_cluster = int(params_obj['num_cluster'])
                assignLabels = str(params_obj['assignLabels'])
                result = spectralClustering.spectral_clustering(filenames,k_min, k_min, num_cluster, assignLabels)
            list_of_df = result[0]
            all_df = pd.concat(list_of_df)
            # make the index and other column labels to be on same line
            all_df.columns.name = all_df.index.name
            all_df.index.name = None
            label = all_df.to_html(col_space=110, justify='left', classes='table table-responsive result-table')
            # write to csv
            result_path = os.path.join("media", "resultfiles", "result.csv")
            all_df.to_csv(result_path, index_label='ID')
            if senbyemail and email and len(email) > 0 : # send the result as long as email addr is entered
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
                email_msg.attach_file(result_path)
                for image in result[1]:
                    email_msg.attach_file(image)
                email_msg.send()
            elif senbyemail == False: # if select sendbyemail but not enter email addr
                # TODO:
                email = 1
            context['label']= label
            if(mlmethod == 'spectralClustering'):
                context['plotly_dash'] = result[1]
            else:
                context['image'] = result[1]
        return JsonResponse(context)
        # return JsonResponse({'label': label, 'image': result[1]})
        # return JsonResponse({'label': result[0].to_html(), 'image': "media"})
    
    def download_csv(request):
        filepath = os.path.join('media', 'resultfiles')
        filename = 'result.csv'
        fs = FileSystemStorage(filepath)
        response = FileResponse(fs.open(filename, 'rb'), content_type='application/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response

    



# def delete(request, pk):
#     if request.method == 'POST':
#         delete_file = FileInfo.objects.get(pk=pk)
#         delete_file.delete()
#     return redirect('index')

# def delete_filelists(request, pk):
#     if request.method == 'POST':
#         delete_filelist = FileListInfo.objects.get(pk=pk)
#         delete_filelist.delete()
#     return redirect('index')

# def download_pdf(request):
#     filepath = os.path.join('media', 'resultfiles')
#     filename = 'result.pdf'
#     fs = FileSystemStorage(filepath)
#     response = FileResponse(fs.open(filename, 'rb'), content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename=%s' % filename
#     return response


def cookie_session(request):
    request.session.set_test_cookie()
    return HttpResponse("<h1>dataflair</h1>")
def cookie_delete(request):
    if request.session.test_cookie_worked():
        request.session.delete_test_cookie()
        response = HttpResponse("dataflair<br> cookie createed")
    else:
        response = HttpResponse("Dataflair <br> Your browser doesnot accept cookies")
    return response

def create_session(request):
    request.session['name'] = 'username'
    request.session['password'] = 'password123'
    return HttpResponse("<h1>dataflair<br> the session is set</h1>")
def access_session(request):
    response = "<h1>Welcome to Sessions of dataflair</h1><br>"
    if request.session.get('name'):
        response += "Name : {0} <br>".format(request.session.get('name'))
    if request.session.get('password'):
        response += "Password : {0} <br>".format(request.session.get('password'))
        return HttpResponse(response)
    else:
        return redirect('create_session')
def delete_session(request):
    try:
        del request.session['name']
        del request.session['password']
    except KeyError:
        pass
    return HttpResponse("<h1>dataflair<br>Session Data cleared</h1>")





