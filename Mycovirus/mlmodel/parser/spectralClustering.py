# import packages
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

# parseFasta(data) credit to Luke
def parseFasta(data):
    d = {fasta.id : str(fasta.seq) for fasta in SeqIO.parse(data, "fasta")}
    pd.DataFrame([d])
    s = pd.Series(d, name='Sequence')
    s.index.name = 'ID'
    s.reset_index()
    return pd.DataFrame(s)

# this method credit to Zhiwen
def get_kmer_table(paths,k_min,k_max):
    genes,gene_len, output_df = read_fasta(paths)
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
def read_fasta(paths):
    all_genes = []
    all_gene_len = []
    output_df = pd.DataFrame()
    
    for path in paths:
        path = os.path.join('media', path)
        virus = parseFasta(path)
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
    kmer_table, output_df = get_kmer_table(paths, k_min, k_max)
    spectral_clustering = SpectralClustering(n_clusters= num_cluster, assign_labels = assignLabels, random_state = 0)
    labels = spectral_clustering.fit_predict(kmer_table)

    from django.shortcuts import render
    from plotly.offline import plot
    from plotly.graph_objs import Scatter
    import plotly.express as px

    # plotly dash
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(kmer_table)
    d = {'x':pca_result[:,0], 'y':pca_result[:,1], 'label':labels}
    d['label'] = d['label'].astype(str)
    df = pd.DataFrame(d)
    fig = px.scatter(df, x='x', y='y', 
        title="Spectral Clustering",
        labels=dict(x="Principal component 1", y="Principal component 2", label="Label"), 
        color='label')
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    fig.write_image(os.path.join('media', 'images', 'plotly.png'))
    output_df.insert(0, "Labels", labels)
    return [[output_df], [plot_div]]
    
    # # make an image (will separate this process later)
    # pca = PCA(n_components=2)
    # pca_result = pca.fit_transform(kmer_table)
    # d = {'dimension1':pca_result[:,0], 'dimension2':pca_result[:,1], 'label':labels}
    # df = pd.DataFrame(d)
    # for i in range(num_cluster):
    #     label = df.loc[df['label'] == i]
    #     color = 'C'+str(i)
    #     plt.scatter(label['dimension1'].tolist(),label['dimension2'].tolist(), c = color )
    # plt.xlabel('principal component 1')
    # plt.ylabel('principal component 2')
    # plt.title('Spectral clustring')
    # path = os.path.join('media', 'images', 'spectral Clustring' + str(i) + '.png')
    # plt.savefig(path, bbox_inches='tight')
    # plt.close()
    # output_df.insert(0, "Labels", labels)
    # return [[output_df], [path]]

# this method takes prints the spectral clustering result by using PCA
# paths: a list of strings. contains file paths
# k_min: int. min of kmer
# k_max: int. max of kmer
# num_cluster: int. number of clusters
# assignLabels: a string. the way to assign label at the final stage of spectral clustering. Can be "kmeans" or "discretize"
def PCA_show_spectural_clustering(paths, k_min, k_max, num_cluster, assignLabels):
    kmer_table = get_kmer_table(paths, k_min, k_max)
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

