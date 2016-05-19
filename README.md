# match3d

`match3d` is an extension for our [image matching library](https://github.com/ascribe/image-match).
It allows you to store and search 3D models (STL files) for similar designs.

## Requirements

We hope to streamline the setup process soon. In the meantime, follow these
steps, or use [docker](#using-docker).

### image-match

You will need [image-match](https://github.com/ascribe/image-match) installed.
Follow the install directions in the link.  Along the way you will get elasticsearch
and the scientific python libraries set up.

### blender

`match3d` uses [blender](https://www.blender.org/) for rendering.  The blender packages are out-of-date
on Ubuntu 15.10, so to be safe install blender as explained [here](http://tipsonubuntu.com/2015/04/03/install-blender-2-74-ubuntu-14-04linux-mint-17/):

```sh
sudo add-apt-repository ppa:thomas-schiex/blender
sudo apt-get update
sudo apt-get install blender
```

### match3d
To install `match3d` along with its python dependencies:

```sh
pip install -e .
```

## Using Docker

Run `elasticsearch`:

```bash
$ docker-compose up -d es
```

Then to start an `ipython` session:

```bash
$ docker-compose run --rm m3d ipython
```

## Basic usage

`match3d` is essentially a collection of blender scripts for generating views of 3D models, and Python scripts
for turning those into something searchable by image-match.

### API operations

The most important functionality is provided in `api_operations.py`.

```python
from match3d.api_operations import APIOperations
api = APIOperations(index_name='3d_test')
```

`index_name` is the name of the elasticsearch index to use. Defaults to `match3d` if none is specified.

#### ADD

You can add a model from URL or local file. You must specify some kind of label either way.
Label uniqueness isn´t enforced (yet), but duplicate labels will be ignored in searches:

```python
api.add('human', stl_url='http://people.sc.fsu.edu/~jburkardt/data/stla/humanoid_tri.stl')
api.add('human_other', stl_url='http://people.sc.fsu.edu/~jburkardt/data/stla/humanoid.stl')
```

Some more example [STL files](http://www.eng.nus.edu.sg/LCEL/RP/u21/wwwroot/stl_library.htm).
For example, download and unzip the Porsche, then:

```python
api.add('porsche', stl_file='/home/ryan/Downloads/porsche.stl')
```

#### SEARCH

Search the renderings of different objects and the score of the single best view. Lower numbers are better
matches.

```python
api.search(stl_file='/home/ryan/Downloads/porsche.stl')
```

Gives the result:

```python
{'/home/ryan/Downloads/porsche.stl':
    {
        u'human_other': 0.44157460914354879,
        u'porsche': 0.0
    }
}
```

Or:

```python
api.search('http://people.sc.fsu.edu/~jburkardt/data/stla/humanoid.stl')
```

gives:

```python
{'http://people.sc.fsu.edu/~jburkardt/data/stla/humanoid.stl':
    {
        u'human': 0.13292872986279264,
        u'human_other': 0.0,
        u'porsche': 0.24738691224575407}
}
```

#### LIST
```python
api.list_designs()
```

returns

```python
[u'porsche', u'human_other', u'human']
```
