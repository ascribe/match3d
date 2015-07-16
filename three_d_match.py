__author__ = 'ryan'

import tempfile
import elasticsearch
from image_match.signature_database import SignatureES
from os import spawnvp
from os import P_WAIT
from os.path import expanduser, abspath

INDEX_NAME = '***REMOVED***_tester'

class ThreeDSearch():
    def __init__(self, _stl_directory_name):
        self.output_directory = None
        self.stl_directory_name = _stl_directory_name

    def generate_images(self):
        self.output_directory = tempfile.mkdtemp()

        args = ['blender',
                '-b', '-P', 'image_match_generator.py', '--',
                '-d', abspath(expanduser(self.stl_directory_name)),
                '-o', self.output_directory,
                '--no-rotations',
                '--only-front-view']

        spawnvp(P_WAIT, 'blender', args)
        return self.output_directory

    def search_images(self):
        pass

    def run(self):
        path = self.generate_images()
        #  self.search_images()