Generator of Images for Humans
==============================

Overview
--------
This Python Blender script produces images, one image per STL file, showing
nine renderings of the 3D object pasted into a single image as a :math:`3x3`
collage. The idea is to have one image that can give a human a good sense of
what the 3D object is. The camera positions are chosen to be fairly evenly
distributed on a sphere (not randomly).

Usage
-----

Example usage:

.. code-block:: bash

    $ blender -b -P generate_images_for_humans.py -- -d ~/Documents/ascribe/cad_files/testset1/ -o test_out_dir

The ``-d`` argument is the directory containing subdirectories which contain
STL files. All of those subdirectories will be scanned and the STL file they
contain will be rendered.

The -o argument is the output directory where all the final images will be
saved. If that directory doesn't exist yet, it will be created. Each image is
named after the parent directory of the associated STL file.

Note that we're assuming that each subdirectory contains only one STL file.
