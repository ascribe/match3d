import pHash
from image_match import goldberg
from image_match.signature_database import normalized_distance
import csv
import pandas as pd
import numpy as np
from operator import add

HASH_FUNCTIONS = ['dct', 'mexican_hat', 'goldberg']
# HASH_FUNCTIONS = ['dct', 'radial', 'mexican_hat', 'goldberg']

class ImageHasher:
    def __init__(self, hash_functions=HASH_FUNCTIONS):
        self.hash_functions = hash_functions
        self.dct = 'dct' in hash_functions
        self.radial = 'radial' in hash_functions
        self.mexican_hat = 'mexican_hat' in hash_functions
        self.goldberg = 'goldberg' in hash_functions
        if self.goldberg:
            self.gis = goldberg.ImageSignature()

        self.data = None

    def run(self, input_csv, output_csv='hashes.csv'):
        with open(input_csv, 'rb') as input_csv_file:
            input_reader = csv.reader(input_csv_file, delimiter=',')
            with open(output_csv, 'wb') as output_csv_file:
                output_writer = csv.writer(output_csv_file)
                for row in input_reader:
                    image_name, image_full_path, stl_full_path = row
                    hashes = self.get_hashes(image_full_path)
                    output_writer.writerow(row + hashes)

    def get_hashes(self, image_full_path):
        hashes = []
        if self.dct:
            hashes.append(pHash.imagehash(image_full_path))
        if self.radial:
            hashes.append(pHash.image_digest(image_full_path).coeffs)
        if self.mexican_hat:
            hashes.append(pHash.mh_imagehash(image_full_path))
        if self.goldberg:
            hashes.append(list(self.gis.generate_signature(image_full_path)))
        return hashes


class Benchmarker(ImageHasher):
    def load_data(self, results_csv='hashes.csv'):
        self.data = pd.read_csv(results_csv, header=None, names=['image_name',
                                                    'image_full_path',
                                                    'stl_full_path']
                                                   + self.hash_functions)

    def distances(self, target_image):
        hashes = dict(zip(self.hash_functions, self.get_hashes(target_image)))
        scores = {}
        for hash_name in hashes.iterkeys():
            scores[hash_name] = self.get_scores(hash_name, hashes[hash_name])
        df = pd.DataFrame(scores)
        df.index = self.data['image_full_path']
        return df

    def get_scores(self, hash_name, _hash):
        if hash_name == 'dct':
            return self.data[hash_name].apply(lambda x: pHash.hamming_distance(_hash, x))
        if hash_name == 'mexican_hat':
            return self.data[hash_name].apply(lambda x: pHash.hamming_distance2(_hash, eval(x)))
        if hash_name == 'goldberg':
            return self.data[hash_name].apply(lambda x: normalized_distance(np.array([eval(x)]), _hash)[0])

    def get_best(self, target_image):
        df = self.distances(target_image)
        scores = {_hash: self.get_best_col(df, _hash)
                  for _hash in self.hash_functions
                  if df[_hash].median() != 0}

        scores['composite'] = np.sqrt(reduce(add, [x**2 for x in scores.values()]))
        [x.sort() for x in scores.values()]
        return scores

    @staticmethod
    def get_best_col(df, _hash):
        return df[_hash]/df[_hash].median()
