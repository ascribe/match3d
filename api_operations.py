from three_d_match import ThreeDSearch
from shutil import copy
from elasticsearch.helpers import bulk
from os.path import join, abspath, expanduser
from os import listdir
from image_match.signature_database import make_record
import tempfile
#from generate_images_for_humans import ImagesBuilder

class APIOperations(ThreeDSearch):

    def add(self, stl_id, stl_file, origin=None, doc_type='stl_image'):
        input_directory = tempfile.mkdtemp()
        output_directory = tempfile.mkdtemp()
        copy(stl_file, input_directory)

        blender_args = ['blender',
                        '-b', '-P', 'image_match_generator.py', '--',
                        '-d', abspath(expanduser(input_directory)),
                        '-o', output_directory,
                        ]
        self.generate_images(input_directory, blender_args=blender_args)

        to_insert = []

        for image_path in listdir(output_directory):
            if image_path.split('.')[-1] != 'csv':
                rec = make_record(join(output_directory, image_path),
                                  self.ses.gis,
                                  self.ses.k,
                                  self.ses.N)

                rec['stl_id'] = stl_id
                if origin:
                    rec['origin'] = origin

                to_insert.append({
                    '_index': self.ses.index,
                    '_type': doc_type,
                    '_source': rec
                })

        _, errs = bulk(self.es, to_insert)

    def search(self, _id=None, stl_file=None):
        pass

    def render(self, _id=None, stl_file=None):
        pass
