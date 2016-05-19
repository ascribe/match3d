Basic usage
===========
``match3d`` is essentially a collection of blender scripts for generating views
of 3D models, and Python scripts for turning those into something searchable by
``image-match``.

API operations
--------------
The most important functionality is provided in ``api_operations.py``.

.. code-block:: python

    from match3d.api_operations import APIOperations
    api = APIOperations(index_name='3d_test')

``index_name`` is the name of the elasticsearch index to use. Defaults to
``match3d`` if none is specified.


ADD
^^^
You can add a model from URL or local file. You must specify some kind of label
either way. Label uniqueness isn´t enforced (yet), but duplicate labels will be
ignored in searches:

.. code-block:: python

    api.add('human', stl_url='http://people.sc.fsu.edu/~jburkardt/data/stla/humanoid_tri.stl')
    api.add('human_other', stl_url='http://people.sc.fsu.edu/~jburkardt/data/stla/humanoid.stl')

Some more example `STL files`_. For example, download and unzip the Porsche,
then:

.. code-block:: python

    api.add('porsche', stl_file='/home/ryan/Downloads/porsche.stl')


SEARCH
^^^^^^

Search the renderings of different objects and the score of the single best
view. Lower numbers are better matches.

.. code-block:: python
    
    api.search(stl_file='/home/ryan/Downloads/porsche.stl')

Gives the result:

.. code-block:: python
    
    {'/home/ryan/Downloads/porsche.stl':
        {
            u'human_other': 0.44157460914354879,
            u'porsche': 0.0
        }
    }

Or:

.. code-block:: python
    
    api.search('http://people.sc.fsu.edu/~jburkardt/data/stla/humanoid.stl')

gives:

.. code-block:: python
    
    {'http://people.sc.fsu.edu/~jburkardt/data/stla/humanoid.stl':
        {
            u'human': 0.13292872986279264,
            u'human_other': 0.0,
            u'porsche': 0.24738691224575407}
    }


LIST
^^^^

.. code-block:: python
    
    api.list_designs()

returns

.. code-block:: python

    [u'porsche', u'human_other', u'human']

    
.. _STL files: http://www.eng.nus.edu.sg/LCEL/RP/u21/wwwroot/stl_library.htm
