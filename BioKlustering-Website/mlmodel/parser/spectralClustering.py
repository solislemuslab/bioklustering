# Copyright 2020 by LiuLe Yang, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the BioKlustering Website.

import os
import numpy as np
import pandas as pd
from Bio import SeqIO
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import SpectralClustering
from .helpers import plotly_dash_show_plot, update_parameters
import copy


# parseFasta(data) credit to Luke
def parseFasta(data):
    d = {fasta.id: str(fasta.seq) for fasta in SeqIO.parse(data, "fasta")}
    pd.DataFrame([d])
    s = pd.Series(d, name='Sequence')
    s.index.name = 'ID'
    s.reset_index()
    return pd.DataFrame(s)

def get_ids_from_fasta(sequence_paths):
    retval = []
    for path in sequence_paths:
        path = os.path.join("media", path)
        d = {fasta.id : str(fasta.seq) for fasta in SeqIO.parse(path, "fasta")}
        retval = np.concatenate((np.array(retval), np.array(list(d.keys()))))
    return retval

# this method credit to Zhiwen
def get_kmer_table(paths, k_min, k_max):
    genes, gene_len, output_df = read_fasta(paths)
    count_vect = CountVectorizer(analyzer='char', ngram_range=(k_min, k_max))
    X = count_vect.fit_transform(genes)
    chars = count_vect.get_feature_names()
    kmers = X.toarray()
    kmer_freq = []
    for i in range(len(genes)):
        kmer_freq.append(kmers[i] / gene_len[i])
    input = pd.DataFrame(kmer_freq, columns=chars)
    return input, output_df


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
        output_df = pd.concat([output_df, virus])
        virus = virus.drop_duplicates(keep="last")
        genes_seq = get_gene_sequences(path)
        gene_len = get_gene_len(genes_seq)
        all_genes = all_genes + genes_seq
        all_gene_len = all_gene_len + gene_len
    return all_genes, all_gene_len, output_df


# this method is modified for website
# this method takes predits the input and make prediction using spectral clustering
# paths: a list of strings. contains file paths
# k_min: int. min of kmer
# k_max: int. max of kmer
# num_cluster: int. number of clusters
# assignLabels: a string. the way to assign label at the final stage of spectral clustering. Can be "kmeans" or "discretize"
def spectral_clustering(userId, paths, k_min, k_max, num_cluster, assignLabels, method, seed):
    kmer_table, output_df = get_kmer_table(paths, k_min, k_max)
    IDs = get_ids_from_fasta(paths)
    # if len(kmer_table) < num_cluster:
    #     raise ValueError()
    spectral_clustering = SpectralClustering(n_clusters=num_cluster, assign_labels=assignLabels, random_state=seed)
    labels = spectral_clustering.fit_predict(kmer_table)
    plot_div = plotly_dash_show_plot(userId, kmer_table, labels, "Unsupervised Spectral Clustering", method, ID=IDs)
    output_df.insert(0, "Labels", labels)
    return [[output_df], [plot_div]]


