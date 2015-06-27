"""Generates oriented images for matching models based on images

"""

__author__ = 'ryan'

# put modules in path
import sys
sys.path.append('.')
from blenderbase import BlenderBase
from mathutils import Matrix, Vector    # blender-specific classes

from functools import reduce
from operator import add
from os import mkdir, walk
from hashlib import md5
from os.path import join, abspath, basename
from numpy.linalg import eig

import numpy as np
import argparse
import csv


class ImagesBuilder(BlenderBase):
    def __init__(self, args):
        self.output_dir = abspath(args['output-directory'])
        self.target_dir = abspath(args['target-directory'])
        resolution = args.get('resolution')
        if not resolution:
            resolution = 1024
        super(ImagesBuilder, self).__init__(resolution)
        self.scene.objects['Lamp'].location = 5 * Vector([1, 0, 0])

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
        with open(join(self.output_dir, 'image_match_generator_report.csv'), 'w') as report_file:
            for stl_name in self._get_filesnames_of_type(self.target_dir):
                self.generate_images(stl_name, report_file=report_file)

    def generate_images(self, stl_name, report_file=None):
        self._clear_scene()
        obj = self._load_stl(stl_name)
        self._center_object(obj)
        self._scale_object(obj)
        self._set_tracking(obj)

        # calculate the moment of inertia matrix Ic
        # (Use the same assumptions as Blender uses when calculating center of mass:
        # The object is a collection of point masses. Those point masses are at the face centroids.
        # The mass of a face = its area times its density. We can assume density=1.)
		# Those assumptions also make Ic more a property of the shape than of the mesh used to digitize the shape.
        faces = obj.data.polygons
        Ic = self._inertia_matrix(faces)

        # calculate the 3 prinicipal moments of inertia (evals) and vectors on the corresponding principal axes (evecs)
        evals, evecs = eig(Ic)
        evecs = evecs.T

        if report_file:
            report_writer = csv.DictWriter(report_file,
                                           fieldnames=['id', 'image_filename', 'stl_filename'])

        for eig_vec_num in range(3):
            # cycle through possible orientations by rolling columns
            orientation = np.roll(evecs, eig_vec_num, axis=1)
            transform_matrix = Matrix(orientation).to_4x4()

            # rotate object to principal axes
            obj.data.transform(transform_matrix)

            # render for +/- each eigenvector and include every 90deg rotation
            for i, radian in enumerate(2 * np.pi * np.arange(4) / 4.0):
                obj.data.transform(Matrix.Rotation(radian, 4, [1, 0, 0]))
                self.scene.objects['Lamp'].location = 5 * Vector([1, 0, 0])
                self.scene.camera.location = 5 * Vector([1, 0, 0])
                path = '{}.{}.{}.front.png'.format(md5(stl_name.encode('utf-8')).hexdigest(), eig_vec_num, i)
                self._render_scene(join(self.output_dir, path))
                if report_file:
                    report_writer.writerow({'id': path, 'image_filename': abspath(join(self.output_dir, path)), 'stl_filename': stl_name})
                self.scene.objects['Lamp'].location = 5 * Vector([-1, 0, 0])
                self.scene.camera.location = 5 * Vector([-1, 0, 0])
                path = '{}.{}.{}.back.png'.format(md5(stl_name.encode('utf-8')).hexdigest(), eig_vec_num, i)
                self._render_scene(join(self.output_dir, path))
                if report_file:
                    report_writer.writerow({'id': path, 'image_filename': abspath(join(self.output_dir, path)), 'stl_filename': stl_name})
                obj.data.transform(Matrix.Rotation(-radian, 4, [1, 0, 0]))

            # rotate back
            transform_matrix.invert()
            obj.data.transform(transform_matrix)

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
    def _bracketB(v):
        return Matrix([[    0, -v[2], v[1]],
                        [v[2],    0, -v[0]],
                        [-v[1], v[0],   0]])

    @staticmethod
    def _matrix_square(M):
        # dot product is defined for blender Matrix class, but not power
        return M * M

    @classmethod
    def _inertia_matrix(cls, faces):
        # see http://en.wikipedia.org/wiki/Moment_of_inertia
        # and https://www.blender.org/api/blender_python_api_2_74_release/bpy.types.MeshPolygon.html
        return reduce(add, map(lambda f: -1 * f.area * cls._matrix_square(cls._bracketB(f.center)), faces))



parser = argparse.ArgumentParser(description='Generate oriented images for image matching')

# handle incoming blender args
_, all_arguments = parser.parse_known_args()
double_dash_index = all_arguments.index('--')
script_args = all_arguments[double_dash_index + 1:]

# define our args
parser.add_argument('target-directory', metavar='d', type=str, help='directory containing STL files')
parser.add_argument('output-directory', metavar='o', type=str, help='directory where to put images')

parser.add_argument('--resolution', type=int, help='resolution of renderings (n x n)')

# get the script args
parsed_script_args, _ = parser.parse_known_args(script_args)

# fire awaaay
args = vars(parsed_script_args)
trainer = ImagesBuilder(args)
trainer.run()