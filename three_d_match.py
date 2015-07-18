__author__ = 'ryan'

import tempfile
import elasticsearch
from image_match.signature_database import SignatureES
from os import spawnvp, P_WAIT, listdir, rmdir, remove, walk
from os.path import expanduser, abspath, join, splitext, dirname, basename


class ThreeDSearch():
    def __init__(self, es_nodes=['localhost'], index_name='***REMOVED***_tester', cutoff=0.1):
        self.es = elasticsearch.Elasticsearch(es_nodes)
        self.ses = SignatureES(self.es, index=index_name)
        self.ses.distance_cutoff = cutoff

    @staticmethod
    def generate_images(stl_directory_name):
        output_directory = tempfile.mkdtemp()

        args = ['blender',
                '-b', '-P', 'image_match_generator.py', '--',
                '-d', abspath(expanduser(stl_directory_name)),
                '-o', output_directory,
                '--no-rotations',
                '--only-front-view']

        spawnvp(P_WAIT, 'blender', args)
        return output_directory

    def search_images(self, _images_directory):
        img_paths = [join(_images_directory, x) for x in listdir(_images_directory) if splitext(x)[-1] == '.png']
        res = []
        for img_path in img_paths:
            s = self.ses.parallel_find(img_path, n_parallel_words=self.ses.N)
            res.append(s.next())
        return res

    @staticmethod
    def composite_score(results):
        uniques = {}
        for i, result in enumerate(results):
            for hit in result:
                k = basename(dirname(hit['path']))
                if uniques.has_key(k):
                    uniques[k].append(hit['dist'])
                else:
                    uniques[k] = [hit['dist']]
        for key in uniques:
            uniques[key] += (3 - len(uniques[key])) * [1.]
            uniques[key] = sum(uniques[key])/3.0

        return uniques

    @staticmethod
    def _get_directories_of_type(directory, filetypes=['stl'], ignore_path=''):
        w = walk(directory)
        for t in w:
            for filename in t[-1]:
                if not filename.startswith('.')\
                        and filename.rpartition('.')[-1] in filetypes\
                        and abspath(join(t[0], filename)) != ignore_path:
                    yield abspath(join(t[0], filename))

    def run(self, stl_directory_name):
        key = basename(dirname(stl_directory_name))
        images_path = self.generate_images(dirname(stl_directory_name))
        res = self.search_images(images_path)
        for file_path in listdir(images_path):
            remove(join(images_path, file_path))
        rmdir(images_path)
        return {key: self.composite_score(res)}

    def run_all(self, stl_top_level_dir, ):
        stl_paths = self._get_directories_of_type(stl_top_level_dir)
        scores = {}
        for stl_path in stl_paths:
            scores.update(self.run(stl_path))
        return scores