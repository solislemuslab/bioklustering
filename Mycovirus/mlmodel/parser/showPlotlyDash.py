# Copyright 2020 by Chunrong Huang, Solis-Lemus Lab, WID.
# All rights reserved.
# This file is part of the Mycovirus Website.
import os
import pandas as pd
import plotly.express as px
from sklearn.decomposition import PCA
from django.shortcuts import render
from plotly.offline import plot
from plotly.graph_objs import Scatter

# show the prediction in plotly dashboard which allows
# interactive functionalities
# kmer_table: kmer table
# label: cluster label in ndarray
def plotly_dash_show_plot(kmer_table, labels):
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(kmer_table)
    dots = {'x':pca_result[:,0], 'y':pca_result[:,1], 'label':labels}
    dots['label'] = dots['label'].astype(str)
    df = pd.DataFrame(dots)
    fig = px.scatter(df, x='x', y='y', 
        title="Spectral Clustering",
        labels=dict(x="Principal component 1", y="Principal component 2", label="Label"), 
        color='label')
    # plotly dashboard in html 
    plot_div = plot(fig, output_type='div', include_plotlyjs=False)
    # save the static plot into media
    fig.write_image(os.path.join('media', 'images', 'plotly.png'))
    
    return plot_div