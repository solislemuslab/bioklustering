# Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the BioKlustering Website.

import os
import pandas as pd
import json
import time
import zipfile
from .models import FileInfo, FileListInfo
from django import forms
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.generic.edit import FormView
from django.http import FileResponse, HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login
from django.core.validators import MinValueValidator
from datetime import datetime, timezone
from mlmodel.forms import MyNumberInput, MySelect, FileInfoForm, FileListInfoForm, PredictInfoForm, ParametersInfoForm
from mlmodel.parser import kmeans, GMM, spectralClustering
from mlmodel.models import PredictInfo
from .parser.helpers import read_csv_labels
import traceback


# the login page
class LoginView(FormView):

    # sign up page
    def resigster(request):
        form = UserCreationForm()
        if request.method == 'POST':
            form = UserCreationForm(request.POST)

            if form.is_valid():
                form.save()
                username = form.cleaned_data['username']
                password = form.cleaned_data['password1']
                user = authenticate(username=username, password=password)
                login(request, user)
                return redirect('index')

        context = {'registerForm': form}
        path = os.path.join("registration", "register.html")
        return render(request, path, context)


# The home page
class PredictionView(FormView):

    def __init__(self, *args, **kwargs):
        super(FormView, self).__init__(*args, **kwargs)
        self.path = os.path.join('mlmodel', self.template_name)

    # Dispaly the home page
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            upload_form = FileInfoForm(prefix="upload_form")
            filelist_last = FileListInfo.objects.filter(user=self.request.user).last()
            filelist = getattr(filelist_last, 'filelist', None)
            if filelist is not None:
                filelist = filelist.all()
            filelist_form = FileListInfoForm(prefix="filelist_form", initial={'filelist': filelist})
            filelist_form.fields['filelist'].queryset = FileInfo.objects.filter(user=self.request.user)

            predict_info = PredictInfo.objects.filter(user=self.request.user)
            if predict_info is None or predict_info.last() is None:
                predict_info = PredictInfo.objects.create(user=self.request.user, mlmodels="unsupervisedKmeans")
            else:
                predict_info = predict_info.last()
            predict_info_param_str = getattr(predict_info, "parameters", "{}")
            if predict_info_param_str == '':  # prevent errors
                predict_info_param_str = "{}"
            predict_info_param_dict = json.loads(predict_info_param_str)
            predict_form = PredictInfoForm(prefix="predict_form", instance=predict_info)
            parameters_form = self.get_parameters_form(predict_info.mlmodels, predict_info_param_dict)

            return render(self.request, self.path, {
                'upload_form': upload_form,
                'filelist_form': filelist_form,
                'filelist': FileListInfo.objects.filter(user=self.request.user).last(),
                'predict_form': predict_form,
                'parameters_form': parameters_form,
            })
        else:
            upload_form = FileInfoForm(prefix="upload_form")
            filelist_last = FileListInfo.objects.last()
            filelist_form = FileListInfoForm(prefix="filelist_form")
            if filelist_last:
                filelist_form = FileListInfoForm(prefix="filelist_form",
                                                 initial={'filelist': getattr(filelist_last, 'filelist').all()})

            predict_info = PredictInfo.objects.last()
            if predict_info is None:
                predict_info = PredictInfo.objects.create()
                predict_info.mlmodels = "unsupervisedKmeans"
            predict_form = PredictInfoForm(prefix="predict_form", instance=predict_info)
            parameters_form = self.get_parameters_form(predict_info.mlmodels, getattr(predict_info, "content", {}))

            return render(self.request, self.path, {
                'upload_form': upload_form,
                'filelist_form': filelist_form,
                'filelist': FileListInfo.objects.last(),
                'predict_form': predict_form,
                'parameters_form': parameters_form,
            })

    # get the input from upload data, select files, choose models, ipnut parameters
    def post(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and self.request.method == 'POST':
            upload_form = FileInfoForm(self.request.POST, files=self.request.FILES, prefix="upload_form")
            filelist_form = FileListInfoForm(self.request.POST, prefix="filelist_form")
            filelist_form.fields['filelist'].queryset = FileInfo.objects.filter(user=self.request.user)
            predict_form = PredictInfoForm(self.request.POST, prefix="predict_form")

            upload_form.user = self.request.user
            filelist_form.user = self.request.user
            predict_form.user = self.request.user

            upload_form_isalid = upload_form.is_valid()
            filelist_form_isvalid = filelist_form.is_valid()
            predict_form_isvalid = predict_form.is_valid()

            # upload a file
            if upload_form_isalid and not predict_form_isvalid and not filelist_form_isvalid:
                upload_form2 = upload_form.save(commit=False)
                upload_form2.user = self.request.user
                upload_form2.save()
                #  process the uploaded file before writing it to database
                fileval = upload_form['filepath'].value()  # actual file
                filepath = os.path.join("media", "userfiles", fileval.name)
                self.handle_uploaded_file(fileval, filepath)
                labelval = upload_form['filepath'].value()  # actual file
                labelpath = os.path.join("media", "userfiles", labelval.name)
                self.handle_uploaded_file(labelval, labelpath)
                # save the filelist
            elif filelist_form_isvalid and not upload_form_isalid and not predict_form_isvalid:
                filelist = FileListInfo.objects.filter(user=self.request.user)
                if filelist is None or filelist.last() is None:
                    filelist = FileListInfo.objects.create(user=self.request.user)
                else:
                    filelist = filelist.last()
                if 'add_filelist' in self.request.POST:  # update filelist for prediction
                    filelist_form.fields['filelist'].queryset = FileInfo.objects.filter(user=self.request.user)
                    filelist_form.instance = filelist
                    filelist_form.save()
                elif 'delete_filelist' in self.request.POST:  # delete files from file list
                    filelist = filelist_form.cleaned_data['filelist']
                    for item in filelist:
                        item.delete()
            # choose a model or fill in parameters
            else:
                context = {}
                content = {}

                predict_info = PredictInfo.objects.filter(user=self.request.user).last()
                if predict_info is None:
                    predict_info = PredictInfo.objects.filter(user=self.request.user).create()
                    predict_info.mlmodels = "unsupervisedKmeans"
                if self.request.method == 'POST':
                    if 'mlmodels' in self.request.POST:  # choose model
                        predict_info.mlmodels = self.request.POST['mlmodels']
                        predict_info.save()
                        content = {}
                    elif 'predict_form-mlmodels' in self.request.POST:  # choose model
                        predict_info.mlmodels = self.request.POST['predict_form-mlmodels']
                        predict_info.save()
                        content = {}
                    else:  # submit params (or handle other invalid forms)
                        for key in self.request.POST.keys():
                            if key != 'csrfmiddlewaretoken':
                                content[key] = self.request.POST[key]

                filelist_last = FileListInfo.objects.filter(user=self.request.user).last()
                if filelist_form_isvalid or 'add_filelist' not in content:
                    if filelist_last:
                        filelist_form = FileListInfoForm(prefix="filelist_form",
                                                         initial={'filelist': getattr(filelist_last, 'filelist').all()})
                        filelist_form.fields['filelist'].queryset = FileInfo.objects.filter(user=self.request.user)

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
                    'filelist': FileListInfo.objects.filter(user=self.request.user).last(),
                    'predict_form': predict_form,
                    'parameters_form': parameters_form,
                })

            return redirect('index')

        return redirect('index')

    # Ensure that large files don’t overwhelm system’s memory
    def handle_uploaded_file(self, fileval, filepath):
        with open(filepath, 'wb+') as destination:
            for chunk in fileval.chunks():
                destination.write(chunk)

    # Dynamically generate a parameter form based on the selected model 
    def get_parameters_form(self, mlmodels, content):
        if mlmodels == "unsupervisedGMM":
            cov_types = [
                ('spherical', 'Spherical'),
                ('diag', 'Diag'),
                ('tied', 'Tied'),
                ('full', 'Full'),
            ]
            visual_types = [
                ('PCA', 'PCA'),
                ('TSNE', 'TSNE'),
            ]
            cov_type_img1 = os.path.join("media", "models", "images", "gmm_cov_type_1.png")
            cov_type_img2 = os.path.join("media", "models", "images", "gmm_cov_type_2.png")
            cov_type_img3 = os.path.join("media", "models", "images", "gmm_cov_type_3.png")
            cov_type_img4 = os.path.join("media", "models", "images", "gmm_cov_type_4.png")
            new_fields = {
                'k_min': forms.IntegerField(validators=[MinValueValidator(2)],
                                            widget=MyNumberInput(attrs={
                                                "class": "form-control",
                                                "label": "K-min",
                                                "help_text": "The minimum length of k-mer. You can choose a value starting at 2. Less than 6 is recommended according to our experiments. Default is set to be 2."
                                            })),
                'k_max': forms.IntegerField(validators=[MinValueValidator(2)],
                                            widget=MyNumberInput(attrs={
                                                "class": "form-control",
                                                "label": "K-max",
                                                "help_text": "The maximum length of k-mer. You can choose a value starting at 2. Less than 6 is recommended according to our experiments. Default is set to be 3."
                                            })),
                'num_class': forms.IntegerField(validators=[MinValueValidator(2)],
                                                widget=MyNumberInput(attrs={
                                                    "class": "form-control",
                                                    "label": "Number of classes",
                                                    "help_text": "The number of predicted labels. You can choose a value starting at 2. Default is set to be 2."
                                                })),
                'cov_type': forms.ChoiceField(choices=cov_types,
                                              widget=MySelect(attrs={
                                                  "class": "custom-select",
                                                  "label": "Covariance type",
                                                  "help_text": "Type of covariance. There are four types of covariances: spherical, diagonal, tied, and full. Default is set to be full. More details see <u>Learn More about GMM</u> above.",
                                                  "isHtml": True
                                              })),
                'seed': forms.IntegerField(validators=[MinValueValidator(2)],
                                           widget=MyNumberInput(attrs={
                                               "class": "form-control",
                                               "label": "Seed",
                                               "help_text": "The random seed to reproduce the results. Please select an integer less than 10 digits. If none chosen, it will be internally selected and returned to the used in the logfiles."
                                           })),
                'visual': forms.ChoiceField(choices=visual_types,
                                            widget=MySelect(attrs={
                                                "class": "custom-select",
                                                "label": "Visualization",
                                                "help_text": "Dimension-reduction technique to visualize the clusters",
                                                "isHtml": True
                                            })),
                'description': {
                    'Gaussian Mixture Model (GMM)': 'GMM is a probabilistic model that estimates the underlying multiple Gaussian distributions behind the observations. Input will be gene sequences, aligned or unaligned, coverted to k-mer counts and output will be predicted labels for each sequence: 0,1, etc. A k-mer table will be created to transfer the input data for analysis. When using this model, the following parameters are needed:',
                    'K-mer': 'Consecutive genes of length k. The range of length of k-mer can be adjusted. For instance, if you set the minimum length to be 3 and maximum length 3 for gene sequence ATGG, two k-mers ATG and TGG are considered.',
                    'K-min': 'The minimum length of k-mer to include in the k-mer table. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 2.',
                    'K-max': 'The maximum length of k-mer to include in the k-mer table. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 3.',
                    'Number of classes': 'The number of predicted labels. Default is set to be 2.',
                    'Covariance type': 'The type of covariance. There are four types of covariances: spherical, diagonal, tied, and full. Default is set to be full. See the following figure of how they work: <br><img src="%s"><br><img src="%s"><br><img src="%s"><br><img src="%s">' % (
                    cov_type_img1, cov_type_img2, cov_type_img3, cov_type_img4)
                }
            }
            # default values of the paramters
            if not bool(content) or 'k_min' not in content:
                content = {
                    'k_min': 2,
                    'k_max': 3,
                    'num_class': 2,
                    'cov_type': 'full',
                    'seed': int(time.time()),
                    'visual': 'PCA'
                }
        elif mlmodels == "semisupervisedGMM":
            cov_types = [
                ('spherical', 'Spherical'),
                ('diag', 'Diag'),
                ('tied', 'Tied'),
                ('full', 'Full'),
            ]
            visual_types = [
                ('PCA', 'PCA'),
                ('TSNE', 'TSNE'),
            ]
            model_selection = [
                ('Yes', 'Yes'),
                ('No', 'No')
            ]
            cov_type_img1 = os.path.join("media", "models", "images", "gmm_cov_type_1.png")
            cov_type_img2 = os.path.join("media", "models", "images", "gmm_cov_type_2.png")
            cov_type_img3 = os.path.join("media", "models", "images", "gmm_cov_type_3.png")
            cov_type_img4 = os.path.join("media", "models", "images", "gmm_cov_type_4.png")
            new_fields = {
                'k_min': forms.IntegerField(validators=[MinValueValidator(2)],
                                            widget=MyNumberInput(attrs={
                                                "class": "form-control",
                                                "label": "K-min",
                                                "help_text": "The minimum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 2."
                                            })),
                'k_max': forms.IntegerField(validators=[MinValueValidator(2)],
                                            widget=MyNumberInput(attrs={
                                                "class": "form-control",
                                                "label": "K-max",
                                                "help_text": "The maximum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 3."
                                            })),
                'num_class': forms.IntegerField(validators=[MinValueValidator(2)],
                                                widget=MyNumberInput(attrs={
                                                    "class": "form-control",
                                                    "label": "Number of classes",
                                                    "help_text": "The number of predicted labels. You can choose starting from 2. Default is set to be 2."
                                                })),
                'cov_type': forms.ChoiceField(choices=cov_types,
                                              widget=MySelect(attrs={
                                                  "class": "custom-select",
                                                  "label": "Covariance type",
                                                  "help_text": "Type of covariance. There are four types of covariances: spherical, diagonal, tied, and full. Default is set to be full. More details see <u>Learn More about GMM</u> above.",
                                                  "isHtml": True
                                              })),
                'seed': forms.IntegerField(validators=[MinValueValidator(2)],
                                           widget=MyNumberInput(attrs={
                                               "class": "form-control",
                                               "label": "Seed",
                                               "help_text": "The random seed to reproduce the results. Please select an integer less than 10 digits. If none are selected, it will be determined by current time."
                                           })),
                'visual': forms.ChoiceField(choices=visual_types,
                                            widget=MySelect(attrs={
                                                "class": "custom-select",
                                                "label": "Visualization",
                                                "help_text": "Dimension-reduction technique to visualize the clusters",
                                                "isHtml": True
                                            })),
                'model_selection': forms.ChoiceField(choices=model_selection,
                                                     widget=MySelect(attrs={
                                                         "class": "custom-select",
                                                         "label": "Model Selection",
                                                         "help_text": "If you are not sure how to choose parameters, you can use model selection. We will return the prediction with the best accuracy based on the number of classes you enter. The prediction might take longer if you use model selection.",
                                                         "isHtml": True
                                                     })),
                'description': {
                    'Gaussian Mixture Model (GMM)': 'GMM is a probabilistic model that estimates the underlying multiple Gaussian distributions behind the observations. Input will be gene sequences, aligned or unaligned, coverted to k-mer counts and output will be predicted labels for each sequence: 0,1, etc. A k-mer table will be created to transfer the input data for analysis. When using this model, the following parameters are needed:',
                    'K-mer': 'Consecutive genes of length k. The range of length of k-mer can be adjusted. For instance, if you set the minimum length to be 3 and maximum length 3 for gene sequence ATGG, two k-mers ATG and TGG are considered.',
                    'K-min': 'The minimum length of k-mer to include in the k-mer table. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 2.',
                    'K-max': 'The maximum length of k-mer to include in the k-mer table. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 3.',
                    # 'Number of classes': 'The number of predicted labels. Default is set to be 2.',
                    'Covariance type': 'The type of covariance. There are four types of covariances: spherical, diagonal, tied, and full. Default is set to be full. See the following figure of how they work: <br><img src="%s"><br><img src="%s"><br><img src="%s"><br><img src="%s">' % (
                    cov_type_img1, cov_type_img2, cov_type_img3, cov_type_img4)
                }
            }
            # default values of the paramters
            if not bool(content) or 'k_min' not in content:
                content = {
                    'k_min': 2,
                    'k_max': 3,
                    'num_class': 2,
                    'cov_type': 'full',
                    'seed': int(time.time()),
                    'visual': 'PCA',
                    'model_selection': 'No'
                }
        elif mlmodels == "unsupervisedSpectralClustering":
            assignLabels = [
                ('kmeans', 'kmeans'),
                ('discretize', 'discretize')
            ]
            visual_types = [
                ('PCA', 'PCA'),
                ('TSNE', 'TSNE'),
            ]
            new_fields = {
                'k_min': forms.IntegerField(validators=[MinValueValidator(2)],
                                            widget=MyNumberInput(attrs={
                                                "class": "form-control",
                                                "label": "K-min",
                                                "help_text": "The minimum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 2."
                                            })),
                'k_max': forms.IntegerField(validators=[MinValueValidator(2)],
                                            widget=MyNumberInput(attrs={
                                                "class": "form-control",
                                                "label": "K-max",
                                                "help_text": "The maximum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 3."
                                            })),
                'num_cluster': forms.IntegerField(validators=[MinValueValidator(2)],
                                                  widget=MyNumberInput(attrs={
                                                      "class": "form-control",
                                                      "label": "Number of Clusters",
                                                      "help_text": "The number of predicted labels. You can choose starting from 2. Default is set to be 2."
                                                  })),
                'assignLabels': forms.ChoiceField(choices=assignLabels,
                                                  widget=MySelect(attrs={
                                                      "class": "custom-select",
                                                      "label": "Assign Labels",
                                                      "help_text": "The way to assign label at the final stage of spectral clustering. Can be 'kmeans' or 'discretize'.",
                                                      "isHtml": True
                                                  })),
                'seed': forms.IntegerField(validators=[MinValueValidator(2)],
                                           widget=MyNumberInput(attrs={
                                               "class": "form-control",
                                               "label": "Seed",
                                               "help_text": "The random seed to reproduce the results. Please select an integer less than 10 digits. If none are selected, it will be determined by current time."
                                           })),
                'visual': forms.ChoiceField(choices=visual_types,
                                            widget=MySelect(attrs={
                                                "class": "custom-select",
                                                "label": "Visualization",
                                                "help_text": "Dimension-reduction technique to visualize the clusters",
                                                "isHtml": True
                                            })),
                'description': {
                    "Spectral Clustering": "The spectral clustering method uses the information behind the eigenvalues of the kmer table that is created based on the input dataset. It will successfully reduce the dimensionality of the input data set. This method also shows the visualization of the clustering using two principle components of the kmer table.",
                    "K-min": "An integer. The minimum of kmer",
                    "K-max": "An integer. The maximum of kmer",
                    "Number of Clusters": "An integer. The number of clusters",
                    "Assign Labels": "A string. The way to assign label at the final stage of spectral clustering. Can be 'kmeans' or 'discretize'."
                }
            }
            # default values of the paramters
            if not bool(content) or 'k_min' not in content:
                content = {
                    'k_min': 2,
                    'k_max': 3,
                    'num_cluster': 2,
                    'assignLabels': 'kmeans',
                    'visual': 'PCA',
                    'seed': int(time.time()),
                }
        elif mlmodels == "semisupervisedSpectralClustering":
            assignLabels = [
                ('none', 'none'),
                ('kmeans', 'kmeans'),
                ('discretize', 'discretize')
            ]
            visual_types = [
                ('PCA', 'PCA'),
                ('TSNE', 'TSNE'),
            ]
            new_fields = {
                'k_min': forms.IntegerField(validators=[MinValueValidator(2)],
                                            widget=MyNumberInput(attrs={
                                                "class": "form-control",
                                                "label": "K-min",
                                                "help_text": "The minimum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 2."
                                            })),
                'k_max': forms.IntegerField(validators=[MinValueValidator(2)],
                                            widget=MyNumberInput(attrs={
                                                "class": "form-control",
                                                "label": "K-max",
                                                "help_text": "The maximum length of k-mer. You can choose starting from 2. However, less than 6 is recommended according to our experiments. Default is set to be 3."
                                            })),
                'num_cluster': forms.IntegerField(validators=[MinValueValidator(2)],
                                                  widget=MyNumberInput(attrs={
                                                      "class": "form-control",
                                                      "label": "Number of Clusters",
                                                      "help_text": "The number of predicted labels. You can choose starting from 2. Default is set to be 2."
                                                  })),
                'assignLabels': forms.ChoiceField(choices=assignLabels,
                                                  widget=MySelect(attrs={
                                                      "class": "custom-select",
                                                      "label": "Assign Labels",
                                                      "help_text": "The way to assign label at the final stage of spectral clustering. Can be 'kmeans' or 'discretize'.",
                                                      "isHtml": True
                                                  })),
                'seed': forms.IntegerField(validators=[MinValueValidator(2)],
                                           widget=MyNumberInput(attrs={
                                               "class": "form-control",
                                               "label": "Seed",
                                               "help_text": "The random seed to reproduce the results. Please select an integer less than 10 digits. If none are selected, it will be determined by current time."
                                           })),
                'visual': forms.ChoiceField(choices=visual_types,
                                            widget=MySelect(attrs={
                                                "class": "custom-select",
                                                "label": "Visualization",
                                                "help_text": "Dimension-reduction technique to visualize the clusters",
                                                "isHtml": True
                                            })),
                'description': {
                    "Spectral Clustering": "The spectral clustering method uses the information behind the eigenvalues of the kmer table that is created based on the input dataset. It will successfully reduce the dimensionality of the input data set. This method also shows the visualization of the clustering using two principle components of the kmer table.",
                    "K-min": "An integer. The minimum of length of k-mer",
                    "K-max": "An integer. The maximum of length of k-mer",
                    "Number of Clusters": "An integer. The number of clusters",
                    "Assign Labels": "A string. The way to assign label at the final stage of spectral clustering. Can be 'kmeans' or 'discretize'."
                }
            }
            # default values of the paramters
            if not bool(content) or 'k_min' not in content:
                content = {
                    'k_min': 2,
                    'k_max': 3,
                    'num_cluster': 2,
                    'assignLabels': 'none',
                    'seed': int(time.time()),
                    'visual': 'PCA'
                }
        elif mlmodels == "unsupervisedKmeans":
            visual_types = [
                ('PCA', 'PCA'),
                ('TSNE', 'TSNE'),
            ]
            new_fields = {
                'klength_min': forms.IntegerField(validators=[MinValueValidator(2)],
                                                  widget=MyNumberInput(attrs={
                                                      "class": "form-control",
                                                      "label": "K Length Min",
                                                      "help_text": "The minimum kmer length, defaulted to 6."
                                                  })),
                'klength_max': forms.IntegerField(validators=[MinValueValidator(2)],
                                                  widget=MyNumberInput(attrs={
                                                      "class": "form-control",
                                                      "label": "K Length Max",
                                                      "help_text": "The maximum kmer length, defaulted to 6."
                                                  })),
                'rNum': forms.IntegerField(validators=[MinValueValidator(2)],
                                           widget=MyNumberInput(attrs={
                                               "class": "form-control",
                                               "label": "Seed",
                                               "help_text": "The random seed to reproduce the results. Please select an integer less than 10 digits. If none are selected, it will be determined based on the time."
                                           })),
                'cNum': forms.IntegerField(validators=[MinValueValidator(2)],
                                           widget=MyNumberInput(attrs={
                                               "class": "form-control",
                                               "label": "Number of clusters",
                                               "help_text": "Number of clusters, defaulted to 2."
                                           })),
                'visual': forms.ChoiceField(choices=visual_types,
                                            widget=MySelect(attrs={
                                                "class": "custom-select",
                                                "label": "Visualization",
                                                "help_text": "Dimension-reduction technique to visualize the clusters",
                                                "isHtml": True
                                            })),
                'description': {
                    "Unsupervised Kmeans": "kmeans is an unsupervised clustering method that clusters the data into k clusters and assigns labels to each each data point. Every point is assigned to the nearest centroid, and these centroids are formed by minimizing the squared Euclidian distances within each cluster.",
                    "K Length Min": "The minimum k-mer length, defaulted to 6.",
                    "K Length Max": "The maximum k-mer length, defaulted to 6.",
                    "Seed": "Random seed. If none are selected, it will be determined based on the time.",
                    "Number of clusters": "Number of clusters, defaulted to 2."
                }
            }
            # default values of the paramters
            if not bool(content) or 'klength_min' not in content:
                content = {
                    'klength_min': 6,
                    'klength_max': 6,
                    'rNum': int(time.time()),
                    'cNum': 2,
                    'visual': 'PCA'
                }
        elif mlmodels == "semisupervisedKmeans":
            visual_types = [
                ('PCA', 'PCA'),
                ('TSNE', 'TSNE'),
            ]
            new_fields = {
                'klength_min': forms.IntegerField(validators=[MinValueValidator(2)],
                                                  widget=MyNumberInput(attrs={
                                                      "class": "form-control",
                                                      "label": "K Length Min",
                                                      "help_text": "The minimum kmer length, defaulted to 6."
                                                  })),
                'klength_max': forms.IntegerField(validators=[MinValueValidator(2)],
                                                  widget=MyNumberInput(attrs={
                                                      "class": "form-control",
                                                      "label": "K Length Max",
                                                      "help_text": "The maximum kmer length, defaulted to 6."
                                                  })),
                'rNum': forms.IntegerField(validators=[MinValueValidator(2)],
                                           widget=MyNumberInput(attrs={
                                               "class": "form-control",
                                               "label": "Seed",
                                               "help_text": "Random seed number. If none selected, it will be determined based on the time."
                                           })),
                'cNum': forms.IntegerField(validators=[MinValueValidator(2)],
                                           widget=MyNumberInput(attrs={
                                               "class": "form-control",
                                               "label": "Number of clusters",
                                               "help_text": "Number of clusters, defaulted to 2."
                                           })),
                'visual': forms.ChoiceField(choices=visual_types,
                                            widget=MySelect(attrs={
                                                "class": "custom-select",
                                                "label": "Visualization",
                                                "help_text": "Dimension-reduction technique to visualize the clusters",
                                                "isHtml": True
                                            })),
                'description': {
                    "Semi-supervised Kmeans": "The meanshift algorithm is used to identity locations of high density within the k-mer space of the data, and then the unsupervised k-means model is run with these locations as the initial centroid coordinates.  The known labels are then compared against the many predicted labels and these clusters are reassigned into groups that minimize the prediction error.",
                    "K Length Min": "The minimum k-mer length, defaulted to 6.",
                    "K Length Max": "The maximum k-mer length, defaulted to 6.",
                    "Seed": "Random seed number. If none selected, it will be determined based on the time.",
                }
            }
            # default values of the paramters
            if not bool(content) or 'klength_min' not in content:
                content = {
                    'klength_min': 6,
                    'klength_max': 6,
                    'rNum': int(time.time()),
                    'cNum': 2,
                    'visual': 'PCA'
                }
        else:
            new_fields = {}
            if not bool(content):
                content = {}

        DynamicParametersInfoForm = type('DynamicParametersInfoForm', (ParametersInfoForm,), new_fields)
        parameters_form = DynamicParametersInfoForm(content)
        return parameters_form


