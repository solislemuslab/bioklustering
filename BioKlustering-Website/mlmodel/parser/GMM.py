# Copyright 2020 by Zhiwen Xu, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the BioKlustering Website.

# import packages
import numpy as np
import pandas as pd
from Bio import SeqIO, AlignIO
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.mixture import GaussianMixture as GMM
import os
from .helpers import plotly_dash_show_plot, update_parameters
import copy


def parseFasta(data):
    print("data:",data)
    d = {fasta.id: str(fasta.seq) for fasta in SeqIO.parse(data, "fasta")}
    pd.DataFrame([d])
    s = pd.Series(d, name='Sequence')
    s.index.name = 'ID'
    s.reset_index()
    return pd.DataFrame(s)


def get_kmer_table(path, k_min, k_max):
    genes, gene_len, output_df = read_fasta(path)
    count_vect = CountVectorizer(analyzer='char', ngram_range=(k_min, k_max))
    X = count_vect.fit_transform(genes)
    chars = count_vect.get_feature_names()
    kmers = X.toarray()
    kmer_freq = []
    for i in range(len(genes)):
        kmer_freq.append(kmers[i] / gene_len[i])
    input = pd.DataFrame(kmer_freq, columns=chars)
    return input, output_df


def get_gene_sequences(filename):
    genes = []
    with open(filename) as handle:
        for record in SeqIO.parse(handle, "fasta"):
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
        output_df = pd.concat([output_df, virus])
        virus = virus.drop_duplicates(keep="last")
        genes = list(virus['Sequence'])
        genes_seq = get_gene_sequences(path)
        gene_len = get_gene_len(genes_seq)
        all_genes = all_genes + genes_seq
        all_gene_len = all_gene_len + gene_len
    return all_genes, all_gene_len, output_df


def get_predictions(userId, path, k_min, k_max, num_class, cov_type, seed, method):
    kmer_table, output_df = get_kmer_table(path, k_min, k_max)
    gmm = GMM(n_components=num_class, covariance_type=cov_type, random_state=seed).fit(kmer_table)
    predictions = gmm.predict(kmer_table)
    plot_div = plotly_dash_show_plot(userId, kmer_table, predictions, "Unsupervised Gaussian Mixture Model", method)
    output_df.insert(0, "Labels", predictions)
    return [[output_df], [plot_div]]


# original
def get_predictions_semi_original(path, k_min, k_max, num_class, cov_type, seed, labels):
    kmer_table, output_df = get_kmer_table(path, k_min, k_max)
    finalDf = pd.concat([kmer_table, pd.Series(labels)], axis=1)
    gmm = GMM(n_components=num_class, covariance_type=cov_type, random_state=seed)
    gmm.means_init = np.array([kmer_table[finalDf.Labels == i].mean(axis=0) for i in range(num_class)])
    gmm.fit(kmer_table)
    predictions = gmm.predict(kmer_table)
    return predictions



