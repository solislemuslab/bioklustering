#!/usr/bin/env python
# coding: utf-8

# In[35]:


import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)
from mlmodel.parser import GMM
import pandas as pd


# In[ ]:


def test_GMM_Unsup(test_file_1):
    k_min = 2 
    k_max = 6 
    num_class = 2 
    cov_type = 'full' 
    seed = 0
    [labels],[plot] = GMM.get_predictions(0, [test_file_1], k_min, k_max, num_class, cov_type, seed, 'PCA')
    print(labels)
    assert all(labels['Labels'] == [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0,
       1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,
       1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1,
       1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0,
       1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1,
       1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
       1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
       1, 1])
    
def test_GMM_Semi(test_file_1,test_file_2):
    k_min = 2 
    k_max = 3 
    num_class = 2 
    cov_type = 'full' 
    seed = 0 
    labels_50 = pd.read_csv('media/' + test_file_2)
    labels_50 = pd.Series(labels_50['Labels'])
    
    [labels],[plot] = GMM.get_predictions_semi(0, [test_file_1],k_min,k_max,num_class,cov_type,seed,labels_50, 'PCA')

    assert all(labels == [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
       1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1,
       0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 1,
       0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0,
       1, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1,
       1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1,
       1, 1, 1, 1, 0, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0,
       0, 1])
    
def test_GMM_Semi2(test_file_1,test_file_3):
    num_class = 2
    labels_10 = pd.read_csv('media/' + test_file_3)
    labels_10 = pd.Series(labels_10['Labels'])
    
    [labels],[plot] = GMM.model_selection(0, [test_file_1], labels_10, num_class, 0, 'method')
    
    labels = GMM.model_selection([test_file_1],labels_10,num_class)
    assert all(labels == [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
       0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
       1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1,
       1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0,
       1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0,
       0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0,
       0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0,
       1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 
       0, 1])


# In[11]:


#test_file_1 = "../../../manuscript/validation_data/Semi-supervised-test-dataset/combined_Bat_Cat_flu.fa" #need to be changed to filepath in github
#test_file_2 = '../../../manuscript/validation_data/Semi-supervised-test-dataset/labels_fifty_percent.csv' #need to be changed to filepath in github
#test_file_3 = '../../../manuscript/validation_data/Semi-supervised-test-dataset/labels_ten_percent.csv' #need to be changed to filepath in github

os.system("ls")
print("0-----------------")
os.system("ls ../")
print("0-----------------")
os.system("ls ../manuscript/")
print("0-----------------")
os.system("ls ../manuscript/validation-data/")
print("0-----------------")
os.system("ls ../manuscript/validation-data/Semi-supervised-test-dataset/")

os.system("cp ../manuscript/validation-data/Semi-supervised-test-dataset/combined_Bat_Cat_flu.fa media/combined_Bat_Cat_flu.fa")
os.system("cp ../manuscript/validation-data/Semi-supervised-test-dataset/labels_fifty_percent.csv media/labels_fifty_percent.csv")
os.system("cp ../manuscript/validation-data/Semi-supervised-test-dataset/labels_ten_percent.csv media/labels_ten_percent.csv")


test_file_1 = "combined_Bat_Cat_flu.fa"
test_file_2 = "labels_fifty_percent.csv"
test_file_3 = "labels_ten_percent.csv"


test_GMM_Unsup(test_file_1)    
test_GMM_Semi(test_file_1,test_file_2)
test_GMM_Semi2(test_file_1,test_file_3)

os.system("rm media/combined_Bat_Cat_flu.fa")
os.system("rm media/labels_fifty_percent.csv")
os.system("rm media/labels_ten_percent.csv")

print("Everything passed")



# In[ ]:




