"""
match33d is an extension for our
`image matching library <https://github.com/ascribe/image-match>`_.

It allows you to store and search 3D models (STL files) for similar designs.

"""
import io
import os
import re

from setuptools import setup, find_packages


def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r'^__version__ = [\'"]([^\'"]*)[\'"]', version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


tests_require = [
    'coverage',
    'pep8',
    'pyflakes',
    'pylint',
    'pytest',
    'pytest-cov',
    'pytest-xdist',
]

dev_require = [
    'ipdb',
    'ipython',
]

docs_require = [
    'recommonmark>=0.4.0',
    'Sphinx>=1.3.5',
    'sphinxcontrib-napoleon>=0.4.4',
    'sphinx-rtd-theme>=0.1.9',
]


setup(
    name='match3d',
    version=find_version('match3d', '__init__.py'),
    description=('match3d allows you to store and search 3D models (STL files)'
                 'for similar designs.'),
    long_description=__doc__,
    url='https://github.com/ascribe/3dmatch/',
    author='Ryan Henderson',
    author_email='ryan@ascribe.io',
    license='Apache License 2.0',
    zip_safe=True,

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Database',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Software Development',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Topic :: Multimedia :: Graphics',
    ],

    packages=find_packages(),

    setup_requires=[
        'pytest-runner',
    ],
    install_requires=[
        'image_match',
        'requests',
    ],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        'dev':  dev_require + tests_require + docs_require,
        'docs':  docs_require,
    },
)
