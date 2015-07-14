__author__ = 'ryan'

import tempfile
import elasticsearch
from os import execvp


class ThreeDSearch():
    def __init__(self, _stl_directory_name):
        self.output_directory = None
        self.stl_directory_name = _stl_directory_name

    def generate_images(self):
        self.output_directory = tempfile.mkdtemp()

        args = ['blender',
                '-b', '-P', 'image_match_generator.py', '--',
                '-d', self.stl_directory_name,
                '-o', self.output_directory]

        execvp('blender', args)
        return self.output_directory

    def search_images(self):
        pass

    def run(self):
        print self.generate_images()
        #  self.search_images()