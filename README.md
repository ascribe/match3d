## Table of contents
- 3D Training Set Generator
- Image Match Generator

# 3D Training Set Generator
## Overview

Currently a single script used to generate training sets for matching of 3D models on images. Can output a mixure of views on the target model, as well as views on other (confusion) models. Can also include non-3D model images -- see examples below.  Please be sure to have Blender 2.7+ installed (previous versions lack numpy support).

To see the usage, use: `$ blender -b -P test_set_generator.py -- -h`

	usage: blender [-h] [--stl-directory STL_DIRECTORY]
		       [--image-directory IMAGE_DIRECTORY] [--resolution RESOLUTION]
		       [--transforms [TRANSFORMS [TRANSFORMS ...]]]
		       t d n

	Generate training sets of images from 3D models

	positional arguments:
	  t                     path to target STL file
	  d                     directory to store training set
	  n                     number of samples to generate for each class (true,
				other model, other image)

	optional arguments:
	  -h, --help            show this help message and exit
	  --stl-directory STL_DIRECTORY
				directory containing stl files, which will be searched
				recursively. the target stl will be ignored
	  --image-directory IMAGE_DIRECTORY
				directory containing image files (will search
				recursively for images)
	  --resolution RESOLUTION
				resolution of renderings (n x n)
	  --transforms [TRANSFORMS [TRANSFORMS ...]]
				transforms to apply, e.g. --transforms rotate lighting
				randomly rotates the object and randomly positions the
				lighting


ALL CALLS TO THE SCRIPT must begin with `blender -b -P test_set_generator.py --` which executes the python script as a blender script. `-b` tells blender to run in the background (no GUI) and `-P` tells it to accept a python script.  Arguments to `test_set_generator.py` go after the `--`.

## Examples

### The simplest example

A target model, output directory, and number of images is always required.  The simplest call looks e.g. like this:

```
$ blender -b -P test_set_generator.py -- ~/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045871/model.stl output/ 1
```

