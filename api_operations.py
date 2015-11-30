from three_d_match import ThreeDSearch
from shutil import copy
from elasticsearch.helpers import bulk, BulkIndexError
from os.path import join, abspath, expanduser
from os import listdir, spawnvp, P_WAIT
from image_match.signature_database import make_record
import tempfile
from shutil import rmtree
from ascribe import AscribeWrapper

# Ascribe credentials
BEARER_TOKEN = '1b26f1ab053facda3bd4263c4d102d1404d3a008'


class APIOperations(ThreeDSearch):
    def __init__(self, es_nodes=['localhost'],
                 index_name='***REMOVED***_tester',
                 artist_name='***REMOVED***',
                 cutoff=0.5):
        super(APIOperations, self).__init__(es_nodes=es_nodes,
                                            index_name=index_name,
                                            cutoff=cutoff)

        self.ascribe_wrapper = AscribeWrapper(BEARER_TOKEN)
        self.artist_name = artist_name

    def add(self, stl_id, stl_file, origin=None, doc_type='image'):
        input_directory = tempfile.mkdtemp()
        output_directory = tempfile.mkdtemp()
        try:
            copy(stl_file, input_directory)

            blender_args = ['blender',
                            '-b', '-P', 'image_match_generator.py', '--',
                            '-d', abspath(expanduser(input_directory)),
                            '-o', output_directory,
                            ]
            self.generate_images(input_directory, blender_args=blender_args)

            to_insert = []

            # ascribe the file
            piece = {
                # file upload not implemented yet...coming soon?
                'file': self._encrypt(stl_file),
                'artist_name': self.artist_name,
                'title': stl_id
            }

            ascribe_response = self.ascribe_wrapper(piece)

            for image_path in listdir(output_directory):
                if image_path.split('.')[-1] != 'csv':
                    rec = make_record(join(output_directory, image_path),
                                      self.ses.gis,
                                      self.ses.k,
                                      self.ses.N)

                    rec['ascribe_hash'] = ascribe_response['piece']['digital_work']['hash']
                    rec['ascribe_id'] = ascribe_response['piece']['digital_work']['id']
                    rec['ascribe_url'] = ascribe_response['piece']['digital_work']['url_safe']

                    rec['stl_id'] = stl_id
                    if origin:
                        rec['origin'] = origin

                    to_insert.append({
                        '_index': self.ses.index,
                        '_type': doc_type,
                        '_source': rec
                    })

            _, errs = bulk(self.es, to_insert)

        finally:
            rmtree(input_directory)
            rmtree(output_directory)

        return ascribe_response

    def _encrypt(self, stl_file):
        return stl_file

    def _decrypt(self, encrypted_stl_file):
        return encrypted_stl_file
    
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

    def render(self, stl_file=None, stl_id=None):
        input_directory = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        if stl_id:
            pass
        else:
            copy(stl_file, input_directory)
            blender_args = ['blender',
                    '-b', '-P', 'generate_images_for_humans.py', '--',
                    '-d', input_directory,
                    '-o', output_dir,
                    '--custom-name', stl_id
                    ]
            spawnvp(P_WAIT, 'blender', blender_args)
        rmtree(input_directory)
        return output_dir

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
