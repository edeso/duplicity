# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import os
import sys

sys.path.insert(0, os.path.abspath("../bin"))
sys.path.insert(0, os.path.abspath("../duplicity"))
sys.path.insert(0, os.path.abspath("../testing"))
sys.path.insert(0, os.path.abspath("../tools"))


# -- Project information -----------------------------------------------------

project = "duplicity"
copyright = "2021, Kenneth Loafman"  # pylint: disable=redefined-builtin
author = "Kenneth Loafman"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    ".DS_Store",
    "README*",
    "Thumbs.db",
    "_build",
    "setup.py",
    "testing/manual",
    "testing/override",
]


# -- Options for HTML output -------------------------------------------------

# The document name of the “master” document, that is, the document that
# contains the root toctree directive. Default is 'index' now, however,
# 'content' is still used at readthedocs.
master_doc = "index"

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []


# -- Extension configuration -------------------------------------------------
autodoc_mock_imports = [
    "duplicity._librsync",
    "duplicity.apsw",
]

autodoc_default_options = {
    "autofunction": True,
    "members": True,
    "member-order": "alphabetical",
    "special-members": "__init__, __call__, __next__",
    "undoc-members": True,
}

source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}


# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True
