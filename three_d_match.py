__author__ = 'ryan'

import tempfile
import elasticsearch
from image_match.signature_database import SignatureES
from os import spawnvp, P_WAIT, listdir
from os.path import expanduser, abspath, join, splitext


class ThreeDSearch():
    def __init__(self, es_nodes=['localhost'], index_name='***REMOVED***_tester'):
        self.es = elasticsearch.Elasticsearch(es_nodes)
        self.ses = SignatureES(self.es, index=index_name)

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
        for img_path in img_paths:
            pass

    def run(self, stl_directory_name):
        images_path = self.generate_images(stl_directory_name)
        self.search_images(images_path)