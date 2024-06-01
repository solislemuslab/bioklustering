## Align Sequences with MUSCLE and Construct Tree with IQ-Tree ## 


Directory: `cd ./Desktop/collab_dat_march_24`

Amino Acids: `./muscle -in ./combined_amino.fasta -out ./collab_amino_aligned.fasta`

IQ-Tree: `./iqtree-1.6.12-Linux/bin/iqtree -s collab_amino_aligned.fasta -m MFP -bb 1000`


