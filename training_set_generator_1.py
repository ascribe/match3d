"""Blender script for generating training sets

Requires blender 2.7+

Usage example: see README.md
"""

__author__ = 'ryan'

# put modules in path
import sys
sys.path.append('.')
from blenderbase import BlenderBase
from mathutils import Matrix, Vector    # blender-specific classes

from os import mkdir, walk
from hashlib import md5
from collections import Counter
from random import choice
from mimetypes import MimeTypes
from os.path import join, abspath

import numpy as np
import argparse
import csv


class TrainingSetGenerator(BlenderBase):
    def __init__(self, args):
        resolution = args.get('resolution')
        if not resolution:
            resolution = 512
        super(TrainingSetGenerator, self).__init__(resolution)

        # transforms
        self.TRANSFORM_DICT = {'rotate': self._random_rotate_object,
                               'lighting': self._random_lighting,
                               'none': self._no_transform}

        # required arguments
        self.target_file = args['target']
        self.n = args['num-examples']
        self.output_dir = args['output-dir']

        # optional parameters
        self.stl_directory = args.get('stl_directory')
        self.image_directory = args.get('image_directory')

        if args.get('transforms'):
            self.transforms = args.get('transforms')
            for transform in self.transforms:
                if transform not in self.TRANSFORM_DICT:
                    raise KeyError('{} not a valid transformation.  Valid transformations are {}.'
                                   .format(transform, self.TRANSFORM_DICT.keys()))
        else:
            self.transforms = ['none']

        # initialize the light source
        self.scene.objects['Lamp'].location = 5 * Vector([1, 1, 1])

        # initialize the directory structure
        try:
            mkdir(self.output_dir)
        except OSError as e:
            # directory may already exist
            if e.errno == 17:
                pass
            else:
                raise e

    def run(self):
        # initialize csv writers
        with open(join(self.output_dir, 'report.csv'), 'w') as csv_report_file,\
                open(join(self.output_dir, 'ground_truth.csv'), 'w') as csv_ground_truth_file:
            # generate target files
            self._generate_images(self.target_file, n=self.n,
                                  report_file=csv_report_file,
                                  ground_truth_file=csv_ground_truth_file,
                                  is_target=1)

            if self.stl_directory:
                # generate confusion files
                stls = list(set(self._get_filesnames_of_type(self.stl_directory,
                                                             filetypes=['stl'],
                                                             ignore_path=abspath(self.target_file))))
                used_stls = []
                for i in range(self.n):
                    used_stls.append(choice(stls))
                counter = Counter(used_stls)
                del used_stls
                del stls
                for key in counter.keys():
                    self._generate_images(key, n=counter[key],
                                          report_file=csv_report_file,
                                          ground_truth_file=csv_ground_truth_file,)

            if self.image_directory:
                # add paths to image files
                m = MimeTypes()
                img_suffixes = [key[1:] for key in m.types_map[1].keys() if m.types_map[1][key].startswith('image')]
                imgs = list(set(self._get_filesnames_of_type(self.image_directory,
                                                             filetypes=img_suffixes)))
                for i in range(self.n):
                    image_path = choice(imgs)
                    if not hasattr(self, 'ground_truth_writer'):
                        self.ground_truth_writer = csv.DictWriter(ground_truth_file, delimiter='\t', fieldnames=['render_path', 'is_target'])
                    self.ground_truth_writer.writerow({'render_path': image_path, 'is_target': 0})

    def _generate_images(self, stl_path, n, report_file=None, ground_truth_file=None, is_target=0):
        self._clear_scene()
        obj = self._load_stl(stl_path)
        self._center_object(obj)
        self._scale_object(obj)
        self._set_tracking(obj)

        for i in range(n):
            row = dict()
            row['stl_path'] = abspath(stl_path)
            path_base = md5(stl_path.encode('utf-8')).hexdigest()
            for transform in self.transforms:
                transform_name = self.TRANSFORM_DICT[transform].__name__
                transform_vals = self.TRANSFORM_DICT[transform](obj)
                for key in transform_vals.keys():
                    row['_'.join([transform_name, key])] = transform_vals[key]

            render_path = join(self.output_dir, '{}.{}.png'.format(path_base, i))
            self._render_scene(render_path)
            row['render_path'] = abspath(render_path)
            if report_file:
                if not hasattr(self, 'report_writer'):
                    self.report_writer = csv.DictWriter(report_file, delimiter='\t', fieldnames=sorted(row.keys(), reverse=True))
                    self.report_writer.writeheader()
                self.report_writer.writerow(row)
            if ground_truth_file:
                if not hasattr(self, 'ground_truth_writer'):
                    self.ground_truth_writer = csv.DictWriter(ground_truth_file, delimiter='\t', fieldnames=['render_path', 'is_target'])
                self.ground_truth_writer.writerow({'render_path': row['render_path'], 'is_target': is_target})

    @staticmethod
    def _get_filesnames_of_type(directory, filetypes=['stl'], ignore_path=''):
        w = walk(directory)
        for t in w:
            for filename in t[-1]:
                if not filename.startswith('.')\
                        and filename.rpartition('.')[-1] in filetypes\
                        and abspath(join(t[0], filename)) != ignore_path:
                    yield abspath(join(t[0], filename))

    @staticmethod
    def _random_point_on_sphere():
        # returns a point from a uniform distribution over the unit sphere
        length = 0.0
        while length < 0.001:
            # prevent division by zero, and overflow
            random_gaussians = np.random.normal(size=3)
            length = np.linalg.norm(random_gaussians)
        return random_gaussians/length

    def _random_rotate_object(self, obj):
        axis = self._random_point_on_sphere()
        angle = np.random.random() * 2 * np.pi
        obj.data.transform(Matrix.Rotation(angle, 4, axis))
        return {'x_axis': axis[0],
                'y_axis': axis[1],
                'z_axis': axis[2],
                'angle': angle}

    def _random_lighting(self, obj):
        pos = [-1, 0, 0]
        while pos[0] < 0:
            pos = 5 * self._random_point_on_sphere()
        self.scene.objects['Lamp'].location = pos
        return {'pos_x': pos[0],
                'pos_y': pos[1],
                'pos_z': pos[2]
                }

    def _no_transform(self, obj):
        return {}

parser = argparse.ArgumentParser(description='Generate training sets of images from 3D models')

# handle incoming blender args
_, all_arguments = parser.parse_known_args()
double_dash_index = all_arguments.index('--')
script_args = all_arguments[double_dash_index + 1:]

# define our args
parser.add_argument('target', metavar='t', type=str, help='path to target STL file')
parser.add_argument('output-dir', metavar='d', type=str, help='directory to store training set')
parser.add_argument('num-examples', metavar='n', type=int, help='number of samples to generate for each class')

parser.add_argument('--stl-directory', type=str, help='directory containing stl files, which will be searched recursively. the target stl will be ignored')
parser.add_argument('--image-directory', type=str, help='directory containing image files (will search recursively for images)')
parser.add_argument('--resolution', type=int, help='resolution of renderings (n x n)')

# random transform tags
parser.add_argument('--transforms', nargs='*', help='transforms to apply, e.g. --transforms rotate lighting randomly rotates the object and randomly positions the lighting')

# get the script args
parsed_script_args, _ = parser.parse_known_args(script_args)

# fire awaaay
args = vars(parsed_script_args)
trainer = TrainingSetGenerator(args)
trainer.run()
