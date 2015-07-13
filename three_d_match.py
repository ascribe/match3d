__author__ = 'ryan'

import tempfile
import elasticsearch
from os import execvp

class ThreeDSearch():
    def __init__(self):
        self.output_directory = None

    def run(self, stl_directory_name):
        self.output_directory = tempfile.mkdtemp()

        args = ['-b', '-p', 'image_match_generator.py', '--',
                '-d', stl_directory_name,
                '-o', self.output_directory]

        execvp('blender', args)