from django.shortcuts import redirect, render
from .models import FileInfo
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from .parser.parseFasta import *
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as ug
from django.core.exceptions import ValidationError
from django import forms
import os 
from django.core.files.storage import FileSystemStorage
import pandas as pd
from mlmodel.forms import FileInfoForm, PredictInfoForm
from django.views.generic.edit import FormView
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
            if upload_form.is_valid() and not predict_form.is_valid():
                upload_form.save()
                #  process the uploaded file before writing it to database
                f = upload_form['filepath'].value()
                filepath = f.name
                handle_uploaded_file(f, filepath)
                return redirect('index') #TODO
            elif predict_form.is_valid() and not upload_form.is_valid():
                files = FileInfo.objects.all()
                path = os.path.join('mlmodel', 'result.html')
                if len(files) != 0:
                    predict_form.save()
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
