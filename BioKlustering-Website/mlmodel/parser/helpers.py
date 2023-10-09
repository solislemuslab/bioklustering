# Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the BioKlustering Website.

import os
import json
import datetime
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from plotly.offline import plot
from mlmodel.models import PredictInfo, FileInfo
from django.http import HttpResponse

# show the prediction in plotly dashboard which allows
# interactive functionalities
# userId: user's id (used for filename)
# kmer_table: kmer table
# label: cluster label in ndarray
# model_title: the name of the plot
def plotly_dash_show_plot(userId, kmer_table, labels, model_title, method, ID = None):
    if method == "PCA":
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(kmer_table)
        results = pca_result
    elif method == "TSNE":
        tsne = TSNE(n_components=2, random_state = 0)
        tsne_result = tsne.fit_transform(kmer_table)
        results = tsne_result
    random_list = []
    for i in range(len(results[:,0])):
        random_list.append(None)
    if ID is None:
        ID = random_list
    dots = {'x':results[:,0], 'y':results[:,1], 'label':labels, "ID":ID}
    # add the following line for Spectral Clustering
    numpy_labels = np.array(labels)
    dots['label'] = numpy_labels.astype(str)
    df = pd.DataFrame(dots)
    fig = px.scatter(df, x='x', y='y', 
        title=model_title + " " + method,
        labels=dict(x="Principal component 1", y="Principal component 2", label="Label"), 
        color='label', hover_data=['ID'])
    # plotly dashboard in html 
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    # save the static plot into media
    if not os.path.exists(os.path.join('media', 'images')):
        os.makedirs(os.path.join('media', 'images'))
    fig.write_image(os.path.join('media', 'images', str(userId)+'plotly.png'))
    
    return plot_div

# a method that combines the labels in the label files 
# into one array and in the right order
# label_paths: a list of label paths
def read_csv_labels(label_paths):
    all_labels = pd.Series()
    for path in label_paths:
        path = os.path.join("media", path)
        labels = pd.read_csv(path, header=None)
        # get first column
        labels = labels.iloc[:,0].tolist()
        # remove header if the csv has a header
        if isinstance(labels[0], str):
            labels.pop(0)
        # ensure all labels are integers
        labels = [int(i) for i in labels]
        labels = pd.Series(labels)
        #all_labels = all_labels.append(labels, ignore_index=True)
        all_labels = pd.concat([all_labels, labels], ignore_index=True)
    all_labels.name = "Labels"
    return all_labels

# def read_fasta_sequences(sequence_paths):
#     all_sequences = pd.DataFrame()
#     for path in sequence_paths:
#         path = os.path.join("media", path)
#         sequence = parseFasta(path)
#         all_sequences = all_sequences.append(sequence, ignore_index=True)
#     all_sequences.name = "Sequence"
#     return all_sequences

# update the parameters in the predictInfo object for params.txt and front end
# userId: a number
# new_params: a dictinary where key is the param name and value is the param value
def update_parameters(userId, new_params):
    predict_info = PredictInfo.objects.filter(user=userId).last()
    predict_info_params = getattr(predict_info, "parameters")
    predict_info_params_dict = json.loads(predict_info_params)
    for param in new_params.items():
        key = param[0]
        value = param[1]
        predict_info_params_dict[key] = str(value)
    predict_info.parameters = json.dumps(predict_info_params_dict)
    predict_info.save()

# helper that delete files periodically
def file_cleanup(request):
    today = datetime.date.today()
    period = datetime.timedelta(30)
    filter_date = today - period
    # filter files that are 30 days ago
    filter_files = FileInfo.objects.filter(create_date__lte=filter_date)
    for f in filter_files:
        # uncomment below to see which files will get deleted
        # print(str(f.create_date) + ": " + str(f) + ", " + str(f.getLabelPaths()))
        f.delete()
    return HttpResponse({"file cleanup success": ""})

    