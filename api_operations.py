from three_d_match import ThreeDSearch
from shutil import copy
from elasticsearch.helpers import bulk
from os.path import join, abspath, expanduser
from os import listdir, rmdir
from image_match.signature_database import make_record
import tempfile
from shutil import rmtree

#from generate_images_for_humans import ImagesBuilder

class APIOperations(ThreeDSearch):

    def add(self, stl_id, stl_file, origin=None, doc_type='image'):
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
        rmtree(input_directory)
        rmtree(output_directory)

    def search(self, stl_file=None, return_raw=False, ranking='single'):
        # TODO: include origin field
        input_directory = tempfile.mkdtemp()
        copy(stl_file, input_directory)
        images_directory = self.generate_images(input_directory)
        res = self.search_images(images_directory)
        rmtree(input_directory)
        rmtree(images_directory)
        if return_raw:
            return res
        elif ranking == 'single':
            return {stl_file: self.best_single_image(res)}

    def render(self, _id=None, stl_file=None):
        pass

    def best_single_image(self, results, n_per_view=5):
        scores = {}
        for result in results:
            for i in range(n_per_view):
                if result:
                    best = min(result, key=lambda x: x['dist'])
                    k = self.es.get(id=best['id'], index=self.ses.index, doc_type='image',
                                         fields=['stl_id'])['fields']['stl_id'][0]
                    if k not in scores:
                        scores[k] = best['dist']
                    elif best['dist'] < scores[k]:
                        scores[k] = best['dist']
                    result.remove(best)
        return scores