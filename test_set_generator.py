__author__ = 'ryan'
#from mathutils import Matrix, Vector    # blender-specific classes
import bpy                          # blender-specific module

import numpy as np
import argparse

"""Blender script for generating training sets

Requires blender 2.7+
"""


class TrainingSetGenerator:
    def __init__(self, args):
        self.target_file = args.get('target')
        self.n = args.get('num-examples')
        self.output_dir = args.get('output-dir')
        # optional parameters
        self.stl_list_path = args.get('stl-list')
        self.image_list_path = args.get('image-list')

        # initialize the camera
        self.scene = bpy.data.scenes["Scene"]
        self.scene.camera.data.type = 'ORTHO'

    def set_tracking(self, obj):
        cns = self.scene.camera.constraints.new('TRACK_TO')
        cns.target = obj
        cns.track_axis = 'TRACK_NEGATIVE_Z'
        cns.up_axis = 'UP_Y'

    @staticmethod
    def _clear_scene():
        # clear scene
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.delete(use_global=False)

    @staticmethod
    def _load_stl(stl_path):
        # load stl
        bpy.ops.import_mesh.stl(filepath=path)
        bpy.ops.object.select_by_type(type='MESH')
        return bpy.context.active_object

    @staticmethod
    def _center_object(obj):
        obj.location = [0, 0, 0]
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

    @staticmethod
    def _scale_object(obj):
        factor = 3./max([x.co.magnitude for x in obj.data.vertices.values()])
        bpy.ops.transform.resize(value=(factor, factor, factor))
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

    @staticmethod
    def _random_rotate_object(obj):
        random_gaussians = np.random.normal(size=3)
        random_gaussians = random_gaussians/np.linalg.norm(random_gaussians)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate training sets of images from 3D models')
    parser.add_argument('target', metavar='t', type=str, help='path to target STL file')
    parser.add_argument('output-dir', metavar='d', type=str, help='directory to store training set')
    parser.add_argument('num-examples', metavar='n', type=int, help='number of samples to generate for each class (true, other model, other image)')

    parser.add_argument('--stl-list', type=str, help='location of list of stl paths to use, or directory containing only STL files (should not include target)')
    parser.add_argument('--image-list', type=str, help='location of list of image paths to use, or directory containing only image files (should not include target)')

    args = parser.parse_args()

    result = TrainingSetGenerator(vars(args))