Where `~/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045871/model.stl` is the target file, `output/` is the output directory (it will be created if it doesn't exists) and `1` is the number of samples.

This produces rather uninteresting output: a folder `output/` containing three files:
```
$ ls output/ -1
56b2e246e5bfeb1a0ad363674d8dc6a1.0.png
ground_truth.csv
report.csv
``` 
The first file, `56b2e246e5bfeb1a0ad363674d8dc6a1.0.png` is an image derived from the model. No random transforms have been done.  The filename is an MD5 hash of the absolute path of the `.stl` with an index `.0` appended. Since we specified `n=1`, there is only one image. Opening the image might show you something like this:

![56b2e246e5bfeb1a0ad363674d8dc6a1.0.png](http://i.imgur.com/QleasvG.png)

Neat! We also get two CSVs, but let's save those for the next example.

### Random transformations

You can't do much machine learning on one example from one angle, so let's make some more:

```
blender -b -P test_set_generator.py -- ~/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045871/model.stl output/ 3 --transforms rotate lighting
```

Notice here we've changed the number of outputs from 1 to 3, and added `--transforms rotate lighting`.  `--transforms` tells which random transforms to apply.  Currently, only `rotate` and `lighting` are implemented, but we can very easily add more.

Looking at the output:
```
$ ls output/ -1
56b2e246e5bfeb1a0ad363674d8dc6a1.0.png
56b2e246e5bfeb1a0ad363674d8dc6a1.1.png
56b2e246e5bfeb1a0ad363674d8dc6a1.2.png
ground_truth.csv
report.csv
```
Looking at the output images, we can see the effect of rotation and changing lighting position.

![56b2e246e5bfeb1a0ad363674d8dc6a1.0.png](http://i.imgur.com/V2QesQS.png)
![56b2e246e5bfeb1a0ad363674d8dc6a1.1.png](http://i.imgur.com/wH5GXL4.png)
![56b2e246e5bfeb1a0ad363674d8dc6a1.2.png](http://i.imgur.com/i90kVGh.png)

Let's look at `report.csv`:
```
stl_path	render_path	_random_rotate_object_z_axis	_random_rotate_object_y_axis	_random_rotate_object_x_axis	_random_rotate_object_angle	_random_lighting_pos_z	_random_lighting_pos_y	_random_lighting_pos_x
/home/ryan/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045871/model.stl	/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.0.png	0.039725603276	-0.0966933519261	-0.994521127044	0.059562967286782724	-3.88532852678	-0.675290002655	3.0737933651
/home/ryan/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045871/model.stl	/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.1.png	-0.515433487249	-0.856211032052	-0.0350854501814	1.4480763197907711	0.0940595360946	3.79531168129	3.25373048139
/home/ryan/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045871/model.stl	/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.2.png	0.728741633166	-0.668272784427	0.14948952366	5.989241688199174	-4.62283078663	1.61107560989	1.01679442239
```
Here we have bunch of imformation about what was done, and to what, including which model and the names of the output images (note the rotation information is cumulative, I should fix it to be absolute).

We probably want to mix in some images from other models though, to confuse our models.

### A world of confusion
The script can search a target directory recursively for other `.stl` models to use.  It will ignore any files with the same absolute path as the target file.

```
 $ blender -b -P test_set_generator.py -- ~/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045871/model.stl output/ 3 --transforms rotate lighting --stl-directory ~/***REMOVED***_cad_files_for_ascribe/
```
Here I've added `--stl-directory ~/***REMOVED***_cad_files_for_ascribe/`.  This will randomly choose and render `n=3` images from all the `.stl` files under `stl-directory`.

```
$ ls output/ -1
1c7d5225645ee8c28e841c7e25a26cbe.0.png
36f1558b4ea559ec31e5fc39aff41aea.0.png
56b2e246e5bfeb1a0ad363674d8dc6a1.0.png
56b2e246e5bfeb1a0ad363674d8dc6a1.1.png
56b2e246e5bfeb1a0ad363674d8dc6a1.2.png
93dff5a8ba9f243edc1af37b820e2cd4.0.png
ground_truth.csv
report.csv
```
![files](http://i.imgur.com/wG3qjZi.png)

Note again our original images, `56b2e246e5bfeb1a0ad363674d8dc6a1.x.png` along with three new ones. If we open `ground_truth.csv`, we see two columns: image paths and labels. `1` if the image corresponds to the target, `0` if it corresponds to anything else:

```
/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.0.png	1
/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.1.png	1
/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.2.png	1
/home/ryan/PycharmProjects/3d-match/output/1c7d5225645ee8c28e841c7e25a26cbe.0.png	0
/home/ryan/PycharmProjects/3d-match/output/36f1558b4ea559ec31e5fc39aff41aea.0.png	0
/home/ryan/PycharmProjects/3d-match/output/93dff5a8ba9f243edc1af37b820e2cd4.0.png	0
```
If you increase `n` to 1000, you'll end up with a thousand views on the target model, plus a thousand views selected from amongst all the confusion models.

### Other images
You can confuse your learner further with any additional images if you like. Just add the `--image-directory` option.
```
$ blender -b -P test_set_generator.py -- ~/***REMOVED***_cad_files_for_ascribe/***REMOVED***_cad_files_for_ascribe/sn-10045871/model.stl output/ 3 --transforms rotate lighting --stl-directory ~/***REMOVED***_cad_files_for_ascribe/ --image-directory ~/oxbuild/
```
This will add some image paths to `ground_truth.csv`.  By default, the images are not copied but I plan to add a flag for that soon.
```
/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.0.png	1
/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.1.png	1
/home/ryan/PycharmProjects/3d-match/output/56b2e246e5bfeb1a0ad363674d8dc6a1.2.png	1
/home/ryan/PycharmProjects/3d-match/output/62967edd0eb31252c306aa38b539e386.0.png	0
/home/ryan/PycharmProjects/3d-match/output/4442f5db6cb69476bfe0dcbc5cd45da7.0.png	0
/home/ryan/PycharmProjects/3d-match/output/0eb8a30cf5a6f1c368018f68d314f6e9.0.png	0
/home/ryan/oxbuild/christ_church_000059.jpg	0
/home/ryan/oxbuild/oxford_000357.jpg	0
/home/ryan/oxbuild/oxford_001079.jpg	0
```

# Image Match Generator
This generates oriented images of 3D models. It can be used to match STLs based on images.

24 images are generated per model (3 eigenvectors x 2 viewing directions x 4 viewing angles)

To see usage:`$ blender -b -P image_match_generator.py -- -h`

	usage: blender [-h] [--resolution RESOLUTION] d o

	Generate oriented images for image matching

	positional arguments:
	  d                     directory containing STL files
	  o                     directory where to put images

	optional arguments:
	  -h, --help            show this help message and exit
	  --resolution RESOLUTION
				resolution of renderings (n x n)
	Error: Not freed memory blocks: 215
## Generating Images
Example usage:
```
$ blender -b -P image_match_generator.py -- -d ~/***REMOVED***_cad_files_for_ascribe/ -o test_output/
```

In addition to the images, generates a CSV `image_match_generator_report.csv` with filename, absolute path, and absolute path to the STL file.

An output filename like `5e499560c9bdd4e745f030f2c32eebb0.0.3.back.1.png` has the suffix `.0.3.back.1.png` meaning the axis of view is the zeroth eigenvector, with a three-quarters rotation, from the back, and reflected (i.e. that last 1 means reflected; it would be 0 if not reflected).

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

(Note: The following example uses the old-style output filenames, from before we included the 0/1 for reflections at the end of the filename.)

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