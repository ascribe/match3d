"""An example Python script illustrating how to use sebench to benchmark
a set of search results from a search engine.
"""

import numpy as np
from sebench import SEBenchmarker


fpath = './score_matrix_tournament.csv'
sr_arr = np.genfromtxt(fpath, dtype=object, delimiter=',')
# print "sr_arr.shape = {}".format(sr_arr.shape)

# Set up a search engine benchmarker (sebench)
# by reading a file of golden search results
csv1 = './***REMOVED***_data/golden_se_results.csv'
csv2 = './***REMOVED***_data/approved_names.csv'
bmt = SEBenchmarker(csv1, csv2)

score_dict = {}  # will be a dictionary of lists

for row_idx in range(1, sr_arr.shape[0]):
    qname = sr_arr[row_idx, 0]
    row_list = sr_arr[row_idx].tolist()
    search_results = []

    for result_num in range(5):
        num_str = str(result_num) + '.0'
        idx_of_result_num = row_list.index(num_str)
        item_name = sr_arr[0, idx_of_result_num]
        search_results.append(item_name)

    se_score = bmt.every_score(qname, search_results)
    if se_score['first_result'] != 1.0:
        print "\nWhen qname = {}".format(qname)
        print "the first search result is not {}".format(qname)
        print "In fact, search_results = {}".format(search_results)

    for key, value in se_score.items():
        if key not in score_dict:
            score_dict[key] = [value]
        else:
            score_dict[key].append(value)

print "\nSummary Statistics\n"
for key, value in score_dict.items():
    val_array = np.array(value)
    print "{}".format(key)
    print "  Number of values summarized = {}".format(len(val_array))
    print "  Median  = {}".format(np.median(val_array))
    print "  Average = {}".format(np.average(val_array))
