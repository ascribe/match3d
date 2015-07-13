#Benchmarking Similariy Search Engines with sebench

sebench.py is a Python module with tools to benchmark similarity search engines.

It works by comparing a search engine's search results to golden search results created by humans. It outputs a bunch of scores.


##Terminology

One submits an item with a particular name ("query name" or qname) to a search engine and one gets back an ordered list of items (search results), in order from most similar to least similar.

qname --> Search Engine --> search_results (a Python list of item names)

'Joe' --> Search Engine --> ['Joe', 'Sam', 'Tom', 'Robert', 'Ken']

Golden search results are search results that were created manually by humans. For a particular query item, there are two lists: the definitely-similar items (which you definitely want in the search results) and the maybe-similar items (which might be nice to have in the search results, as a bonus). For example:

definitely_similar['Joe'] = ['Moe', 'Bo']

maybe_similar['Joe'] = ['Joseph']

One or both of those lists may be empty. Note that qname is not included in the definitely-similar list. That's because qname is identical to qname, which goes beyond being definitely-similar. We always hope that qname will be the first search result.

## Input Files

The two lists are stored and read from a CSV file of golden search results. That file has the following general structure:

```
"Joe","Moe","Bo","0","Joseph","1"
"Jill","Tammy","0","Marina","Amanda","1"
"Fido","Rex","0","1"
```
The first item in a row is qname, then comes the list of definitely-similar items, terminated by a "0" entry. Then comes the list of maybe-similar items, which is terminated by a "1". (You'll want to avoid having items named "0" and "1".)

There's a second, optional CSV file, listing all the allowed item names, with one name per line. It's useful to automatically detect spelling mistakes or other typos in the golden search results file.

```
"Joe"
"Moe"
"Bo"
etc.
```
##Usage Example

Suppose we have a file of golden search results and a file of approved item names. Suppose also that we submitted 'B' to a search engine and the resulting search results were ['A','E','C','D']. Here's how we'd get the set of scores for those search results:

(Note that sebench.py imports csv, networkx, and operator. Those are all included in the Python 2.7 Anaconda packages.)

```
$ ipython

In [1]: from sebench import SEBenchmarker

In [2]: bmt = SEBenchmarker('./data/test_golden_sr.csv','./data/test_apr_names.csv')

In [3]: sc4 = bmt.every_score('B',['A','E','C','D'])

In [4]: sc4
Out[4]: 
{'disorder': 0.16666666666666666,
 'first_result': 0.0,
 'precision1': 0.5,
 'precision2': 0.75,
 'recall1': 0.6666666666666666,
 'recall2': 0.75,
 'similarity': 0.5555555555555556}
```
## Explanations of the Scores

### First Result Score

The **first result score** is 1.0 if the first search result is the same as qname, and 0.0 otherwise. In the above example, it was 0.0 because the first search result was 'A' but it should have been 'B'. Had it been 'B', the first result score would have been 1.0.

### Precision and Recall

**Precision** is the fraction of the search results which are "relevant items." **Recall** is the fraction of relevant items that were found. There are many ways to define a relevant item. Two possibilities are:

1. A "relevant item" is any item that is either qname or one of the items definitely-similar to qname.
2. A "relevant item" is any item that is qname, an item definitely-similar to qname, or an item maybe-similar to qname.

In the above example, there are four search results ('A', 'E', 'C', and 'D'). Moreover:

definitely_similar('B') = ['A','C']

maybe_similar('B') = ['E']

So:

relevant set (def. 1) = 'B', 'A', 'C' (3 items), and of those 2 were found

relevant set (def. 2) = 'B', 'A', 'C', 'E' (4 items), and of those 3 were found

So:

precision1 = (2 relevant1 items found) / (4 search results) = 0.5

precision2 = (3 relevant2 items found) / (4 search results) = 0.75

recall1 = (2 relevant1 items found) / (3 relevant1 items) = 0.66666...

recall2 = (3 relevant2 items found) / (4 relevant2 items) = 0.75

### Similarity and Disorder Scores

The last two scores, similarity and disorder, hinge on a calculation of distance from qname to other items. Here's how that distance is calculated:

The distance from qname to qname is zero. The distance from qname to definitely-similar items is 1. The distance from qname to maybe-similar items is a constant named self.dist2 in the code. It's currently hardwired as self.dist2 = 2.

How can we calculate the distance to other items? We can draw a weighted directed graph (digraph) where the nodes are items and:

* if B is in the list of items definitely-similar to A, then there's a directed edge from A to B with weight = 1.
* if U is in the list of items maybe-similar to V, then there's a directed edge from V to U with weight = self.dist2 = 2.

The distance from qname to any item can then be *defined* as the length of the shortest path from qname to that item. If there's no such path, then the distance is undefined (or we can pretend it's some very big number).

Roughly speaking, the similarity score of some search results equals the sum of the *inverse* distances from qname to the items in the search results. If qname is in the search results, we don't add 1/0, we add self.dist2 = 2 to that score. If there's an item in the search results where there's no path from qname to that item, then that item contributes 0.0 to the score.

That score is some number between 0.0 and some maximum. It will be maximum if the search results include qname, as many definitely-similar items as possible, and then as many maybe-similar items as possible. (We pretend that we can only get as many search results as are in search_results.) Therefore we can calculate the maximum score.

Knowing the maximum, we can normalize the similarity score by dividing by that maximum. That means the (normalized) similarity score, which is what gets reported, can range from 0.0 to 1.0. Ideally, it is 1.0.

In the above example, the search results were A, E, C, and D, with distances-from-qname of 1, 2, 1, and effectively infinite. Therefore:

un-normalized similarity score = 1/1 + 1/2 + 1/1 + 0.0 = 2.5

maximum similarity score = score of B, A, C, E = 2 + 1/1 + 1/1 + 1/2 = 4.5

normalized similarity score = 2.5 / 4.5 = 0.5555...

Note that the similarity score doesn't care about the *order* of the search results. It just cares that the search engine found lots of similar items, the more the better, with more-similar items contributing more to the score.

In the above example, the search results were ['A','E','C','D']. Their distances from qname are [1, 2, 1, effectively infinite]. We see that their order is almost correct (increasing). If we just swap the two middle results, then we get a sequence that increases from the closest (most-similar) item to the farthest-away (least-similar).

We could define the "disorder" as the minimum number of adjacent-item swaps necessary to get the search results in the correct order (increasing order of distance from qname). It turns out (via [a theorem](https://stackoverflow.com/questions/20990127/)) that equals the number of "inversions" of the array, which can be counted by doing a merge sort. The code does that.

The final-reported disorder score is divided by the maximum possible number of inversions, which happens to be n*(n-1)/2 (where n is the number of search results).

Therefore, disorder ranges from 0.0 to 1.0. Ideally, it's 0.0. It's something we want to minimize.

In the above example, the number or swaps needed to get the search results in the correct (increasing) order was 1. The maximum-possible number of swaps needed was 4*(4-1)/2 = 6. Therefore:

disorder = 1/6 = 0.16666...

If similarity=1.0 and disorder=0.0, then the search results are the best we could hope for (for that number of search results).
