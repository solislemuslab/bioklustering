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
    
def kmeans(userId, fasta, klength_min, klength_max, rNum, cNum, method):
    inputData = read_fasta_sequences(fasta)
    inputData["Sequence"] = inputData["Sequence"].apply(lambda x: x.replace("-", ""))

    kmerXTableInput = kmerXTable(inputData, klength_min, klength_max)
    km = KMeans(random_state = rNum, n_clusters = cNum)
    km.fit(kmerXTableInput) 
    y_hat = km.predict(kmerXTableInput)

    plotly_kmertable = kmerXTableInput
    if method == "PCA":
        plotly_kmertable = preprocessing.normalize(kmerXTableInput)
    plot_div = plotly_dash_show_plot(userId, plotly_kmertable, y_hat, "Unsupervised Kmeans", method)
    inputData.insert(0, "Labels", y_hat)
        
    return [[inputData], [plot_div]]
        
def kmeans_semiSupervised(userId, fasta, klength_min, klength_max, rNum, y_hat, method):
    inputData = read_fasta_sequences(fasta)
    inputData["Sequence"] = inputData["Sequence"].apply(lambda x: x.replace("-", ""))
    kmerXTableInput = kmerXTable(inputData, klength_min, klength_max)

    PCAembedding = PCA(n_components=10)
    NkmerXTableInput = preprocessing.normalize(kmerXTableInput)
    PCAembedding_low = PCAembedding.fit_transform(NkmerXTableInput)
    
    ms = MeanShift()
    ms.fit(PCAembedding_low)
    cluster_centers = ms.cluster_centers_

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        kmms = KMeans(init = cluster_centers, n_clusters = len(cluster_centers))
        kmms_labels = kmms.fit_predict(PCAembedding_low)

    # convert all clusters into two clusters
    kmerXTableInput["pLabels"] = kmms_labels
    kmerXTableInput["aLabels"] = y_hat.tolist()
    newLabels_clusters_1 = kmerXTableInput[kmerXTableInput["aLabels"] == 1]["pLabels"].tolist()
    newLabels_clusters_0 = kmerXTableInput[kmerXTableInput["aLabels"] == 0]["pLabels"].tolist()
    newLabels = []

    for label in kmms_labels:
        if newLabels_clusters_1.count(label) > newLabels_clusters_0.count(label):
            newLabels.append(1)
        else:
            newLabels.append(0)

    kmerTable = kmerXTableInput.drop(columns=["pLabels", "aLabels"])
    plotly_kmertable = kmerTable
    plotly_labels = np.array(newLabels)
    if method == "PCA":
        plotly_kmertable = preprocessing.normalize(kmerTable)
    plotly_div = plotly_dash_show_plot(userId, plotly_kmertable, plotly_labels, "Semi-supervised Kmeans", method)

    inputData.insert(0, "Labels", newLabels)       

    return [[inputData], [plotly_div]]
