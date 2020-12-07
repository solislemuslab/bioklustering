## Julia script to randomly decide the author of first authors
## Claudia (November 2020)

using Random
s = 9159277212
Random.seed!(s);
people = ["chunrong", "liule", "luke", "zhiwen"] ##alphabetical
people[randperm(length(people))]