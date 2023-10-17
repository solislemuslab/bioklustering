# Bingo 3C

## Introduction to Bingo-3C

Bingo-3C is an open-source tool (https://github.com/mouneem/BiNGO-3C/tree/main) that clusters genomic sequences by encoding them to a 2-bit binary format. Since Bingo-3C also split the long DNA sequence into smaller k-mers (or words, as used in Bingo-3C), we add Bingo-3C for comparison with BioKlustering.

## Steps we took to run Bingo-3C

1. Download the zipped repository from github.
2. Enhanced the backend of Bingo-3C by incorporating JavaScript code, enabling the extraction of a similarity matrix as a CSV file. Initially, the similarity scores were represented as strings/texts, but the code parses them into a two-dimensional matrix and facilitates the automatic download of the CSV file. (The updated Bingo-3C can be found here in this forked repository: https://github.com/YukeWu/BiNGO-3C)
3. Executed Bingo-3C using our dataset of 500 Covid sequences.
    - Copy the sequences in ./bingo_test_input.txt (https://github.com/YukeWu/bioklustering/blob/master/manuscript/Covid_data/bingo_test_input.txt).
    - Open index.html (BiNGO-3C/SW3C_webserver/index.html) by double clicking the file. 
    - Paste the sequences into the text input section of Multiple Sequecne Comparison, which is colored green in index.html.
    - Set word size to be 3 and use the default gap size, which is set to 1.
    - Click "Compare all sequences" and the browser will pop up to ask if the user would allow downloading.
    - Click "Allow" to obtain the CSV file that contains the similarity matrix.
4. Developed a Python script to cluster the sequences based on the similarity matrix, utilizing the same clustering methods employed in BioKlustering (KMeans, Gausian-Mixture Model, and Spectral Clustering).