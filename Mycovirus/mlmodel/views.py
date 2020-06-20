import os 
import pandas as pd
from .models import FileInfo
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
from mlmodel.forms import FileInfoForm, PredictInfoForm
from mlmodel.parser import kmeans
from mlmodel.models import PredictInfo

class PredictionView(FormView):
    template = 'predict.html'
        
    def get(self, request, *args, **kwargs):
        upload_form = FileInfoForm(prefix = "upload_form")
        predict_form = PredictInfoForm(prefix = "predict_form")
        files = FileInfo.objects.all()
        context = {
            'upload_form': upload_form,
            'predict_form': predict_form,
            'files': files
        }
        path = os.path.join('mlmodel', self.template)
        return render(self.request, path, context)
    
    def post(self, request, *args, **kwargs):
        if self.request.method=='POST':
            upload_form = FileInfoForm(self.request.POST, files=self.request.FILES, prefix="upload_form")
            predict_form = PredictInfoForm(self.request.POST, prefix="predict_form")
            upload_form_isalid = upload_form.is_valid()
            predict_form_isvalid = predict_form.is_valid()

            if upload_form_isalid and not predict_form_isvalid:
                upload_form.save()
                #  process the uploaded file before writing it to database
                f = upload_form['filepath'].value() # actual file
                filepath = os.path.join("media", "resultfiles", f.name)
                handle_uploaded_file(f, filepath)
                return redirect('index') #TODO
            elif predict_form_isvalid and not upload_form_isalid:
                files = FileInfo.objects.all()
                path = os.path.join('mlmodel', 'result.html')
                if len(files) != 0:
                    predict_form.save()
                    # if predict_form['sendbyemail'].value():
                    #     from_email = "mycovirus.website@mail.com"
                    #     to_email = predict_form['email'].value()
                    #     send_mail(
                    #         '[Mycovirus Website]Here is your prediction result.',
                    #         'Here is the message. Test.',
                    #         from_email,
                    #         [to_email],
                    #         fail_silently=False,
                    #     )
                    #     predict_form['email'].value()

                    return redirect('result')
        
        upload_form = FileInfoForm(prefix = "upload_form")
        predict_form = PredictInfoForm(prefix = "predict_form")
        files = FileInfo.objects.all()
        path = os.path.join('mlmodel', self.template)
        return render(self.request, path, {
            'upload_form': upload_form,
            'predict_form': predict_form,
            'files': files,
        })

        #     else:
        #         upload_form = FileInfoForm(prefix = "upload_form")
        #         predict_form = PredictInfoForm(prefix = "predict_form")
        #         files = FileInfo.objects.all()
        #         path = os.path.join('mlmodel', self.template)
        #         return render(self.request, path, {
        #             'upload_form': upload_form,
        #             'predict_form': predict_form,
        #             'files': files,
        #         })
        # else:
        #     upload_form = FileInfoForm(prefix = "upload_form")
        #     predict_form = PredictInfoForm(prefix = "predict_form")
        #     files = FileInfo.objects.all()
        #     path = os.path.join('mlmodel', self.template)
        #     return render(self.request, path, {
        #         'upload_form': upload_form,
        #         'predict_form': predict_form,
        #         'files': files,
        #     })
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
        filenames = FileInfo.objects.values_list('filepath', flat=True)
        mlmethod = getattr(PredictInfo.objects.last(), "mlmodels")
        senbyemail = getattr(PredictInfo.objects.last(), "sendbyemail")
        email = getattr(PredictInfo.objects.last(), "email")
        result = []
        if(mlmethod == "kmeans"):
            result = kmeans.websiteScriptKmeans(filenames)
        elif(mlmethod == "kmeansPCA"):
            result = kmeans.kmeansPCA(filenames)
        elif(mlmethod == "kmeansTSNE"):
            result = kmeans.kmeansTSNE(filenames)
        elif(mlmethod == "kmeansMeanshiftPCA"):
            result = kmeans.kmeansMeanshiftPCA(filenames)
        elif(mlmethod == "kmeansMeanshiftTSNE"):
            result = kmeans.kmeansMeanshiftTSNE(filenames)
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
            email_msg.send()
        elif senbyemail == False: # if select sendbyemail but not enter email addr
            # TODO:
            email = 1
    # return JsonResponse({'label': lable})    
    return JsonResponse({'label': label, 'image': result[1]})

def delete(request, pk):
    if request.method == 'POST':
        delete_file = FileInfo.objects.get(pk=pk)
        delete_file.delete()
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
