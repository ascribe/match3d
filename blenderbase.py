"""Base class for blender operations

"""
__author__ = 'ryan'

import bpy  # blender-specific module
from mathutils import Matrix, Vector    # blender-specific classes
import numpy as np


class BlenderBase():
    def __init__(self, resolution):
        # initialize the camera
        self.scene = bpy.data.scenes["Scene"]
        self.scene.camera.data.type = 'ORTHO'
        self.scene.camera.location = 5 * Vector([1, 0, 0])

        # render resolution
        # If you want the final rendered image to be N x N pixels,
        # then you need to set resolution_x=2*N and resolution_y=2*N.
        # Why? That's not so clear. But it works.
        self.scene.render.resolution_x = 2 * resolution
        self.scene.render.resolution_y = 2 * resolution

        # turning off raytracing can greatly speed up the non-parallel parts of rendering
        self.scene.render.use_raytrace = False

    def _set_tracking(self, obj):
        cns = self.scene.camera.constraints.new('TRACK_TO')
        cns.target = obj
        cns.track_axis = 'TRACK_NEGATIVE_Z'
        cns.up_axis = 'UP_Y'

    @staticmethod
    def _set_background_colors(colors_string):
        scn = bpy.context.scene
        if colors_string == 'white':
            scn.world.horizon_color = (1.0, 1.0, 1.0)

    @staticmethod
    def _clear_scene():
        # clear scene
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_by_type(type='MESH')
        bpy.ops.object.delete(use_global=False)

    @staticmethod
    def _load_stl(stl_path):
        # load stl
        bpy.ops.import_mesh.stl(filepath=stl_path)
        bpy.ops.object.select_by_type(type='MESH')
        return bpy.context.active_object

    @staticmethod
    def _center_object(obj):
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
        obj.location = [0, 0, 0]

    @staticmethod
    def _scale_object(obj):
        factor = 3/max([np.linalg.norm(x.co) for x in obj.data.vertices.values()])
        bpy.ops.transform.resize(value=(factor, factor, factor))
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')

    @staticmethod
    def _render_scene(path):
        bpy.data.scenes["Scene"].render.filepath = path
        bpy.ops.render.render(write_still=True)