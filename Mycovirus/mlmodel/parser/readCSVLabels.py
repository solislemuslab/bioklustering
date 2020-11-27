import pandas as pd
import os

def read_csv_labels(label_paths):
    all_labels = pd.Series()
    for path in label_paths:
        path = os.path.join("media", path)
        labels = pd.read_csv(path)
        labels = pd.Series(labels['Labels'])
        all_labels = all_labels.append(labels, ignore_index=True)
    all_labels.name = "Labels"
    return all_labels

