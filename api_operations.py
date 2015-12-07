from three_d_match import ThreeDSearch
from shutil import copy
from elasticsearch.helpers import bulk, BulkIndexError
from os.path import join, abspath, expanduser
from os import listdir, spawnvp, P_WAIT, getenv, remove
from image_match.signature_database import make_record
import tempfile
from shutil import rmtree
from ascribe import AscribeWrapper
from boto.s3.connection import S3Connection
from boto.s3.key import Key
import requests
import gnupg


class APIOperations(ThreeDSearch):
    def __init__(self, es_nodes=['localhost'],
                 index_name='***REMOVED***_tester',
                 artist_name='***REMOVED***',
                 cutoff=0.5,
                 pgp_fingerprint=None,
                 bucket_name='***REMOVED***'):
        super(APIOperations, self).__init__(es_nodes=es_nodes,
                                            index_name=index_name,
                                            cutoff=cutoff)

        self.ascribe_wrapper = AscribeWrapper()
        self.artist_name = artist_name

        if pgp_fingerprint:
            self.pgp_fingerprint = pgp_fingerprint
        else:
            self.pgp_fingerprint = getenv('STILNEST_PGP_FINGERPRINT')

        self.gpg = gnupg.GPG()

        self.conn = S3Connection(host='s3.eu-central-1.amazonaws.com')

        # the 'get_bucket' by name function doesn't work in eu-central-1, this is a workaround
        self.bucket = [x for x in self.conn.get_all_buckets() if x.name == bucket_name][0]

    def add(self, stl_id, stl_url=None, stl_file=None, origin=None, doc_type='image'):
        input_directory = tempfile.mkdtemp()
        output_directory = tempfile.mkdtemp()
        temporary_stl = tempfile.mkstemp(suffix='.stl')[-1]

        # TODO: many of these functions should be parallelized
        try:
            # if a url is supplied, attempt to download the STL
            if stl_url:
                r = requests.get(stl_url)
                with open(temporary_stl, 'wb') as f:
                    f.write(r.content)
                stl_file = temporary_stl

            # copy the supplied stl file or requested data to a temp dir
            copy(stl_file, input_directory)
            path = join(input_directory, stl_file)

            # set up and run the rendering process. fork and wait for completion
            blender_args = ['blender',
                            '-b', '-P', 'image_match_generator.py', '--',
                            '-d', abspath(expanduser(input_directory)),
                            '-o', output_directory,
                            ]

            self.generate_images(input_directory, blender_args=blender_args)

            # encrypt the file, if possible
            with open(path, 'rb') as f:
                encrypted_ascii_data = self.gpg.encrypt_file(f, self.pgp_fingerprint)

            # upload encrypted file to S3
            k = Key(self.bucket)
            k.key = stl_id
            k.set_contents_from_string(encrypted_ascii_data.data)
            k.set_acl('public-read')
            url = 'https://{host}/{bucket}/{key}'.format(host=self.conn.server_name(),
                                                         bucket=self.bucket.name,
                                                         key=k.name)
            to_insert = []

            # ascribe the file
            piece = {
                'file_url': url,
                'artist_name': self.artist_name,
                'title': stl_id
            }

            ascribe_response = self.ascribe_wrapper.create_piece(piece)

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
            remove(temporary_stl)

        return ascribe_response

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
