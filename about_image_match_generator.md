# About Image Match Generator

Given a directory whose subdirectories contain STL files (3D models), Image Match Generator (`image_match_generator.py`) will generate a standard set of images per STL file. The images get stored in the specified output directory.

The set of images is "standard" in the sense that if one were to model the same physical object with a different mesh (a different STL file), the images generated for *it* would be roughly the same.

NOTE: Image Match Generator does *not* generate images of the reflected object (or reflected images of the object). You have to generate those afterwards (with other software). (You need the reflected versions because an object and its mirror image have the same shape.)

To see usage:`$ blender -b -P image_match_generator.py -- -h`

    usage: blender [-h] [--resolution RESOLUTION] [--no-rotations]
                   [--only-front-view]
                   d o

    Generate oriented images for image matching

    positional arguments:
      d                     directory containing STL files
      o                     directory where to put images

    optional arguments:
      -h, --help            show this help message and exit
      --resolution RESOLUTION
                            resolution of renderings (n x n)
      --no-rotations        do not generate rotations
      --only-front-view     only generate front views

## Generating Images
Example usage:
```
$ blender -b -P image_match_generator.py -- -d ~/***REMOVED***_cad_files_for_ascribe/ -o test_output/
```

In addition to the images, generates a CSV `image_match_generator_report.csv` with filename, absolute path, and absolute path to the STL file.

An output filename like `5e499560c9bdd4e745f030f2c32eebb0.0.3.back.png` has the suffix `.0.3.back.png` meaning the axis of view is the zeroth eigenvector, with a three-quarters rotation, from the back.

## Matching Images
To use the images for matching, you'll need to install our [image match library](https://bitbucket.org/ascribe/image_match), and [elasticsearch](https://www.elastic.co/guide/en/elasticsearch/guide/current/_installing_elasticsearch.html) along with the elasticsearch [python driver](https://elasticsearch-py.readthedocs.org/en/master/) and the [cairosvg package](http://cairosvg.org/).  You may also want to use the [Anaconda python distribution](http://continuum.io/downloads) if you're not already (if this sounds daunting, let me know and I can help out -- I don't know your python experience!).

Once that's all set up, you can use the image match library to build a database and search for matches.  For example, in ipython:

```
In [1]: import elasticsearch
In [2]: es = elasticsearch.Elasticsearch(['localhost']) #  use the local elasticsearch server
In [3]: from image_match.signature_database import SignatureES
In [4]: ses = SignatureES(es, index='***REMOVED***_tester') #  use any name you like here
In [5]: ses.add_images(ids_file='test_out/image_match_generator_report.csv') #  using the csv -- will take some seconds
In [6]: es.count(index='***REMOVED***_tester') #  see that your inserts were sucessful
Out[6]: {u'_shards': {u'failed': 0, u'successful': 5, u'total': 5}, u'count': 1992}
```

Now you can test one of the images -- here I just picked one from the files we generated.  In general, you would search over all views and somehow make a composite score (coming soon!)

```
In [7]: s = ses.parallel_find('test_out/5e499560c9bdd4e745f030f2c32eebb0.2.3.back.png', n_parallel_words=63)  # generate an iterator for searching
In [8]: s.next()  # find matches
Out[8]: 
[{'dist': 0.46437469606956266,
  'id': u'AU3DDxTKYh8lR23XVhKR',
  'path': u'/home/ryan/oxbuild/all_souls_000013.jpg'},
 {'dist': 0.0,
  'id': u'5e499560c9bdd4e745f030f2c32eebb0.2.3.back.png',
  'path': u'/home/ryan/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045852/model.stl'},
 {'dist': 0.49960623511077062,
  'id': u'6b335604cafe26f55da7bc7384dd211b.0.3.front.png',
  'path': u'/home/ryan/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045896/model.stl'}]

```

Note the one exact match -- `{'dist': 0.0, ...` -- along with a couple distant matches (apparently I put some images from another directory in this index).
