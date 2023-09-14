# Copyright 2020 by Luke Selberg, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the BioKlustering Website.

import pandas as pd
from Bio import SeqIO
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.cluster import MeanShift
from sklearn import preprocessing
import numpy as np
import os
from .helpers import plotly_dash_show_plot

def parseFasta(data):
    d = {fasta.id : str(fasta.seq) for fasta in SeqIO.parse(data, "fasta")}
    pd.DataFrame([d])

    s = pd.Series(d, name='Sequence')
    s.index.name = 'ID'
    s.reset_index()
    return pd.DataFrame(s)

def kmerXTable(s, a, b):
    tfid_vector = TfidfVectorizer(analyzer='char', ngram_range=(a,b))
    s_hat = tfid_vector.fit_transform(s.Sequence)
    kmerNames = tfid_vector.get_feature_names()
    kmers = s_hat.toarray()
    return pd.DataFrame(kmers,columns=kmerNames, index = s.index)

# credit to chunrong
def read_fasta_sequences(sequence_paths):
    all_sequences = pd.DataFrame()
    for path in sequence_paths:
        path = os.path.join("media", path)
        sequence = parseFasta(path)
        all_sequences = pd.concat([all_sequences, sequence])
    return all_sequences

def get_ids_from_fasta(sequence_paths):
    retval = []
    for path in sequence_paths:
        path = os.path.join("media", path)
        d = {fasta.id : str(fasta.seq) for fasta in SeqIO.parse(path, "fasta")}
        retval = np.concatenate((np.array(retval), np.array(list(d.keys()))))
    return retval

# didn't change because unsupervised k means doesn't require actual labels.
def kmeans(userId, fasta, klength_min, klength_max, rNum, cNum, method):
    inputData = read_fasta_sequences(fasta)
    inputData["Sequence"] = inputData["Sequence"].apply(lambda x: x.replace("-", ""))
    IDs = get_ids_from_fasta(fasta)
    print("IDs:", IDs)
    kmerXTableInput = kmerXTable(inputData, klength_min, klength_max)
    #km = KMeans(random_state = rNum, n_clusters = cNum)
    #km.fit(kmerXTableInput) 
    #y_hat = km.predict(kmerXTableInput)
    PCAembedding = PCA(n_components=10)
    NkmerXTableInput = preprocessing.normalize(kmerXTableInput)
    PCAembedding_low = PCAembedding.fit_transform(NkmerXTableInput)
    
    ms = MeanShift()
    ms.fit(PCAembedding_low)
    cluster_centers = ms.cluster_centers_

    n_cluster_centers = len(cluster_centers)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kmms = KMeans(init = cluster_centers, n_clusters = n_cluster_centers)
        #kmms = KMeans(init = 'k-means++', n_clusters = 2, n_init=20, max_iter=600)
        y_hat = kmms.fit_predict(PCAembedding_low)

    if n_cluster_centers > cNum:
        res = y_hat
        unique_predicted_labels = get_unique_numbers(res)
        predicted_labels_count = {}
        for label in unique_predicted_labels:
            predicted_labels_count[label] = (res == label).sum()
        max_item = max(predicted_labels_count, key=predicted_labels_count.get)
        predicted_labels_count = sorted(predicted_labels_count.items(), key=lambda x: x[1], reverse=True)
        map_predict_to_actual = {}
        max_value = cNum-1
        for i in range(len(predicted_labels_count)):
            if i < max_value:
                map_predict_to_actual[predicted_labels_count[i][0]] = i
            else:
                # print(f"{predicted_labels_count[i][0]} mapped to {max_value}")
                map_predict_to_actual[predicted_labels_count[i][0]] = max_value

        # predictions_final contains the final results
        # it takes care of the case when num_class > number of unique labels given
        predictions_final = []
        # print(f"map_predict_to_actual: {map_predict_to_actual}")
        for i in range(len(res)):
            if res[i] in map_predict_to_actual.keys():
                predictions_final.append(map_predict_to_actual[res[i]])
            else:
                predictions_final.append(map_predict_to_actual[max_item])
        # print(predictions_final)
        y_hat = np.array(predictions_final)

    plotly_kmertable = kmerXTableInput
    if method == "PCA":
        plotly_kmertable = preprocessing.normalize(kmerXTableInput)
    plot_div = plotly_dash_show_plot(userId, plotly_kmertable, y_hat, "Unsupervised Kmeans", method, ID=IDs)
    inputData.insert(0, "Labels", y_hat)
        
    return [[inputData], [plot_div]]


# added helper method for semi-supervised labeling
def get_unique_numbers(numbers):

    list_of_unique_numbers = []

    unique_numbers = set(numbers)

    for number in unique_numbers:
        list_of_unique_numbers.append(number)

    return list_of_unique_numbers


