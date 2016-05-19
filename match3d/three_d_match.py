__author__ = 'ryan'

import tempfile
import elasticsearch
from image_match.elasticsearch_driver import SignatureES
from os import spawnvp, P_WAIT, listdir, rmdir, remove, walk
from os.path import expanduser, abspath, join, splitext, dirname, basename


class ThreeDSearch(object):
    def __init__(self, es_nodes=['localhost'], index_name='match3d', cutoff=0.5):
        self.es = elasticsearch.Elasticsearch(es_nodes)
        self.ses = SignatureES(self.es, index=index_name)
        self.ses.distance_cutoff = cutoff

    @staticmethod
    def generate_images(stl_directory_name, blender_args=None):
        output_directory = tempfile.mkdtemp()

        if not blender_args:
            blender_args = ['blender',
                    '-b', '-P', 'image_match_generator.py', '--',
                    '-d', abspath(expanduser(stl_directory_name)),
                    '-o', output_directory,
                    '--no-rotations',
                    '--only-front-view']

        spawnvp(P_WAIT, 'blender', blender_args)
        return output_directory

    def search_images(self, _images_directory):
        img_paths = [join(_images_directory, x) for x in listdir(_images_directory) if splitext(x)[-1] == '.png']
        res = []
        for img_path in img_paths:
            res.append(self.ses.search_image(img_path))
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

    @classmethod
    def tournament_score(self, results, max_matches=5):
        composite_score = self.composite_score(results)
        k = composite_score.keys()
        v = composite_score.values()
        winners = sorted(zip(k, v), key=lambda x: x[1])[:max_matches]
        ranked_winners = {}
        for i, winner in enumerate(winners):
            ranked_winners.update({winner[0]: i})
        return ranked_winners

    @staticmethod
    def best_single_image(results, n_per_view=5):
        scores = {}
        for result in results:
            for i in range(n_per_view):
                if result:
                    best = min(result, key=lambda x: x['dist'])
                    k = basename(dirname(best['path']))
                    if k not in scores:
                        scores[k] = best['dist']
                    elif best['dist'] < scores[k]:
                        scores[k] = best['dist']
                    result.remove(best)
        return scores

    @staticmethod
    def _get_directories_of_type(directory, filetypes=['stl'], ignore_path=''):
        w = walk(directory)
        for t in w:
            for filename in t[-1]:
                if not filename.startswith('.')\
                        and filename.rpartition('.')[-1] in filetypes\
                        and abspath(join(t[0], filename)) != ignore_path:
                    yield abspath(join(t[0], filename))

    def run(self, stl_directory_name, return_raw=False, ranking='dist'):
        key = basename(dirname(stl_directory_name))
        images_path = self.generate_images(dirname(stl_directory_name))
        res = self.search_images(images_path)
        for file_path in listdir(images_path):
            remove(join(images_path, file_path))
        rmdir(images_path)
        if return_raw:
            return res
        elif ranking == 'dist':
            return {key: self.composite_score(res)}
        elif ranking == 'tournament':
            return {key: self.tournament_score(res)}
        elif ranking == 'single':
            return {key: self.best_single_image(res)}

    def run_all(self, stl_top_level_dir, ranking='single'):
        stl_paths = self._get_directories_of_type(stl_top_level_dir)
        scores = {}
        for stl_path in stl_paths:
            scores.update(self.run(stl_path, ranking=ranking))
        return scores