def intuitive_semi_supervised(userId, file_path, inputlabels, k_min, k_max, num_cluster, assignLabels, seed, method):
    label_list = inputlabels.to_list()
    IDs = get_ids_from_fasta(file_path)
    unique_given_labels = get_unique_numbers(label_list)
    if num_cluster < len(unique_given_labels) - 1 and -1 in unique_given_labels:
        num_cluster = len(unique_given_labels) - 1
    if num_cluster < len(unique_given_labels) and -1 not in unique_given_labels:
        num_cluster = len(unique_given_labels)
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
    if assignLabels == "none":
        for i in range(k_min, k_max + 1):
            for j in range(i, k_max + 1):
                temp_k_min = i
                temp_k_max = j
                kmer_table, output_df = get_kmer_table(file_path, temp_k_min, temp_k_max)
                spectral_clustering = SpectralClustering(n_clusters=num_cluster, assign_labels="kmeans",
                                                         random_state=seed)
                labels = spectral_clustering.fit_predict(kmer_table)

                given_labels_count = {}
                labels_list = list(inputlabels)
                for label in unique_given_labels:
                    given_labels_count[label] = labels_list.count(label)
                unique_predicted_labels = get_unique_numbers(labels)
                predicted_labels_count = {}
                for label in unique_predicted_labels:
                    predicted_labels_count[label] = (labels == label).sum()
                max_item = max(predicted_labels_count, key=predicted_labels_count.get)
                if -1 in given_labels_count.keys():
                    del given_labels_count[-1]
                given_labels_count = sorted(given_labels_count.items(), key=lambda x: x[1], reverse=True)
                predicted_labels_count = sorted(predicted_labels_count.items(), key=lambda x: x[1], reverse=True)

                unselected_given = copy.deepcopy(unique_given_labels)
                if -1 in unselected_given:
                    unselected_given.remove(-1)
                unselected_pred = copy.deepcopy(unique_predicted_labels)
                map_predict_to_actual = {}
                for label_GIVEN_dict_entry in given_labels_count:
                    label_GIVEN = label_GIVEN_dict_entry[0]
                    predicted_labels_count_GIVEN = {}
                    label_GIVEN_idx = [index for (index, item) in enumerate(labels_list) if item == label_GIVEN]
                    res_GIVEN = [labels[k] for k in label_GIVEN_idx]
                    #print(res_GIVEN)
                    unique_predicted_labels_GIVEN = list(set(get_unique_numbers(res_GIVEN)) & set(unselected_pred))
                    if len(unique_predicted_labels_GIVEN) == 0:
                        continue
                    for lab in unique_predicted_labels_GIVEN:
                        predicted_labels_count_GIVEN[lab] = (res_GIVEN == lab).sum()
                    map_predict_to_actual[max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get)] = label_GIVEN
                    unselected_given.remove(label_GIVEN)
                    unselected_pred.remove(max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get))


                if len(unique_given_labels) <= num_cluster:
                    max_value = max(unique_given_labels) + 1
                    for upl in unique_predicted_labels:
                        if upl not in map_predict_to_actual.keys():
                            map_predict_to_actual[upl] = max_value
                            max_value += 1
                            unselected_pred.remove(upl)
                
                for l in range(len(unselected_given)):
                    map_predict_to_actual[unselected_pred[l]] = unselected_given[l]
                    

                # predictions_final contains the final results
                # it takes care of the case when num_class > number of unique labels given
                predictions_tmp = []
                for k in range(len(labels)):
                    if labels[k] in map_predict_to_actual.keys():
                        predictions_tmp.append(map_predict_to_actual[labels[k]])
                    else:
                        predictions_tmp.append(map_predict_to_actual[max_item])

                correct_count = 0
                for k in range(len(label_list)):
                    if label_list[k] != unknown_label:
                        if label_list[k] == predictions_tmp[k]:
                            correct_count += 1
                temp_accuracy = correct_count / total_labeled
                if temp_accuracy > optimal_accuracy:
                    optimal_accuracy = temp_accuracy
                    optimal_k_min = i
                    optimal_k_max = j
                    res = labels
        for i in range(k_min, k_max + 1):
            for j in range(i, k_max + 1):
                temp_k_min = i
                temp_k_max = j
                kmer_table, output_df = get_kmer_table(file_path, temp_k_min, temp_k_max)
                spectral_clustering = SpectralClustering(n_clusters=num_cluster, assign_labels="discretize",
                                                         random_state=seed)
                labels = spectral_clustering.fit_predict(kmer_table)

                given_labels_count = {}
                labels_list = list(inputlabels)
                for label in unique_given_labels:
                    given_labels_count[label] = labels_list.count(label)
                unique_predicted_labels = get_unique_numbers(labels)
                predicted_labels_count = {}
                for label in unique_predicted_labels:
                    predicted_labels_count[label] = (labels == label).sum()
                max_item = max(predicted_labels_count, key=predicted_labels_count.get)
                if -1 in given_labels_count.keys():
                    del given_labels_count[-1]
                given_labels_count = sorted(given_labels_count.items(), key=lambda x: x[1], reverse=True)
                predicted_labels_count = sorted(predicted_labels_count.items(), key=lambda x: x[1], reverse=True)

                unselected_given = copy.deepcopy(unique_given_labels)
                if -1 in unselected_given:
                    unselected_given.remove(-1)
                unselected_pred = copy.deepcopy(unique_predicted_labels)

                map_predict_to_actual = {}
                for label_GIVEN_dict_entry in given_labels_count:
                    label_GIVEN = label_GIVEN_dict_entry[0]
                    predicted_labels_count_GIVEN = {}
                    label_GIVEN_idx = [index for (index, item) in enumerate(labels_list) if item == label_GIVEN]
                    res_GIVEN = [labels[k] for k in label_GIVEN_idx]
                    unique_predicted_labels_GIVEN = list(set(get_unique_numbers(res_GIVEN)) & set(unselected_pred))
                    if len(unique_predicted_labels_GIVEN) == 0:
                        continue
                    for lab in unique_predicted_labels_GIVEN:
                        predicted_labels_count_GIVEN[lab] = (res_GIVEN == lab).sum()
                    map_predict_to_actual[max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get)] = label_GIVEN
                    unselected_given.remove(label_GIVEN)
                    unselected_pred.remove(max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get))


                if len(unique_given_labels) <= num_cluster:
                    max_value = max(unique_given_labels) + 1
                    for upl in unique_predicted_labels:
                        if upl not in map_predict_to_actual.keys():
                            # print(f"{upl} mapped to {max_value}")
                            map_predict_to_actual[upl] = max_value
                            max_value += 1
                            unselected_pred.remove(upl)
                
                for l in range(len(unselected_given)):
                    map_predict_to_actual[unselected_pred[l]] = unselected_given[l]

                # predictions_final contains the final results
                # it takes care of the case when num_class > number of unique labels given
                predictions_tmp = []
                for k in range(len(labels)):
                    if labels[k] in map_predict_to_actual.keys():
                        predictions_tmp.append(map_predict_to_actual[labels[k]])
                    else:
                        predictions_tmp.append(map_predict_to_actual[max_item])

                correct_count = 0
                for k in range(len(label_list)):
                    if label_list[k] != unknown_label:
                        if label_list[k] == predictions_tmp[k]:
                            correct_count += 1
                temp_accuracy = correct_count / total_labeled
                if temp_accuracy > optimal_accuracy:
                    optimal_accuracy = temp_accuracy
                    optimal_k_min = i
                    optimal_k_max = j
                    res = labels
        # update parameters for front end
        new_params = {
            'accuracy': optimal_accuracy,
            'k_min': optimal_k_min,
            'k_max': optimal_k_max
        }
        update_parameters(userId, new_params)
    else:
        for i in range(k_min, k_max + 1):
            for j in range(i, k_max + 1):
                temp_k_min = i
                temp_k_max = j
                kmer_table, output_df = get_kmer_table(file_path, temp_k_min, temp_k_max)
                spectral_clustering = SpectralClustering(n_clusters=num_cluster, assign_labels=assignLabels,
                                                         random_state=seed)
                labels = spectral_clustering.fit_predict(kmer_table)

                # Get the counts for the given labels and the predicted labels
                given_labels_count = {}
                labels_list = list(inputlabels)
                for label in unique_given_labels:
                    given_labels_count[label] = labels_list.count(label)
                unique_predicted_labels = get_unique_numbers(labels)
                predicted_labels_count = {}
                for label in unique_predicted_labels:
                    predicted_labels_count[label] = (labels == label).sum()
                max_item = max(predicted_labels_count, key=predicted_labels_count.get)
                if -1 in given_labels_count.keys():
                    del given_labels_count[-1]
                given_labels_count = sorted(given_labels_count.items(), key=lambda x: x[1], reverse=True)
                predicted_labels_count = sorted(predicted_labels_count.items(), key=lambda x: x[1], reverse=True)

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
                    res_GIVEN = [labels[k] for k in label_GIVEN_idx]
                    unique_predicted_labels_GIVEN = list(set(get_unique_numbers(res_GIVEN)) & set(unselected_pred))
                    if len(unique_predicted_labels_GIVEN) == 0:
                        continue
                    for lab in unique_predicted_labels_GIVEN:
                        predicted_labels_count_GIVEN[lab] = (res_GIVEN == lab).sum()
                    map_predict_to_actual[max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get)] = label_GIVEN
                    unselected_given.remove(label_GIVEN)
                    unselected_pred.remove(max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get))


                if len(unique_given_labels) <= num_cluster:
                    max_value = max(unique_given_labels) + 1
                    for upl in unique_predicted_labels:
                        if upl not in map_predict_to_actual.keys():
                            # print(f"{upl} mapped to {max_value}")
                            map_predict_to_actual[upl] = max_value
                            max_value += 1
                            unselected_pred.remove(upl)
            
                for l in range(len(unselected_given)):
                    map_predict_to_actual[unselected_pred[l]] = unselected_given[l]

                # predictions_final contains the final results
                # it takes care of the case when num_class > number of unique labels given
                predictions_tmp = []
                for k in range(len(labels)):
                    if labels[k] in map_predict_to_actual.keys():
                        predictions_tmp.append(map_predict_to_actual[labels[k]])
                    else:
                        predictions_tmp.append(map_predict_to_actual[max_item])

                correct_count = 0
                temp_accuracy = 0
                for k in range(len(label_list)):
                    if label_list[k] != unknown_label:
                        if label_list[k] == predictions_tmp[k]:
                            correct_count += 1
                temp_accuracy = correct_count / total_labeled
                if temp_accuracy > optimal_accuracy:
                    optimal_accuracy = temp_accuracy
                    optimal_k_min = i
                    optimal_k_max = j
                    res = labels
        # update parameters for front end
        new_params = {
            'accuracy': optimal_accuracy,
            'k_min': optimal_k_min,
            'k_max': optimal_k_max
        }
        update_parameters(userId, new_params)

    res = np.array(res)
    inputlabels = inputlabels.to_list()

    # Get the counts for the given labels and the predicted labels
    given_labels_count = {}
    labels_list = list(inputlabels)
    for label in unique_given_labels:
        given_labels_count[label] = labels_list.count(label)
    unique_predicted_labels = get_unique_numbers(res)
    predicted_labels_count = {}
    for label in unique_predicted_labels:
        predicted_labels_count[label] = (res == label).sum()
    max_item = max(predicted_labels_count, key=predicted_labels_count.get)
    if -1 in given_labels_count.keys():
        del given_labels_count[-1]
    given_labels_count = sorted(given_labels_count.items(), key=lambda x: x[1], reverse=True)
    predicted_labels_count = sorted(predicted_labels_count.items(), key=lambda x: x[1], reverse=True)

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
        res_GIVEN = [res[k] for k in label_GIVEN_idx]
        unique_predicted_labels_GIVEN = list(set(get_unique_numbers(res_GIVEN)) & set(unselected_pred))
        if len(unique_predicted_labels_GIVEN) == 0:
            continue
        for lab in unique_predicted_labels_GIVEN:
            predicted_labels_count_GIVEN[lab] = (res_GIVEN == lab).sum()
        map_predict_to_actual[max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get)] = label_GIVEN
        unselected_given.remove(label_GIVEN)
        unselected_pred.remove(max(predicted_labels_count_GIVEN, key=predicted_labels_count_GIVEN.get))


    if len(unique_given_labels) <= num_cluster:
        max_value = max(unique_given_labels) + 1
        for upl in unique_predicted_labels:
            if upl not in map_predict_to_actual.keys():
                # print(f"{upl} mapped to {max_value}")
                map_predict_to_actual[upl] = max_value
                max_value += 1
                unselected_pred.remove(upl)
    
    if len(unselected_given) != len(unselected_pred):
        print("error: num unselected given =",len(unselected_given), "!= unselected pred =",len(unselected_pred))
    
    #for l in range(len(unselected_given)):
    #    map_predict_to_actual[unselected_pred[l]] = unselected_given[l]
    
    
    # print(f"map_predict_to_actual: {map_predict_to_actual}")


    # predictions_final contains the final results
    # it takes care of the case when num_class > number of unique labels given
    predictions_final = []
    predictions_tmp = []
    for i in range(len(res)):
        if inputlabels[i] == -1:
            if res[i] in map_predict_to_actual.keys():
                predictions_final.append(map_predict_to_actual[res[i]])
            else:
                predictions_final.append(map_predict_to_actual[max_item])
        else:
            predictions_final.append(inputlabels[i])
        if res[i] in map_predict_to_actual.keys():
            predictions_tmp.append(map_predict_to_actual[res[i]])
        else:
            predictions_tmp.append(map_predict_to_actual[max_item])
    res = np.array(predictions_final) 

    plot_div = plotly_dash_show_plot(userId, kmer_table, res, "Semi-supervised Spectral Clustering", method, ID=IDs)
    output_df.insert(0, "Labels", res)
    return [[output_df], [plot_div]]


def get_unique_numbers(numbers):
    list_of_unique_numbers = []

    unique_numbers = set(numbers)

    for number in unique_numbers:
        list_of_unique_numbers.append(number)

    return list_of_unique_numbers
