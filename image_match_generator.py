"""Generates oriented images for matching models based on images

"""

# put modules in path
import sys
sys.path.append('.')
sys.path.append('./hidden_PIL/')

from blenderbase import BlenderBase
from mathutils import Matrix, Vector    # blender-specific classes

from functools import reduce
from operator import add
from os import mkdir, walk
from hashlib import md5
from os.path import join, abspath, basename
from numpy.linalg import eig
from numpy import roll, pi
# Note: Be sure to use a version of PIL that works with Python 3
# (which is the version of Python that Blender uses)
from PIL import Image

import argparse
import csv

__author__ = 'Ryan Henderson and Troy McConaghy'


class ImagesBuilder(BlenderBase):
    def __init__(self, args):
        self.output_dir = abspath(args['output-directory'])
        self.target_dir = abspath(args['target-directory'])

        resolution = args.get('resolution')
        if not resolution:
            resolution = 1024

        self.all_rotations = args.get('all_rotations')
        self.front_and_back = args.get('front_and_back')
        self.all_reflections = args.get('all_reflections')
        self.use_img_trans = args.get('use_img_trans')

        # initialize some camera settings
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
                self.generate_images(stl_name,
                                     report_file=report_file,
                                     rotations=self.all_rotations,
                                     front_and_back=self.front_and_back)

    def generate_images(self, stl_name, report_file=None,
                        rotations=True, front_and_back=True):
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

        # calculate the 3 prinicipal moments of inertia (evals)
        # and vectors on the corresponding principal axes (evecs)
        evals, evecs = eig(Ic)
        evecs = evecs.T

        # reflection matrix
        # i.e. flip the sign of all y-coordinates
        # = reflection in the x-z plane
        refl_matrix = Matrix([[1,  0, 0, 0],
                              [0, -1, 0, 0],
                              [0,  0, 1, 0],
                              [0,  0, 0, 1]])

        stlhash = md5(stl_name.encode('utf-8')).hexdigest()

        if report_file:
            report_writer = csv.DictWriter(report_file,
                                           fieldnames=['id', 'image_filename',
                                                       'stl_filename'])

        for eig_vec_num in [0, 1, 2]:
            # cycle through possible orientations by rolling columns
            orientation = roll(evecs, eig_vec_num, axis=1)
            transform_matrix = Matrix(orientation).to_4x4()

            # rotate object to current choice of orientation
            obj.data.transform(transform_matrix)

            direction_list = [1, -1] if self.front_and_back else [1]
            for direction in direction_list:
                dirstr = 'front' if direction == 1 else 'back'
                rot_list = [0, 1, 2, 3] if self.all_rotations else [0]
                for rot_num in rot_list:
                    refl_list = [0, 1] if self.all_reflections else [0]
                    for refl_num in refl_list:
                        img_filename = '{}.{}.{}.{}.{}.png'.format(
                            stlhash, eig_vec_num, rot_num, dirstr, refl_num)
                        img_path = abspath(join(self.output_dir, img_filename))

                        if ((rot_num == 0) and (refl_num == 0)):
                            # render the image
                            cam_pos = 5 * Vector([direction, 0, 0])
                            self.scene.camera.location = cam_pos
                            self.scene.objects['Lamp'].location = cam_pos
                            self._render_scene(img_path)
                        else:
                            if self.use_img_trans:
                                # generate the image by rotating and/or
                                # reflecting a previously-rendered image
                                old_img_fn = '{}.{}.0.{}.0.png'.format(stlhash,
                                                                       eig_vec_num,
                                                                       dirstr)
                                old_img_path = abspath(join(self.output_dir,
                                                            old_img_fn))
                                old_img = Image.open(old_img_path)
                                new_img = old_img
                                if rot_num > 0:
                                    new_img = new_img.rotate(rot_num * 90)
                                if refl_num > 0:
                                    opcode = Image.FLIP_LEFT_RIGHT
                                    new_img = new_img.transpose(opcode)
                                new_img.save(img_path)
                            else:
                                # first rotate and/or reflect the object,
                                # then render an image of it
                                if rot_num > 0:
                                    rot_angle = 2.0 * pi * float(rot_num) / 4.0
                                    obj.data.transform(Matrix.Rotation(
                                                       rot_angle,
                                                       4, [direction, 0, 0]))
                                if refl_num > 0:
                                    obj.data.transform(refl_matrix)
                                # render the image
                                cam_pos = 5 * Vector([direction, 0, 0])
                                self.scene.camera.location = cam_pos
                                self.scene.objects['Lamp'].location = cam_pos
                                self._render_scene(img_path)
                                # undo any object rotation or reflection
                                if refl_num > 0:
                                    obj.data.transform(refl_matrix)
                                if rot_num > 0:
                                    obj.data.transform(Matrix.Rotation(
                                                       -rot_angle,
                                                       4, [direction, 0, 0]))

                        if report_file:
                            report_writer.writerow({'id': img_filename,
                                                    'image_filename': img_path,
                                                    'stl_filename': stl_name})

            # Rotate object back to the way was originally.
            # Could do transform_matrix.invert() but the
            # inverse of a rotation matrix is its transpose:
            transform_matrix.transpose()
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
        # see http://en.wikipedia.org/wiki/Moment_of_inertia and
        # www.blender.org/api/blender_python_api_2_74_release/bpy.types.MeshPolygon.html
        return reduce(add, map(lambda f: -1 * f.area * cls._matrix_square(cls._bracketB(f.center)), faces))


parser = argparse.ArgumentParser(description='Generate oriented images for image matching')

# handle incoming blender args
_, all_arguments = parser.parse_known_args()
double_dash_index = all_arguments.index('--')
script_args = all_arguments[double_dash_index + 1:]

# define our args
# positional args
parser.add_argument('target-directory', metavar='d', type=str,
                    help='directory containing STL files')
parser.add_argument('output-directory', metavar='o', type=str,
                    help='directory where to put images')
# optional args
parser.add_argument('--resolution', type=int,
                    help='resolution of renderings (n x n)')
parser.add_argument('--no-rotations', dest='all_rotations',
                    help='do not generate rotations', action='store_false')
parser.add_argument('--only-front-view', dest='front_and_back',
                    help='only generate front views', action='store_false')
parser.add_argument('--no-reflections', dest='all_reflections',
                    help='do not generate reflections', action='store_false')
parser.add_argument('--no-image-transforms', dest='use_img_trans',
                    help='generate all images by rendering',
                    action='store_false')

parser.set_defaults(all_rotations=True)
parser.set_defaults(front_and_back=True)
parser.set_defaults(all_reflections=True)
parser.set_defaults(use_img_trans=True)

# get the script args
parsed_script_args, _ = parser.parse_known_args(script_args)

# generate the images
args = vars(parsed_script_args)
builder = ImagesBuilder(args)
builder.run()