# The reult page
class ResultView(FormView):

    def __init__(self, *args, **kwargs):
        super(FormView, self).__init__(*args, **kwargs)
        self.path = os.path.join('mlmodel', self.template_name)

    # render the result page and it will make the prediction using ajax
    def get(self, request, *args, **kwargs):
        return render(self.request, self.path)

    # actual predict that runs the selected machine learning algorithm
    # and generate the plot and the table
    def process(request):
        start = time.time()
        context = {}
        files = FileInfo.objects.filter(user=request.user).all()
        if len(files) == 0:
            return redirect('index')
        if request.method == 'POST':
            filslist_obj = FileListInfo.objects.filter(user=request.user).last()
            preidct_obj = PredictInfo.objects.filter(user=request.user).last()
            filenames = str(filslist_obj).split(sep=", ")
            mlmethod = getattr(preidct_obj, "mlmodels")
            result = []
            try:
                if mlmethod == "unsupervisedKmeans":
                    params_str = getattr(preidct_obj, "parameters")
                    params_obj = json.loads(params_str)
                    klength_min = int(params_obj['klength_min'])
                    klength_max = int(params_obj['klength_max'])
                    rNum = int(params_obj['rNum'])
                    cNum = int(params_obj['cNum'])
                    method = str(params_obj['visual'])
                    result = kmeans.kmeans(request.user.id, filenames, klength_min, klength_max, rNum, cNum, method)
                elif mlmethod == "semisupervisedKmeans":
                    params_str = getattr(preidct_obj, "parameters")
                    params_obj = json.loads(params_str)
                    klength_min = int(params_obj['klength_min'])
                    klength_max = int(params_obj['klength_max'])
                    rNum = int(params_obj['rNum'])
                    cNum = int(params_obj['cNum'])
                    method = str(params_obj['visual'])
                    filenames = []
                    label_filenames = []
                    for obj in filslist_obj.filelist.all():
                        filenames.append(obj.filepath.name)
                        label_filenames.append(obj.labelpath.name)
                    labels = read_csv_labels(label_filenames)
                    result = kmeans.kmeans_semiSupervised(request.user.id, filenames, klength_min, klength_max, rNum, cNum,
                                                          labels, method)
                elif mlmethod == "unsupervisedGMM":
                    params_str = getattr(preidct_obj, "parameters")
                    params_obj = json.loads(params_str)
                    k_min = int(params_obj['k_min'])
                    k_max = int(params_obj['k_max'])
                    num_class = int(params_obj['num_class'])
                    cov_type = str(params_obj['cov_type'])
                    seed = int(params_obj['seed'])
                    method = str(params_obj['visual'])
                    result = GMM.get_predictions(request.user.id, filenames, k_min, k_max, num_class, cov_type, seed,
                                                 method)
                elif mlmethod == "semisupervisedGMM":
                    params_str = getattr(preidct_obj, "parameters")
                    params_obj = json.loads(params_str)
                    k_min = int(params_obj['k_min'])
                    k_max = int(params_obj['k_max'])
                    num_class = int(params_obj['num_class'])
                    cov_type = str(params_obj['cov_type'])
                    seed = int(params_obj['seed'])
                    method = str(params_obj['visual'])
                    model_selection = str(params_obj['model_selection'])
                    filenames = []
                    label_filenames = []
                    for obj in filslist_obj.filelist.all():
                        filenames.append(obj.filepath.name)
                        label_filenames.append(obj.labelpath.name)
                    labels = read_csv_labels(label_filenames)
                    if model_selection == "Yes":
                        result = GMM.model_selection(request.user.id, filenames, labels, num_class, seed, method)
                    else:
                        result = GMM.get_predictions_semi(request.user.id, filenames, k_min, k_max, num_class, cov_type,
                                                          seed, labels, method)
                elif mlmethod == "unsupervisedSpectralClustering":
                    params_str = getattr(preidct_obj, "parameters")
                    params_obj = json.loads(params_str)
                    k_min = int(params_obj['k_min'])
                    k_max = int(params_obj['k_max'])
                    seed = int(params_obj['seed'])
                    num_cluster = int(params_obj['num_cluster'])
                    assignLabels = str(params_obj['assignLabels'])
                    method = str(params_obj['visual'])
                    result = spectralClustering.spectral_clustering(request.user.id, filenames, k_min, k_max,
                                                                    num_cluster, assignLabels, method, seed)
                elif mlmethod == "semisupervisedSpectralClustering":
                    params_str = getattr(preidct_obj, "parameters")
                    params_obj = json.loads(params_str)
                    k_min = int(params_obj['k_min'])
                    k_max = int(params_obj['k_max'])
                    num_cluster = int(params_obj['num_cluster'])
                    assignLabels = str(params_obj['assignLabels'])
                    seed = int(params_obj['seed'])
                    method = str(params_obj['visual'])
                    filenames = []
                    label_filenames = []
                    for obj in filslist_obj.filelist.all():
                        filenames.append(obj.filepath.name)
                        label_filenames.append(obj.labelpath.name)
                    labels = read_csv_labels(label_filenames)
                    result = spectralClustering.intuitive_semi_supervised(request.user.id, filenames, labels, k_min,
                                                                          k_max, num_cluster, assignLabels, seed,
                                                                          method)

            # Following is the updated exception handler, print out the traceback for easier debugging
            except Exception as e:
                traceback.print_exc()
                # return JsonResponse({'error': str(e)}, status=400)
                return JsonResponse({'error':'Something wrong with the prediction. If you are using semi-supervised model, please make sure the number of labels match the number of sequences. If you continue to see this error, please report this issue to https://github.com/solislemuslab/bioklustering/issues. Make sure you include the steps to reproduce the error.'}, status=400)

            list_of_df = result[0]
            all_df = pd.concat(list_of_df)
            # make the index and other column labels to be on same line
            all_df.columns.name = all_df.index.name
            all_df.index.name = None
            label = all_df.to_html(col_space=110, justify='left', classes='table table-responsive result-table')
            # write to csv
            if not os.path.exists(os.path.join('media', 'resultfiles')):
                os.makedirs(os.path.join('media', 'resultfiles'))
            csv_path = os.path.join("media", "resultfiles", str(request.user.id) + "table.csv")
            all_df.to_csv(csv_path, index_label='ID')
            duration = (time.time() - start) * 1000
            ResultView.create_zip(request, duration)
            
            # return the image and table to result page
            context['label'] = label
            context['plotly_dash'] = result[1]
        return JsonResponse(context)

    # put the plot, table and parameter information into a zip file
    def create_zip(request, duration):
        predict_obj = PredictInfo.objects.filter(user=request.user).last()
        # write params info into a text file
        if not os.path.exists(os.path.join('media', 'resultfiles')):
            os.makedirs(os.path.join('media', 'resultfiles'))
        param_path = os.path.join('media', 'resultfiles', str(request.user.id) + 'params.txt')
        param_file = open(param_path, 'w')
        param_file.write('model: ' + predict_obj.get_mlmodels_display() + '\n')
        params_str = getattr(predict_obj, "parameters")
        params_dict = json.loads(params_str)
        del params_dict['submit_params']
        for param in params_dict.items():
            param_file.write(': '.join(param) + '\n')
        # current date time
        utc_dt = datetime.now(timezone.utc)  # UTC time
        dt = utc_dt.astimezone().isoformat()  # local time
        param_file.write("created time: " + dt + "\n")
        # running time
        param_file.write("running time: {:.2f} ms\n".format(duration))
        param_file.write(
            "note: if you see the parameter values here are different from what you chose, it is because the underlying model finds the best parameter values with the best accuracy based on your input.")
        param_file.close()
        # write csv, params, images into a zipfile
        csv_path = os.path.join('media', 'resultfiles', str(request.user.id) + 'table.csv')
        img_path = os.path.join('media', 'images', str(request.user.id) + 'plotly.png')
        zip_path = os.path.join('media', 'resultfiles', str(request.user.id) + 'results.zip')
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.write(csv_path)
            zf.write(param_path)
            zf.write(img_path)
            zf.close()

    # down the zip file
    def download_zip(request, userId):
        filename = str(userId) + 'results.zip'
        fs = FileSystemStorage()
        response = FileResponse(fs.open(os.path.join('resultfiles', filename), 'rb'), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response


# The FAQ page
class FAQView(FormView):

    def __init__(self, *args, **kwargs):
        super(FormView, self).__init__(*args, **kwargs)
        self.path = os.path.join('mlmodel', self.template_name)

    # render the faq page
    def get(self, request, *args, **kwargs):
        return render(self.request, self.path)