# Revised.
def kmeans_semiSupervised(userId, fasta, klength_min, klength_max, rNum, cNum, y_hat, method):
    inputData = read_fasta_sequences(fasta)
    IDs = get_ids_from_fasta(fasta)
    inputData["Sequence"] = inputData["Sequence"].apply(lambda x: x.replace("-", ""))
    kmerXTableInput = kmerXTable(inputData, klength_min, klength_max)

    PCAembedding = PCA(n_components=10)
    NkmerXTableInput = preprocessing.normalize(kmerXTableInput)
    PCAembedding_low = PCAembedding.fit_transform(NkmerXTableInput)

    ms = MeanShift()
    ms.fit(PCAembedding_low)
    cluster_centers = ms.cluster_centers_

    n_cluster_centers = len(cluster_centers)

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kmms = KMeans(init=cluster_centers, n_clusters=n_cluster_centers, random_state=rNum)
        kmms_labels = kmms.fit_predict(PCAembedding_low)

    if n_cluster_centers > cNum:
        res = kmms_labels
        unique_predicted_labels = get_unique_numbers(res)
        predicted_labels_count = {}
        for label in unique_predicted_labels:
            predicted_labels_count[label] = (res == label).sum()
        max_item = max(predicted_labels_count, key=predicted_labels_count.get)
        predicted_labels_count = sorted(predicted_labels_count.items(), key=lambda x: x[1], reverse=True)
        map_predict_to_actual = {}
        max_value = cNum-1
        for i in range(len(predicted_labels_count)):
            if i < max_value:
                map_predict_to_actual[predicted_labels_count[i][0]] = i
            else:
                # print(f"{predicted_labels_count[i][0]} mapped to {max_value}")
                map_predict_to_actual[predicted_labels_count[i][0]] = max_value

        # predictions_final contains the final results
        # it takes care of the case when num_class > number of unique labels given
        predictions_final = []
        # print(f"map_predict_to_actual: {map_predict_to_actual}")
        for i in range(len(res)):
            if res[i] in map_predict_to_actual.keys():
                predictions_final.append(map_predict_to_actual[res[i]])
            else:
                predictions_final.append(map_predict_to_actual[max_item])
        kmms_labels = np.array(predictions_final)

    kmerXTableInput["pLabels"] = kmms_labels
    kmerXTableInput["aLabels"] = actual_labels = y_hat.tolist()
    # Get the counts for the given labels and the predicted labels
    given_labels_count = {}
    labels_list = list(actual_labels)
    unique_given_labels = get_unique_numbers(actual_labels)
    predictions = kmms_labels
    for label in unique_given_labels:
        given_labels_count[label] = labels_list.count(label)
    unique_predicted_labels = get_unique_numbers(predictions)
    predicted_labels_count = {}
    for label in unique_predicted_labels:
        predicted_labels_count[label] = (predictions == label).sum()
    max_item = max(predicted_labels_count, key=predicted_labels_count.get)
    if -1 in given_labels_count.keys():
        del given_labels_count[-1]
    given_labels_count = sorted(given_labels_count.items(), key=lambda x: x[1], reverse=True)
    predicted_labels_count = sorted(predicted_labels_count.items(), key=lambda x: x[1], reverse=True)

    res = np.array(predictions)

    # Map the predicted labels to the given/actual labels
    map_predict_to_actual = {}
    for label_GIVEN_dict_entry in given_labels_count:
        label_GIVEN = label_GIVEN_dict_entry[0]
        predicted_labels_count_GIVEN = {}
        label_GIVEN_idx = [index for (index, item) in enumerate(labels_list) if item == label_GIVEN]
        res_GIVEN = [res[i] for i in label_GIVEN_idx]
        unique_predicted_labels_GIVEN = get_unique_numbers(res_GIVEN)
        for lab in unique_predicted_labels_GIVEN:
            predicted_labels_count_GIVEN[lab] = (res_GIVEN == lab).sum()
        map_predict_to_actual[max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get)] = label_GIVEN
            
    max_value = max(unique_given_labels) + 1
    for upl in unique_predicted_labels:
        if upl not in map_predict_to_actual.keys():
            # print(f"{upl} mapped to {max_value}")
            map_predict_to_actual[upl] = max_value
            max_value += 1
    
    predictions_final = []

    # predictions_final contains the final results
    # it takes care of the case when num_class > number of unique labels given
    for i in range(len(predictions)):
        if actual_labels[i] == -1:
            if predictions[i] in map_predict_to_actual.keys():
                predictions_final.append(map_predict_to_actual[predictions[i]])
            else:
                predictions_final.append(map_predict_to_actual[max_item])
        else:
            predictions_final.append(actual_labels[i])
    
    newLabels = predictions_final

    kmerTable = kmerXTableInput.drop(columns=["pLabels", "aLabels"])
    plotly_kmertable = kmerTable
    plotly_labels = np.array(newLabels)
    if method == "PCA":
        plotly_kmertable = preprocessing.normalize(kmerTable)
    plotly_div = plotly_dash_show_plot(userId, plotly_kmertable, plotly_labels, "Semi-supervised Kmeans", method, ID=IDs)

    inputData.insert(0, "Labels", newLabels)

    return [[inputData], [plotly_div]]