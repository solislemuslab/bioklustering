# Copyright 2020 by Luke Selberg, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the Mycovirus Website.
from itertools import product
from Bio import SeqIO
import pandas as pd
import numpy as np

#function to read in fasta files
def readFasta(file):
    # read in sequence and id separately
    fasta_sequences = SeqIO.parse(file,'fasta')
    df_1 = pd.DataFrame(fasta_sequences)

    df_1["ID"] = [fasta.id for fasta in SeqIO.parse(file, "fasta")]

    # place id column at front of dataframe
    cols = list(df_1.columns)
    cols = [cols[-1]] + cols[:-1]
    df_1 = df_1[cols]
    df_1.set_index('ID', inplace = True)
    
    return df_1

def possibleKMERS(n):
    return [p for p in product(["A","G","T","C"], repeat = n)]

def kmerCounter(test,n):
    pk = possibleKMERS(n)

    zeros = np.zeros((len(test),len(pk)))

    for row in range(0, len(test)):
        for column in range(0, len(test.iloc[0])-n+1):
            if test.iloc[row].iloc[column] is None:
                break
            zeroIndex = 0
            for kmer in pk:
                if (kmer == tuple(test.iloc[row].iloc[column:column+n])):
                    zeros[row][zeroIndex] += 1
                    break
                zeroIndex += 1
            
    return pd.DataFrame(columns=pk, index=test.index, data = zeros)

def frequencyMaker(count, total):
    return count/total

def kmerCountToFrequency(test):
    df = pd.DataFrame()
    testTotal = test.total
    for row in range(0, len(test)):
        df = df.append(test.iloc[row].apply(frequencyMaker, args=(test.iloc[row].total,)))
    df.total = testTotal
    return df