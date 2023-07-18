# Data from antibiotic resistance

We got the data from `dna-nn/data/data2`.

Two files:
- `concatenated.fasta` with the aligned sequences (122 strains, 483,333 sites)
- `responses.csv` with the labels


Manually, I had to remove the gaps `-` in `concatenated.fasta`.

We also have to write the labels in the same format:

```{r}
dat = read.csv("responses.csv", header=TRUE)

## carb antibiotic
dat2 = data.frame(class=rep(0,length(dat$carb)))
dat2$class[dat$carb == "true"] = 1
## Note that there are 2 unknown labels that I am imputing as 0
write.csv(dat2, file="responses-carb.csv", row.names=FALSE)

## toby antibiotic
dat2 = data.frame(class=rep(0,length(dat$toby)))
dat2$class[dat$toby == "true"] = 1
## Note that there are 2 unknown labels that I am imputing as 0
write.csv(dat2, file="responses-toby.csv", row.names=FALSE)
```