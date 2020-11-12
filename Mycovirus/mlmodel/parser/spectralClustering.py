# Copyright 2020 by LiuLe Yang, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the Mycovirus Website.
import os
import numpy as np
import pandas as pd
from hmmlearn import hmm
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
plt.switch_backend('Agg')
from sklearn import cluster, datasets, mixture
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import cluster, datasets, mixture
from sklearn.decomposition import PCA
from sklearn.neighbors import kneighbors_graph
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import SpectralClustering
from .showPlotlyDash import plotly_dash_show_plot

# parseFasta(data) credit to Luke
def parseFasta(data):
    d = {fasta.id : str(fasta.seq) for fasta in SeqIO.parse(data, "fasta")}
    pd.DataFrame([d])
    s = pd.Series(d, name='Sequence')
    s.index.name = 'ID'
    s.reset_index()
    return pd.DataFrame(s)

# this method credit to Zhiwen
def get_kmer_table(paths,k_min,k_max,supervisedType):
    genes,gene_len, output_df = read_fasta(paths,supervisedType)
    count_vect = CountVectorizer(analyzer='char', ngram_range=(k_min, k_max))
    X = count_vect.fit_transform(genes)
    chars = count_vect.get_feature_names()
    kmers = X.toarray()
    kmer_freq = []
    for i in range(len(genes)):
        kmer_freq.append(kmers[i] / gene_len[i])
    input = pd.DataFrame(kmer_freq, columns=chars)
    return input,output_df

# this method credit to Zhiwen
def get_gene_sequences(filename):
    genes = []
    for record in SeqIO.parse(filename, "fasta"):
        genes.append(str(record.seq))
    return genes

# this method credit to Zhiwen
# genes: a list of gene sequences, which can directly be generated from get_gene_sequences().
def get_gene_len(genes):
    gene_len = []

    for i in range(len(genes)):
        gene_len.append(len(genes[i]))
    return gene_len

# this method credit to Zhiwen
def read_fasta(paths, supervisedType):
    all_genes = []
    all_gene_len = []
    output_df = pd.DataFrame()
    
    for path in paths:
        path = os.path.join('media', path)
        virus = parseFasta(path)
        if(supervisedType == "unsupervised"):
            virus = virus.drop_duplicates(keep="last")
        output_df = pd.concat([output_df, virus])
        genes = list(virus['Sequence'])
        genes_seq = get_gene_sequences(path)
        gene_len = get_gene_len(genes_seq)
        all_genes = all_genes + genes_seq
        all_gene_len = all_gene_len + gene_len
    return all_genes,all_gene_len,output_df

# this method takes predits the input and make prediction using spectral clustering
# paths: a list of strings. contains file paths
# k_min: int. min of kmer
# k_max: int. max of kmer
# num_cluster: int. number of clusters
# assignLabels: a string. the way to assign label at the final stage of spectral clustering. Can be "kmeans" or "discretize"
def spectral_clustering(paths, k_min, k_max, num_cluster, assignLabels):
    kmer_table, output_df = get_kmer_table(paths, k_min, k_max, "unsupervised")
    spectral_clustering = SpectralClustering(n_clusters= num_cluster, assign_labels = assignLabels, random_state = 0)
    labels = spectral_clustering.fit_predict(kmer_table)
    plot_div = plotly_dash_show_plot(kmer_table, labels)
    output_df.insert(0, "Labels", labels)
    return [[output_df], [plot_div]]

# this method takes prints the spectral clustering result by using PCA
# paths: a list of strings. contains file paths
# k_min: int. min of kmer
# k_max: int. max of kmer
# num_cluster: int. number of clusters
# assignLabels: a string. the way to assign label at the final stage of spectral clustering. Can be "kmeans" or "discretize"
def PCA_show_spectural_clustering(paths, k_min, k_max, num_cluster, assignLabels):
    kmer_table = get_kmer_table(paths, k_min, k_max, "unsupervised")
    prediction = SpectralClustering(n_clusters = num_cluster, assign_labels=assignLabels, random_state=0).fit_predict(kmer_table)
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(kmer_table)
    d = {'dimension1':pca_result[:,0], 'dimension2':pca_result[:,1], 'label':prediction}
    df = pd.DataFrame(d)
    for i in range(num_cluster):
        label = df.loc[df['label'] == i]
        color = 'C'+str(i)
        plt.scatter(label['dimension1'].tolist(),label['dimension2'].tolist(), c = color )
    plt.xlabel('principal component 1')
    plt.ylabel('principal component 2')
    plt.title('Spectral Clustering')

def intuitive_semi_supervised(file_path, label_path, k_min, k_max, num_cluster, assignLabels):
    labels = pd.read_csv(label_path)
    label_list = labels["Labels"].to_list()
    total_len = len(label_list)
    unknown_label = -1
    total_labeled = 0
    optimal_accuracy = 0
    optimal_k_min = 0
    optimal_k_max = 0
    kmer_table = pd.DataFrame(data={})
    output_df = pd.DataFrame(data={})
    for i in label_list:
        if label_list[i] != unknown_label:
            total_labeled = total_labeled + 1
    res = [0] * total_len
    for i in range(k_min, k_max + 1):
        for j in range(i, k_max + 1):
            temp_k_min = i
            temp_k_max = j
            kmer_table, output_df = get_kmer_table(file_path, temp_k_min, temp_k_max, "semisupervised")
            spectral_clustering = SpectralClustering(n_clusters=num_cluster, assign_labels=assignLabels,
                                                     random_state=699)
            labels = spectral_clustering.fit_predict(kmer_table)
            correct_count = 0
            temp_accuracy = 0
            for k in range(len(label_list)):
                if (label_list[k] != unknown_label):
                    if (label_list[k] == labels[k]):
                        correct_count += 1
            temp_accuracy = correct_count / total_labeled
            if (temp_accuracy > optimal_accuracy):
                optimal_accuracy = temp_accuracy
                optimal_k_min = i
                optimal_k_max = j
                res = labels
    print("The optimal accuracy based on labeled sequences is: " + str(optimal_accuracy))
    print("The optimal k_min is: " + str(optimal_k_min))
    print("The optimal k_max is: " + str(optimal_k_max))
    plot_div = plotly_dash_show_plot(kmer_table, res)
    output_df.insert(0, "Labels", res)
    return [[output_df], [plot_div]]

def PCA_show_semi_spectural_clustering(file_path, label_path, k_min, k_max, num_cluster, assignLabels):
    prediction = intuitive_semi_supervised(file_path, label_path, k_min, k_max, num_cluster, assignLabels)
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(kmer_table)
    d = {'dimension1': pca_result[:, 0], 'dimension2': pca_result[:, 1], 'label': prediction}
    df = pd.DataFrame(d)
    for i in range(num_cluster):
        label = df.loc[df['label'] == i]
        color = 'C' + str(i)
        plt.scatter(label['dimension1'].tolist(), label['dimension2'].tolist(), c=color)
    plt.xlabel('principal component 1')
    plt.ylabel('principal component 2')
    plt.title('Semi-supervised Spectral clustring with ' + assignLabels)




