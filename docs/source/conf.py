#!/usr/bin/env python3

# -- Path configuration ------------------------------------------------

import sys
from os import path
from trojanzoo_sphinx_theme.linkcode import linkcode_helper

sys.path.insert(0, path.abspath('./'))
sys.path.insert(0, path.abspath('../../'))

import trojanzoo as package  # noqa

pkg_name = package.__name__
pkg_file = package.__file__
pkg_version = str(package.__version__)
pkg_location = path.dirname(path.dirname(pkg_file))

autoapi_dirs = ['../../trojanzoo']

# -- General configuration ------------------------------------------------

project = 'TrojanZoo'
author = 'ain-soph'
copyright = f'2021, {author}'

github_user = author
github_repo = pkg_name
github_version = 'main'

github_url = f'https://github.com/{github_user}/{github_repo}/'
gh_page_url = f'https://{github_user}.github.io/{github_repo}/'

html_baseurl = gh_page_url
html_context = {
    'display_github': True,
    'github_user': github_user,
    'github_repo': github_repo,
    'github_version': github_version,
    "conf_py_path": "/docs/source/",  # Path in the checkout to the docs root
}
html_theme_options = {
    'github_url': github_url,

    'doc_items': {
        'AlpsPlot': '/alpsplot',
        'TrojanZoo': '/trojanzoo',
        'trojanzoo_sphinx_theme': '/trojanzoo_sphinx_theme',
        'base': 'https://github.com/ain-soph/base',
    },

    'logo': 'images/logo/trojanzoo-logo.svg',
    'logo_dark': 'images/logo/trojanzoo-logo-dark.svg',
    'logo_icon': 'images/logo/trojanzoo-logo-icon.svg',
}

# -- Extension configuration ----------------------------------------------

extensions = [
    # 'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.githubpages',
    'sphinx.ext.intersphinx',
    'sphinx.ext.linkcode',  # viewcode
    'sphinx.ext.napoleon',
    'sphinxcontrib.katex',
    'sphinx_copybutton',
    'autoapi.extension',
]


def linkcode_resolve(domain, info):
    return linkcode_helper(
        domain, info,
        prefix=pkg_location,
        github_url=github_url,
        github_version=github_version)


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable', None),
    'torch': ('https://pytorch.org/docs/stable/', None),
}

# -- General default configuration ----------------------------------------

needs_sphinx = '4.0.2'
templates_path = ['_templates']
source_suffix = '.rst'  # ['.rst', '.md']
root_doc = 'index'

release = pkg_version
version = release if release.find('a') == -1 else release[:release.find('a')]

language = None
exclude_patterns = []

# -- General default extension configuration ------------------------------

# autodoc options
autodoc_docstring_signature = True
autodoc_inherit_docstrings = False
autodoc_typehints = 'none'

autoapi_type = 'python'
autoapi_generate_api_docs = False

# autosectionlabel options
# autosectionlabel throws warnings if section names are duplicated.
# The following tells autosectionlabel to not throw a warning for
# duplicated section names that are in different documents.
autosectionlabel_prefix_document = True

# katex options
katex_prerender = True

# napoleon options
napoleon_use_ivar = True
napoleon_use_rtype = False

# todo options
# If true, `todo` and `todoList` produce output, else they produce nothing.
# todo_include_todos = True

# -- Options for HTML output ----------------------------------------------

html_theme = 'trojanzoo_sphinx_theme'
html_favicon = 'images/favicon.ico'
html_title = " ".join((project, version, "documentation"))
