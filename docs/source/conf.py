# -*- coding: utf-8 -*-

import sphinx_rtd_theme


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'match3d'
copyright = u'2016, Ryan Henderson'
author = u'Ryan Henderson'
version = u'0.0.1'
release = u'0.0.1'
language = None
exclude_patterns = []
pygments_style = 'sphinx'
todo_include_todos = True
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
htmlhelp_basename = 'match3ddoc'

latex_elements = {}
latex_documents = [
    (master_doc, 'match3d.tex', u'match3d Documentation',
     u'Ryan Henderson', 'manual'),
]

man_pages = [
    (master_doc, 'match3d', u'match3d Documentation',
     [author], 1)
]

texinfo_documents = [
    (master_doc, 'match3d', u'match3d Documentation',
     author, 'match3d', 'One line description of project.',
     'Miscellaneous'),
]

intersphinx_mapping = {'https://docs.python.org/': None}
