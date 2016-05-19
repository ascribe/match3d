Installation
============
We hope to streamline the setup process soon. In the meantime, you follow the
:ref:`manualsetup`, or use :ref:`usingdocker`.

.. _manualsetup:

Manual setup
------------

image-match
^^^^^^^^^^^
You will need `image-match`_ installed. Follow the install directions in the
link.  Along the way you will get elasticsearch and the scientific python
libraries set up.

blender
^^^^^^^
3D-match uses `blender`_ for rendering. The blender packages are out-of-date on
Ubuntu 15.10, so to be safe install blender as explained
`here <http://tipsonubuntu.com/2015/04/03/install-blender-2-74-ubuntu-14-04linux-mint-17/>`_:

.. code-block:: bash

    $ sudo add-apt-repository ppa:thomas-schiex/blender
    $ sudo apt-get update
    $ sudo apt-get install blender


match3d
^^^^^^^
To install ``match3d`` along with its python dependencies:

.. code-block:: bash

    $ pip install -e .


.. _usingdocker:

Using Docker
------------

Run ``elasticsearch``:

.. code-block:: bash

    $ docker-compose up -d es

Then to start an ``ipython`` session:

.. code-block:: bash

    $ docker-compose run --rm m3d ipython


.. _image-match: https://github.com/ascribe/image-match
.. _blender: https://www.blender.org/
