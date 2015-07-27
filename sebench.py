"""Tools to benchmark search engines by comparing their search results
to 'golden search results'. It's only useful if you have golden search
results.
"""

import csv
import numpy as np
import networkx as nx
from operator import itemgetter
from os.path import join, abspath


class SEBenchmarker:

    def __init__(self, golden_sr_csv, approved_names_csv=''):
        """Reads the 'golden search engine results' from the CSV file
        at golden_sr_csv into some internal data structures.
        Optional: check the item names against those in a file
        of approved names.
        """
        # The distance from a query item to items definitely-similar to
        # it is assumed to be 1. The distance to maybe-similar items is
        # self.dist2
        self.dist2 = 2

        # Initialize the two main dictionaries as empty
        self.definitely_similar = {}
        self.maybe_similar = {}

        # Read the golden search results file
        with open(golden_sr_csv, 'rb') as csvfile:
            row_reader = csv.reader(csvfile, delimiter=',',
                                    quotechar='"')
            for row_list in row_reader:
                qname = row_list[0]
                idx0 = row_list.index('0')
                idx1 = row_list.index('1')
                self.definitely_similar[qname] = row_list[1:idx0]
                self.maybe_similar[qname] = row_list[(idx0 + 1):idx1]

        # Check item names against those in the approved-names file
        if approved_names_csv != '':
            approved_names = []
            used_as_key = {}
            with open(approved_names_csv, 'rb') as csvfile2:
                row_reader2 = csv.reader(csvfile2, delimiter=',',
                                         quotechar='"')
                for row_list in row_reader2:
                    item_name = row_list[0]
                    approved_names.append(item_name)
                    used_as_key[item_name] = False

            # Check that all keys and values are approved names
            for dict_to_check in [self.definitely_similar, self.maybe_similar]:
                for key, value in dict_to_check.items():
                    if key not in approved_names:
                        SEBenchmarker._raise_typo_exception(key)
                    else:
                        used_as_key[key] = True
                    for item_name in value:
                        if item_name not in approved_names:
                            SEBenchmarker._raise_typo_exception(item_name)

            # Check if any approved names didn't get used as keys
            for key, value in used_as_key.items():
                if not value:  # i.e. value == False
                    err_str = key + ' is an approved item name but it never'
                    err_str += ' appeared as a query item in the golden search'
                    err_str += ' results file (i.e. as first on a line).'
                    raise ValueError(err_str)

        self.item_list = self.definitely_similar.keys()
        self.num_items = len(self.item_list)

        # Build the weighted directed graph DG
        # (The weights are interpreted as distances between items)
        self.DG = nx.DiGraph()
        for item_name_1 in self.item_list:
            for item_name_2 in self.definitely_similar[item_name_1]:
                self.DG.add_edge(item_name_1, item_name_2, weight=1)
            for item_name_2 in self.maybe_similar[item_name_1]:
                self.DG.add_edge(item_name_1, item_name_2, weight=self.dist2)

        # Note: It's not necessary to add any weight-zero edges from
        # nodes to themselves; the dijkstra_path_length method will already
        # tell you the minimum distance from A to A is 0.

        if self.DG.number_of_nodes() != self.num_items:
            err_str = 'The number of nodes in the digraph is different'
            err_str += ' from the number of items.'
            raise ValueError(err_str)

    def report1(self, qname_list, search_results_list):
        """Generates a report for a set of searches and their corresponding
        search results. qname_list is a list of strings; qname_list[i] is
        the name of the item searched-for on the ith search.
        search_results_list[i] is the list of search results on the ith
        search. (search_results_list is a list of lists.)
        """
        score_list = {}  # will be a dictionary of lists of scores
        for i, qname in enumerate(qname_list):
            score = self.every_score(qname, search_results_list[i])
            for score_name, value in score.items():
                if score_name not in score_list.keys():
                    score_list[score_name] = [value]
                else:
                    score_list[score_name].append(value)
        report = 'Summary Statistics\n'
        for score_name, value_list in score_list.items():
            val_array = np.array(value_list)
            report += '{}\n'.format(score_name)
            report += "  Number of values summarized = {}\n".format(len(val_array))
            report += "  Median  = {}\n".format(np.median(val_array))
            report += "  Average = {}\n".format(np.average(val_array))
        return report

    def report2(self, qname_list, search_results_list, img_path, html_fname):
        """Writes an HTML file named html_fname containing a visual presentation
        of the searches (qname_list) and their results (search_results_list).
        img_path is the full path to the directory containing item images,
        which are assumed to have file names of the form itemname.png
        """
        with open(html_fname, 'w') as f:
            f.write("<!DOCTYPE html>\n<html>\n<head>\n")
            f.write("<title>Search Report</title>\n</head>\n<body>\n")
            for i, qname in enumerate(qname_list):
                f.write("<h1>Search {}</h1>\n".format(i))
                f.write("<p>Searched for:</p>\n")
                path1 = abspath(join(img_path, qname + '.png'))
                f.write('<img src="file://{}">'.format(path1))
                f.write("<p>Results:</p>\n")
                for item_name in search_results_list[i]:
                    path2 = abspath(join(img_path, item_name + '.png'))
                    f.write('<img src="file://{}">'.format(path2))
                f.write("\n")
                f.write('<p>Items a human said are <em>definitely similar</em> (if any):</p>\n')
                for item_name in self.definitely_similar[qname]:
                    path2 = abspath(join(img_path, item_name + '.png'))
                    f.write('<img src="file://{}">'.format(path2))
                f.write("\n")
                f.write("</body>\n</html>\n")
        return True

    def every_score(self, qname, search_results):
        """Returns a dictionary of all scores for the given query item
        and search results.
        """
        score = {}
        score['precision1'], score['recall1'] = \
            self.precision_and_recall(qname, search_results, version=1)
        score['precision2'], score['recall2'] = \
            self.precision_and_recall(qname, search_results, version=2)
        score['similarity'] = self.similarity_score(qname, search_results)
        score['disorder'] = self.disorder_score(qname, search_results)
        score['first_result'] = self.first_result_score(qname, search_results)
        return score

    def precision_and_recall(self, qname, search_results, version=1):
        """The precision and recall of the search results.
        Precision = fraction of search_results that are relevant.
        Recall = fraction of all relevant items found.
        If version=1 (the default), then the relevant set includes only
        qname and the items definitely-similar to qname.
        If version=2, then the relevant set also includes the items
        maybe-similar to qname.
        """
        self.check_item_names(qname, search_results)
        rel_items = [qname] + self.definitely_similar[qname]
        if version == 2:
            rel_items += self.maybe_similar[qname]
        rel_set = set(rel_items)
        sr_set = set(search_results)
        intersection = rel_set & sr_set
        num_rel_sr = len(intersection)
        precision = float(num_rel_sr) / float(len(search_results))
        recall = float(num_rel_sr) / float(len(rel_set))
        return precision, recall

    def similarity_score(self, qname, search_results):
        """A score where each item in the search results contributes.
        If qname is in the search results, it adds self.dist2.
        If there is no path from qname to the item, it adds 0.0.
        Otherwise the item adds 1 / (min. distance from qname to item).
        The reported score is normalized by dividing by the maximum
        possible score. Ideally, the reported similarity score is 1.0.
        The order of the search results won't affect this score.
        """
        self.check_item_names(qname, search_results)

        # This is a dictionary keyed by target item name
        shortest_dist_to = \
            nx.single_source_dijkstra_path_length(self.DG, qname,
                                                  cutoff=None,
                                                  weight='weight')
        # Determine the score of search_results
        score = 0.0
        for item_name in search_results:
            if item_name == qname:
                score += float(self.dist2)
            elif item_name in shortest_dist_to.keys():
                score += 1.0 / float(shortest_dist_to[item_name])
            else:
                # there is no path from qname to item_name
                score += 0.0

        # Determine the max_possible_score
        shortest_dist_to[qname] = 0
        for item_name in self.item_list:
            # i.e. for all possible items, including qname
            if item_name not in shortest_dist_to.keys():
                shortest_dist_to[item_name] = 12345678  # a big flag value

        sorted_list_of_tuples = sorted(shortest_dist_to.items(),
                                       key=itemgetter(1))
        max_possible_score = 0.0
        for idx in range(len(search_results)):
            dist = sorted_list_of_tuples[idx][1]
            if dist == 0:
                max_possible_score += float(self.dist2)
            elif dist == 12345678:
                max_possible_score += 0.0
            else:
                max_possible_score += 1.0 / float(dist)

        return score / max_possible_score

    def disorder_score(self, qname, search_results):
        """A score that tells you how many adjacent-element swaps you
        need to do to the search results to get them in the correct
        order, from closest-to-qname to farthest-from-qname.
        It's normalized by dividing by the maximum possible # swaps,
        so it ranges from 0.0 to 1.0.
        This is a score you want to minimize. Ideally it is zero.
        Key fact: minimum # swaps = # inversions in the array.
        See https://stackoverflow.com/questions/20990127/
        """
        self.check_item_names(qname, search_results)

        # list_to_sort[i] = the minimum distance from qname to
        #                   search_results[i]
        nr = len(search_results)
        list_to_sort = [None] * nr
        for idx, item_name in enumerate(search_results):
            try:
                list_to_sort[idx] = nx.dijkstra_path_length(self.DG, qname,
                                                            item_name,
                                                            weight='weight')
            except nx.NetworkXNoPath:
                # No path exists betwen qname and item_name
                list_to_sort[idx] = 10000000  # just some big number

        # Count the number of inversions in list_to_sort
        _, inv_count = SEBenchmarker._sort_and_count(list_to_sort)

        # Calculate the max number of inversions possible
        inv_max = (nr * (nr-1)) / 2

        return float(inv_count) / float(inv_max)

    def first_result_score(self, qname, search_results):
        """This score is 1.0 if the first search result is qname,
        and 0.0 otherwise. (A float is returned so these scores
        can be averaged without any integer division surprises.)
        """
        self.check_item_names(qname, search_results)
        return (1.0 if (search_results[0] == qname) else 0.0)

    def check_item_names(self, qname, search_results):
        """Checks to make sure qname and all items in search_results
        are known items, and raises an exception if they're not."""
        if qname not in self.item_list:
            SEBenchmarker._raise_unknown_item_exception(qname)
        for item_name in search_results:
            if item_name not in self.item_list:
                SEBenchmarker._raise_unknown_item_exception(item_name)

    @staticmethod
    def _raise_unknown_item_exception(item_name):
        err_str = "No score can be calculated"
        err_str += " for a search involving an item named " + item_name
        err_str += " because there is no known item with that name."
        raise ValueError(err_str)

    @staticmethod
    def _raise_typo_exception(item_name):
        err_str = item_name + ' was used as an item name in the golden search'
        err_str += ' results file but it is not in the list of approved names.'
        raise ValueError(err_str)

    @staticmethod
    def _sort_and_count(li, c=0):
        if len(li) < 2:
            return li, c
        m = len(li) / 2
        l, cl = SEBenchmarker._sort_and_count(li[:m], c)
        r, cr = SEBenchmarker._sort_and_count(li[m:], c)
        return SEBenchmarker._merge(l, r, cl + cr)

    @staticmethod
    def _merge(l, r, c):
        result = []
        while l and r:
            s = l if l[0] <= r[0] else r
            result.append(s.pop(0))
            if s == r:
                c += len(l)
        result.extend(l if l else r)
        return result, c
