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

# Blender uses its own version of Python (version 3.4 as of June 2015)
# along with its own selection of Python packages which doesn't include PIL
# so I added the location of PIL on my machine to the Python path.
# Note that you need a version of PIL compatible with Python 3.4.
# I'm using the one that comes bundled with Anaconda python=3.4.
# Conda makes it easy to switch between Python 2.7 and 3.4 environments.
path_to_PIL = '/home/troy/miniconda3/envs/anapy34/lib/python3.4/site-packages'
sys.path.append(path_to_PIL)
from PIL import Image

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
        # (Use the same assumptions as Blender uses when
        #  calculating center of mass:
        #  The object is a collection of point masses.
        #  Those point masses are at the face centroids.
        #  The mass of a face = its area times its density.
        #  We can assume density=1.)
        # Those assumptions also make Ic more a property of
        # the shape than of the mesh used to digitize the shape.
        faces = obj.data.polygons
        Ic = self._inertia_matrix(faces)

        # calculate the 3 prinicipal moments of inertia (evals) and vectors on
        # the corresponding principal axes (evecs)
        evals, evecs = eig(Ic)
        evecs = evecs.T

        if report_file:
            report_writer = csv.DictWriter(report_file,
                                           fieldnames=['id', 'image_filename', 'stl_filename'])

        for eig_vec_num in range(3):
            # cycle through possible object orientations by rolling columns
            orientation = np.roll(evecs, eig_vec_num, axis=1)
            transform_matrix = Matrix(orientation).to_4x4()

            # rotate object to current choice of orientation
            obj.data.transform(transform_matrix)

            # file name = hash.eig_vec_num(0,1 or 2).camera_rotation(0,1,2 or
            # 3).front_or_back.reflection(0 or 1).png

            for direction in [1, -1]:
                cam_pos = 5 * Vector([direction, 0, 0])
                self.scene.camera.location = cam_pos
                self.scene.objects['Lamp'].location = cam_pos
                stlhash = md5(stl_name.encode('utf-8')).hexdigest()
                if direction == 1:
                    dirstr = 'front'
                else:
                    dirstr = 'back'
                path = '{}.{}.0.{}.0.png'.format(stlhash, eig_vec_num, dirstr)
                self._render_scene(join(self.output_dir, path))
                if report_file:
                    report_writer.writerow({'id': path, 'image_filename': abspath(
                        join(self.output_dir, path)), 'stl_filename': stl_name})

                # open the image file just generated,
                # then rotate and reflect it to generate some more images
                img = Image.open(abspath(join(self.output_dir, path)))

                img_rot0_ref1 = img.transpose(Image.FLIP_LEFT_RIGHT)
                path = '{}.{}.0.{}.1.png'.format(stlhash, eig_vec_num, dirstr)
                img_rot0_ref1.save(abspath(join(self.output_dir, path)))
                if report_file:
                    report_writer.writerow({'id': path, 'image_filename': abspath(
                        join(self.output_dir, path)), 'stl_filename': stl_name})

                for rot_num in [1, 2, 3]:
                    img2 = img.rotate(rot_num * 90)
                    for refl_num in [0, 1]:
                        if refl_num == 1:
                            img2 = img2.transpose(Image.FLIP_LEFT_RIGHT)
                        path = '{}.{}.{}.{}.{}.png'.format(
                            stlhash, eig_vec_num, rot_num, dirstr, refl_num)
                        img2.save(abspath(join(self.output_dir, path)))
                        if report_file:
                            report_writer.writerow({'id': path, 'image_filename': abspath(
                                join(self.output_dir, path)), 'stl_filename': stl_name})

            # rotate object back
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
        return Matrix([[0, -v[2], v[1]],
                       [v[2],    0, -v[0]],
                       [-v[1], v[0],   0]])

    @staticmethod
    def _matrix_square(M):
        # dot product is defined for blender Matrix class, but not power
        return M * M

    @classmethod
    def _inertia_matrix(cls, faces):
        # see http://en.wikipedia.org/wiki/Moment_of_inertia
        # and
        # https://www.blender.org/api/blender_python_api_2_74_release/bpy.types.MeshPolygon.html
        return reduce(add, map(lambda f: -1 * f.area * cls._matrix_square(cls._bracketB(f.center)), faces))


parser = argparse.ArgumentParser(
    description='Generate oriented images for image matching')

# handle incoming blender args
_, all_arguments = parser.parse_known_args()
double_dash_index = all_arguments.index('--')
script_args = all_arguments[double_dash_index + 1:]

# define our args
parser.add_argument('target-directory', metavar='d',
                    type=str, help='directory containing STL files')
parser.add_argument(
    'output-directory', metavar='o', type=str, help='directory where to put images')

parser.add_argument(
    '--resolution', type=int, help='resolution of renderings (n x n)')

# get the script args
parsed_script_args, _ = parser.parse_known_args(script_args)

# fire awaaay
args = vars(parsed_script_args)
trainer = ImagesBuilder(args)
trainer.run()
