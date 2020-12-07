These files are in the shared [google drive](https://drive.google.com/drive/u/2/folders/0AOrB5Mv4Dq5cUk9PVA)

I need to know sample sizes:
```shell
cd Dropbox/Documents/solislemus-lab/lab-members/undergrad-student-projects/present/bioklustering-website/manuscript/validation-data/datasets

$ grep ">" bat_flu.fa | wc -l
      64
$ grep ">" cat_flu.fa | wc -l
     114
```

Now, we want to see the proportion of 0/1 on the semi-supervised versions:
```shell
cd Dropbox/Documents/solislemus-lab/lab-members/undergrad-student-projects/present/bioklustering-website/manuscript/validation-data/Semi-supervised-test-dataset
```

```r
dat50 = read.table("labels_fifty_percent.csv", header=TRUE)
dat10 = read.table("labels_ten_percent.csv", header=TRUE)

> summary(as.factor(dat50$Labels))
-1  0  1 
89 32 57 
> summary(as.factor(dat10$Labels))
 -1   0   1 
161   7  10

> 32/(32+57)
[1] 0.3595506
> 57/(32+57)
[1] 0.6404494
> 10/17
[1] 0.5882353
> 7/17
[1] 0.4117647
```

I want to create a file that only has observed labels from one class:
```r
dat10 = read.table("labels_ten_percent.csv", header=TRUE)
## currently the first 7rows are observed 0. 
## The first 64 rows are for bat (0) and the
## next 114 rows are for cat (1)

## we will make all first 17 rows observed as 0:
dat10[1:17,]=0

> head(dat10,20)
   Labels
1       0
2       0
3       0
4       0
5       0
6       0
7       0
8       0
9       0
10      0
11      0
12      0
13      0
14      0
15      0
16      0
17      0
18     -1
19     -1
20     -1


## and then, we will make the 1s == -1
dat10$Labels[dat10$Labels == 1] = -1

> summary(as.factor(dat10$Labels))
 -1   0 
161  17

write.table(dat10, file="labels_ten_percent_only0s.csv", row.names=FALSE)
```