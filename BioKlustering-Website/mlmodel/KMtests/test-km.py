import unittest
import pandas as pd

from websiteScripts import *

# data needed
PATH1 = "../data/Sclerotinia_biocontrol_mycovirus_nucleotide.fasta"
PATH01 = "../data/mycovirus_genbank_all_refseq_nucleotide_unique.fasta"
labels_true = [-1 for x in range(350)]

# read in saved labels 
y_hat_us_true = pd.read_csv('y_hat_us_true.csv')
y_hat_s_true = pd.read_csv('y_hat_s_true.csv')

class TestKM(unittest.TestCase):
    def test_km_us(self):
        data = PATH01
        result = kmeans(PATH01, 2, 6, 7, 50)
        for i in range(0, len(result)):
            self.assertEqual(result[0][i], y_hat_us_true['0'][i])
        
    def test_km_s(self):
        data = PATH01
        result = kmeans_semiSupervised(PATH01, labels_true, 6, 7, 50)
        for i in range(0, len(result)):
            self.assertEqual(result[0][i], y_hat_s_true['0'][i])
        
        
if __name__ == '__main__':
    unittest.main()