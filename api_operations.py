from three_d_match import ThreeDSearch
from shutil import copy
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError
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

        self.index_name = index_name

        # the parent class provides the methods for rendering in blender
        super(APIOperations, self).__init__(es_nodes=es_nodes,
                                            index_name=index_name,
                                            cutoff=cutoff)

        # ascribe object, set ASCRIBE_TOKEN in .env
        self.ascribe_wrapper = AscribeWrapper()
        self.artist_name = artist_name

        # encryption goodies. set STILNEST_PGP_FINGERPRINT in .env, or pass it at instantiation
        if pgp_fingerprint:
            self.pgp_fingerprint = pgp_fingerprint
        else:
            self.pgp_fingerprint = getenv('STILNEST_PGP_FINGERPRINT')

        self.gpg = gnupg.GPG()

        # set up AWS s3 connection, credentials and region read from environment variables
        self.conn = S3Connection(host='s3.eu-central-1.amazonaws.com')

        # the 'get_bucket' by name function doesn't work in eu-central-1, this is a workaround
        self.bucket = [x for x in self.conn.get_all_buckets() if x.name == bucket_name][0]

    """
    The following methods -- add, search, render, search_web -- form the basis of the API, and meeting
    the terms of the Stilnest MOU.
    """

    def add(self, stl_id, stl_url=None, stl_file=None, origin=None, doc_type='image'):
        """
        Add an STL to Ascribe and add renders to an elasticsearch database for matching

        :param stl_id: an identifier for the STL file. must be unique.
        :param stl_url: the PUBLIC url pointing to the STL file (optional)
        :param stl_file: path to an STL file. ignored if stl_url is provided, but one must be given (optional)
        :param origin: specify an origin, mainly for bookkeeping (optional)
        :param doc_type: specify the doc_type for elasticsearch renders. You shouldn't need to change this
        :return: the response from Ascribe, or None if the stl_id already exists
        """
        # check if stl_id exists, and add nothing if it does
        try:
            if self._ascribe_id_from_***REMOVED***_id(stl_id):
                return None
        except NotFoundError:
            # No index setup yet, so no duplicates possible!
            pass

        # set up temporary directories
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

            # add image signatures to elasticsearch
            for image_path in listdir(output_directory):
                # ignore the .csv report generated by the renderer
                if image_path.split('.')[-1] != 'csv':
                    rec = make_record(join(output_directory, image_path),
                                      self.ses.gis,
                                      self.ses.k,
                                      self.ses.N)

                    # include some ascribe metadata
                    rec['ascribe_bitcoin_id'] = ascribe_response['piece']['bitcoin_id']
                    rec['ascribe_id'] = ascribe_response['piece']['id']
                    rec['ascribe_url'] = ascribe_response['piece']['digital_work']['url']

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
            # clean up temporary locations
            rmtree(input_directory)
            rmtree(output_directory)
            remove(temporary_stl)

        return ascribe_response

    def search(self, stl_id=None, stl_file=None, return_raw=False, ranking='single'):
        """
        Search by ID or STL file for similar designs
        :param stl_id: an identifier for the STL file. Will attempt to download STL file from ascribe (optional)
        :param stl_file: path to an STL file. ignored if stl_id is provided, but you must provide one of the two (optional)
        :param return_raw: if True, return raw scores per image instead of a composite score (default False)
        :param ranking: ranking system to use. No need to changes this
        :return: list of matches, or None
        """
        # TODO: include origin field
        try:
            input_directory = tempfile.mkdtemp()
            temporary_stl = tempfile.mkstemp(suffix='.stl')[-1]

            # download and decrypt
            if stl_id:
                with open(temporary_stl, 'wb') as f:
                    f.write(self._download_and_decrypt(stl_id))
                    stl_file = temporary_stl

            copy(stl_file, input_directory)
            images_directory = self.generate_images(input_directory)
            res = self.search_images(images_directory)
        finally:
            rmtree(input_directory)
            rmtree(images_directory)
        if return_raw:
            return res
        elif ranking == 'single':
            return {stl_file: self._best_single_image(res)}

    def render(self, stl_file=None, stl_id=None):
        """
        Return a nice rendering. If an stl_id is provided, pull from ascribe,
        otherwise stl_file must be specified
        :param stl_file:
        :param stl_id:
        :return: temp directory location containing rendering
        """
        try:
            # set up temporary files
            input_directory = tempfile.mkdtemp()
            output_dir = tempfile.mkdtemp()
            temporary_stl = tempfile.mkstemp(suffix='.stl')[-1]

            # download and decrypt
            if stl_id:
                with open(temporary_stl, 'wb') as f:
                    f.write(self._download_and_decrypt(stl_id))
                    stl_file = temporary_stl

            copy(stl_file, input_directory)

            # render here
            blender_args = ['blender',
                    '-b', '-P', 'generate_images_for_humans.py', '--',
                    '-d', input_directory,
                    '-o', output_dir,
                    '--custom-name', stl_id
                    ]
            spawnvp(P_WAIT, 'blender', blender_args)

        finally:
            # clean up
            rmtree(input_directory)
            remove(temporary_stl)

        return output_dir

    def search_web(self, stl_id):
        raise NotImplementedError

    def _ascribe_id_from_***REMOVED***_id(self, stl_id):
        # given a ***REMOVED*** ID, get the ascribe ID from the elasticsearch db
        r = self.es.search(index=self.index_name,
                      body={'query': {'match': {'stl_id': stl_id}}},
                      fields=['ascribe_id'], size=1)
        if r['hits']['total'] > 0:
            return r['hits']['hits'][0]['fields']['ascribe_id'][0]
        else:
            # if no matching ID is found, return none
            return None

    def _download_and_decrypt(self, stl_id):
        # pull an encrypted file from ascribe BY STILNEST ID, and return the decrypted data
        _id = self._ascribe_id_from_***REMOVED***_id(stl_id)
        res = self.ascribe_wrapper.retrieve_piece(_id)
        content = requests.get(res['piece']['digital_work']['url'])
        return self.gpg.decrypt(content.content).data

    def _best_single_image(self, results, n_per_view=5):
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
