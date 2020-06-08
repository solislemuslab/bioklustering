from django.shortcuts import redirect, render
from .forms import FileInfoForm
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
from mlmodel.parser.kmeans import *

# Create your views here.
def index(request):
    return redirect('upload')

def upload(request):
    if request.method == 'POST':
        form = FileInfoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            #  process the uploaded file before writing it to database
            f = form['filepath'].value()
            filepath = f.name
            handle_uploaded_file(f, filepath)
            return redirect('upload')
        else:
            files = FileInfo.objects.all()
            path = os.path.join('mlmodel', 'upload.html')
            return render(request, path, {
                "form": form,
                "files": files,
            })
    else:
        form = FileInfoForm()
        files = FileInfo.objects.all()
        path = os.path.join('mlmodel', 'upload.html')
        return render(request, path, {
            "form": form,
            "files": files,
        })

def delete(request, pk):
    if request.method == 'POST':
        delete_file = FileInfo.objects.get(pk=pk)
        delete_file.delete()
    return redirect('upload')

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

def predict(request):
    # files = FileInfo.objects.all()
    # if files[0].sendbyemail:
    #     path = os.path.join('mlmodel', 'sendbyemail.html')
    #     render(request, path)
    # else:
    #     path = os.path.join('mlmodel', 'result.html')
    #     return render(request, path)
    # if request.method == 'GET':
    #     if form.is_valid():
    #         sendbyemail = request.POST.get('sendbyemail')
    #         if request.sendbyemail:
    #             path = os.path.join('mlmodel', 'sendbyemail.html')
    #             render(request, path)
    #         else:
    #             path = os.path.join('mlmodel', 'result.html')
    #             return render(request, path)
    path = os.path.join('mlmodel', 'result.html')
    return render(request, path)

# actual predict 
def process(request):
    files = FileInfo.objects.all()
    form = FileInfoForm()
    lable = "<div>Fail to predict labels.</div>"
    if request.method == 'GET':
        if len(files) == 0:
            return redirect("upload")
        filenames = FileInfo.objects.values_list('filepath', flat=True)
        list_of_df = websiteScriptKmeans(filenames)
        all_df = pd.concat(list_of_df)
        # make the index and other column labels to be on same line
        all_df.columns.name = all_df.index.name
        all_df.index.name = None
        lable = all_df.to_html(col_space=110, justify='left')
        # write to csv
        path = os.path.join("media", "resultfiles", "result.csv")
        all_df.to_csv(path, index_label='ID')
    return JsonResponse({'label': lable})

# a function to ensure that large files don’t overwhelm system’s memory
def handle_uploaded_file(f, filepath):
    with open(filepath, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
