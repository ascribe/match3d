"""Generate images showing renderings of 3D models from multiple viewpoints
to enable humans to compare 3D models.
"""

import sys
sys.path.append('.')
from blenderbase import BlenderBase

from os import walk, remove, mkdir
from os.path import join, abspath, sep

# Blender uses its own version of Python (version 3.4 as of June 2015)
# along with its own selection of Python packages which doesn't include PIL
# so I added the location of PIL on my machine to the Python path.
# Note that you need a version of PIL compatible with Python 3.4.
# I'm using the one that comes bundled with Anaconda python=3.4.
# Conda makes it easy to switch between Python 2.7 and 3.4 environments.
path_to_PIL = '/home/troy/miniconda3/envs/anapy34/lib/python3.4/site-packages'
sys.path.append(path_to_PIL)
from PIL import Image

from math import cos, sin, sqrt
import argparse


class ImagesBuilder(BlenderBase):

    def __init__(self, args):
        self.target_dir = abspath(args['target-directory'])
        self.output_dir = abspath(args['output-directory'])
        # Set subimage resolution = 256 pixels (hardwired).
        # For some reason, I only get 256 if I put double that
        # as the argument for __init__
        self.sub_res = 116
        super(ImagesBuilder, self).__init__(2 * self.sub_res)

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
        for stl_name in self._get_filesnames_of_type(self.target_dir):
            self.generate_image(stl_name)

    def generate_image(self, stl_name):
        self._clear_scene()
        obj = self._load_stl(stl_name)
        self._center_object(obj)
        self._scale_object(obj)
        self._set_tracking(obj)
        self._set_background_colors('white')

        side_len = 3 * self.sub_res  # 3 x subimage resolution
        final_img = Image.new('RGB', (side_len, side_len))

        # Variables associated with generating the points on the sphere
        # https://stackoverflow.com/questions/9600801/evenly-distributing-n-points-on-a-sphere
        numpoints = 9
        dlon = 2.399963230  # radians
        dz = 2.0/numpoints
        lon = 0.0
        z = 1.0 - dz/2.0
        cam_dist = 5.0

        for y_index in range(3):
            for x_index in range(3):
                # Compute the camera position
                r = sqrt(1.0 - z*z)
                x_cam = cam_dist * r * cos(lon)
                y_cam = cam_dist * r * sin(lon)
                z_cam = cam_dist * z
                camera_pos = (x_cam, y_cam, z_cam)

                # Set the camera and lamp positions
                self.scene.camera.location = camera_pos
                self.scene.objects['Lamp'].location = camera_pos

                # Render the view to a temp file
                temp_path = './temp.png'
                self._render_scene(temp_path)

                # Open the just-written temp image file using PIL
                temp_img = Image.open(temp_path)

                # Paste the temp image into the final image.
                # Note that in PIL, x increases from left to right
                # and y increases from top to bottom.
                paste_x = x_index * self.sub_res
                paste_y = y_index * self.sub_res
                final_img.paste(temp_img, (paste_x, paste_y))

                # Delete the temp image file
                remove(temp_path)

                # Update variables used to calculate the camera position
                z = z - dz
                lon = lon + dlon

        # Save the final image to the output directory.
        # Name the image file after its parent directory.
        parent_dir_name = stl_name.rsplit(sep, 2)[1]
        final_img_fname = parent_dir_name + '.png'
        final_img_path = join(self.output_dir, final_img_fname)
        final_img.save(final_img_path)

    @staticmethod
    def _get_filesnames_of_type(directory, filetypes=['stl'], ignore_path=''):
        w = walk(directory)
        for t in w:
            for filename in t[-1]:
                if not filename.startswith('.')\
                        and filename.rpartition('.')[-1] in filetypes\
                        and abspath(join(t[0], filename)) != ignore_path:
                    yield abspath(join(t[0], filename))


parser = argparse.ArgumentParser(
    description='Generate multi-view images of 3D objects for humans')

# handle incoming blender args
_, all_arguments = parser.parse_known_args()
double_dash_index = all_arguments.index('--')
script_args = all_arguments[double_dash_index + 1:]

# define our args
parser.add_argument('target-directory', metavar='d',
                    type=str,
                    help='directory containing directories containing STL files')
parser.add_argument('output-directory', metavar='o',
                    type=str,
                    help='directory where images will be written')

# get the script args and run
parsed_script_args, _ = parser.parse_known_args(script_args)
args = vars(parsed_script_args)
builder = ImagesBuilder(args)
builder.run()
