
# import packages
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pandas import Series, DataFrame
import Bio
from Bio import SeqIO,AlignIO
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.mixture import GaussianMixture as GMM

import os

# methods

# parseFasta(data) credit to Luke
def parseFasta(data):
    d = {fasta.id : str(fasta.seq) for fasta in SeqIO.parse(data, "fasta")}
    pd.DataFrame([d])
    s = pd.Series(d, name='Sequence')
    s.index.name = 'ID'
    s.reset_index()
    return pd.DataFrame(s)

def get_kmer_table(paths,k_min,k_max):
    genes,gene_len,output_df = read_fasta(paths)
    count_vect = CountVectorizer(analyzer='char', ngram_range=(k_min, k_max))
    X = count_vect.fit_transform(genes)
    chars = count_vect.get_feature_names()
    kmers = X.toarray()
    kmer_freq = []
    for i in range(len(genes)):
        kmer_freq.append(kmers[i] / gene_len[i])
    input = pd.DataFrame(kmer_freq, columns=chars)
    return input,output_df

def get_gene_sequences(filename):
    genes = []
    for record in SeqIO.parse(filename, "fasta"):
        genes.append(str(record.seq))
    return genes

# genes: a list of gene sequences, which can directly be generated from get_gene_sequences().
def get_gene_len(genes):
    gene_len = []

    for i in range(len(genes)):
        gene_len.append(len(genes[i]))
    return gene_len

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

def get_predictions(paths,k_min,k_max,num_class,cov_type):
    kmer_table,output_df = get_kmer_table(paths, k_min, k_max)
    gmm = GMM(n_components=num_class,covariance_type=cov_type).fit(kmer_table)
    labels = gmm.predict(kmer_table)
    output_df.insert(0, "Labels", labels)
    return [[output_df], []]

# change the following parameters to user inputs
# paths = ["label0.fasta","label1.fasta"]
# k_min = 2
# k_max = 3
# num_class = 2
# cov_type = 'full'
# predictions = get_predictions(paths,k_min,k_max,num_class,cov_type)