# modified for website
def get_predictions_semi(userId, path, k_min, k_max, num_class, cov_type, seed, labels, method):
    targets = []
    unique_given_labels = get_unique_numbers(labels)
    if num_class < len(unique_given_labels) - 1 and -1 in unique_given_labels:
        num_class = len(unique_given_labels) - 1
    if num_class < len(unique_given_labels) and -1 not in unique_given_labels:
        num_class = len(unique_given_labels)
    kmer_table, output_df = get_kmer_table(path, k_min, k_max)

    finalDf = pd.concat([kmer_table, labels], axis=1)
    gmm = GMM(n_components=num_class, covariance_type=cov_type, random_state=seed)
    for i in range(num_class):
        if i in list(finalDf.Labels):
            targets.append(i)
    if len(targets) == num_class:
        gmm.means_init = np.array([kmer_table[finalDf.Labels == i].mean(axis=0) for i in targets])
    gmm.fit(kmer_table)
    predictions = gmm.predict(kmer_table)

    # Get the counts for the given labels and the predicted labels
    given_labels_count = {}
    labels_list = list(labels)
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
    unselected_given = copy.deepcopy(unique_given_labels)
    if -1 in unselected_given:
        unselected_given.remove(-1)
    unselected_pred = copy.deepcopy(unique_predicted_labels)
    map_predict_to_actual = {}
    for label_GIVEN_dict_entry in given_labels_count:
        label_GIVEN = label_GIVEN_dict_entry[0]
        predicted_labels_count_GIVEN = {}
        label_GIVEN_idx = [index for (index, item) in enumerate(labels_list) if item == label_GIVEN]
        res_GIVEN = [res[i] for i in label_GIVEN_idx]
        unique_predicted_labels_GIVEN = list(set(get_unique_numbers(res_GIVEN)) & set(unselected_pred))
        if len(unique_predicted_labels_GIVEN) == 0:
            continue
        for lab in unique_predicted_labels_GIVEN:
            predicted_labels_count_GIVEN[lab] = (res_GIVEN == lab).sum()
        map_predict_to_actual[max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get)] = label_GIVEN
        unselected_given.remove(label_GIVEN)
        to_rem = max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get)
        unselected_pred.remove(to_rem)

    if len(unique_given_labels) < num_class:
        max_value = max(unique_given_labels) + 1
        for upl in unique_predicted_labels:
            if upl not in map_predict_to_actual.keys():
                print(f"{upl} mapped to {max_value}")
                map_predict_to_actual[upl] = max_value
                max_value += 1
                unselected_pred.remove(upl)

    
    
    print(f"map_predict_to_actual: {map_predict_to_actual}")
    predictions_final = []

    # predictions_final contains the final results
    # it takes care of the case when num_class > number of unique labels given
    for i in range(len(predictions)):
        if labels[i] == -1:
            if predictions[i] in map_predict_to_actual.keys():
                predictions_final.append(map_predict_to_actual[predictions[i]])
            else:
                predictions_final.append(map_predict_to_actual[max_item])
        else:
            print("predicted label ", predictions[i], " mapped to true label ", labels[i], " at index ", i)
            predictions_final.append(labels[i])

    predictions = np.array(predictions_final)
    plot_div = plotly_dash_show_plot(userId, kmer_table, predictions, "Semi-supervised Gaussian Mixture Model", method)
    output_df.insert(0, "Labels", predictions)
    # update parameters for predictInfo object (i.e. for front end)
    acc = cal_accuracy(labels, predictions_final)
    update_parameters(userId, {"accuracy": acc})
    return [[output_df], [plot_div]]


def get_unique_numbers(numbers):
    list_of_unique_numbers = []

    unique_numbers = set(numbers)

    for number in unique_numbers:
        list_of_unique_numbers.append(number)

    return list_of_unique_numbers


def cal_accuracy(labels, predictions):
    err = 0
    total_len = len(labels)
    for i in range(len(labels)):
        if labels[i] == -1:
            total_len = total_len - 1
            continue
        if labels[i] != predictions[i]:
            err += 1

    return 1 - err / total_len


def model_selection(userId, path, labels, num_class, seed, method):
    best_accu = 0
    best_prediction = []
    cov_type = ['full', 'diag', 'tied', 'spherical']
    k_min = [2, 3, 4]
    k_max = [2, 3, 4, 5]
    for cov in cov_type:
        for k1 in k_min:
            for k2 in k_max:
                if k2 >= k1:
                    prediction = get_predictions_semi_original(path, k1, k2, num_class, cov, 0, labels)
                    accu = cal_accuracy(labels, prediction)
                    if accu > best_accu:
                        best_accu = accu
                        best_kmin = k1
                        best_kmax = k2
                        best_cov = cov
                        best_prediction = prediction

    # update parameters for predictInfo object (i.e. for front end)
    new_params = {
        'k_min': best_kmin,
        'k_max': best_kmax,
        'cov_type': best_cov,
        'accuracy': best_accu
    }
    update_parameters(userId, new_params)
    return get_predictions_semi(userId, path, best_kmin, best_kmax, num_class, best_cov, seed, labels, method)
    # return best_kmin,best_kmax,best_cov,best_prediction
