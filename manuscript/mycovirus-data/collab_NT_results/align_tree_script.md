## Align Sequences with MUSCLE and Construct Tree with IQ-Tree ## 


Directory: `cd ./Desktop/collab_dat_march_24`

WID Server directory for MUSCLE: `cd /mnt/ws/home/hlouw/iqtree-project/muscle-5.1.0/src/Linux`

Nucleotides: `./muscle -align /mnt/ws/home/hlouw/iqtree-project/combined_nucleotide.fasta -output /mnt/ws/home/hlouw/iqtree-project/combined_nucleotide_aligned.fasta`

**Note that the file size was too large for MUSCLE, and so the job was outsourced to ClustalW: https://www.ebi.ac.uk/jdispatcher/msa/clustalo**

IQ-Tree: `./iqtree-1.6.12-Linux/bin/iqtree -s combined_nucleotide_aligned.fasta -m MFP -bb 1000`

Job ID on ClustalW: clustalo-I20240605-225102-0824-16715335-p1m


