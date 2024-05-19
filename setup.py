#!/usr/bin/env python3
# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os
import glob
import re
import shutil
import subprocess
import sys
import time
import warnings

warnings.filterwarnings("ignore", message="setup.py install is deprecated")
warnings.filterwarnings("ignore", message="easy_install command is deprecated")
warnings.filterwarnings("ignore", message="pyproject.toml does not contain a tool.setuptools_scm section")
warnings.filterwarnings("ignore", message="Configuring installation scheme with distutils config files")

from setuptools import setup, Extension, Command
from setuptools.command.build_ext import build_ext

# check that we can function here
if not ((3, 8) <= sys.version_info[:2] <= (3, 12)):
    print("Sorry, duplicity requires version 3.8 thru 3.12 of Python.")
    sys.exit(1)

Version: str = "2.2.4rc3"
reldate: str = time.strftime("%B %d, %Y", time.gmtime(int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))))

# READTHEDOCS uses setup.py sdist but can't handle extensions
ext_modules = list()
incdir_list = list()
libdir_list = list()
if os.environ.get("READTHEDOCS", None) is None:
    # set incdir and libdir for librsync
    if os.name == "posix":
        LIBRSYNC_DIR = os.environ.get("LIBRSYNC_DIR", "")
        args = sys.argv[:]
        for arg in args:
            if arg.startswith("--librsync-dir="):
                LIBRSYNC_DIR = arg.split("=")[1]
                sys.argv.remove(arg)
        if LIBRSYNC_DIR:
            incdir_list.append(os.path.join(LIBRSYNC_DIR, "include"))
            libdir_list.append(os.path.join(LIBRSYNC_DIR, "lib"))

    # set incdir and libdir for pyenv
    if pyenv_root := os.environ.get("PYENV_ROOT", None):
        major, minor, patch = sys.version_info[:3]
        incdir_list.append(
            os.path.join(
                f"{pyenv_root}",
                f"versions",
                f"{major}.{minor}.{patch}",
                f"include",
                f"python{major}.{minor}",
            )
        )
        libdir_list.append(
            os.path.join(
                f"{pyenv_root}",
                f"versions",
                f"{major}.{minor}.{patch}",
                f"lib",
                f"python{major}.{minor}",
            )
        )

    # add standard locs
    incdir_list.append("/usr/local/include")
    libdir_list.append("/usr/local/lib")
    incdir_list.append("/usr/include")
    libdir_list.append("/usr/lib")

    # build the librsync extension
    ext_modules = [
        Extension(
            name=r"duplicity._librsync",
            sources=["duplicity/_librsyncmodule.c"],
            include_dirs=incdir_list,
            library_dirs=libdir_list,
            libraries=["rsync"],
        )
    ]


def get_data_files():
    """gen list of data files"""

    # static data files
    data_files = [
        (
            "share/man/man1",
            [
                "man/duplicity.1",
            ],
        ),
        (
            f"share/doc/duplicity-{Version}",
            [
                "CHANGELOG.md",
                "AUTHORS.md",
                "COPYING",
                "README.md",
                "README-LOG.md",
                "README-REPO.md",
                "README-TESTING.md",
            ],
        ),
    ]

    # short circuit fot READTHEDOCS
    if os.environ.get("READTHEDOCS") == "True":
        return data_files

    # msgfmt the translation files
    assert os.path.exists("po"), "Missing 'po' directory."

    linguas = glob.glob("po/*.po")
    for lang in linguas:
        lang = lang[3:-3]
        try:
            os.mkdir(os.path.join("po", lang))
        except os.error:
            pass
        subprocess.run(f"cp po/{lang}.po po/{lang}", shell=True, check=True)
        subprocess.run(f"msgfmt po/{lang}.po -o po/{lang}/duplicity.mo", shell=True, check=True)

    for root, dirs, files in os.walk("po"):
        for file in files:
            path = os.path.join(root, file)
            if path.endswith("duplicity.mo"):
                lang = os.path.split(root)[-1]
                data_files.append((f"share/locale/{lang}/LC_MESSAGES", [f"po/{lang}/duplicity.mo"]))

    return data_files


def cleanup():
    if os.path.exists("po/LINGUAS"):
        linguas = open("po/LINGUAS").readlines()
        for line in linguas:
            langs = line.split()
            for lang in langs:
                shutil.rmtree(os.path.join("po", lang), ignore_errors=True)


class BuildExtCommand(build_ext):
    """Build extension modules."""

    def run(self):
        # build the _librsync.so module
        print("Building extension for librsync...")
        self.inplace = True
        build_ext.run(self)


class SetVersionCommand(Command):
    """
    Mod the versioned files and add correct version and reldate
    """

    description: str = "Version source based env var DUP_VERSION"

    user_options: list = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        global Version

        if not (Version := os.environ.get("DUP_VERSION", False).strip("\"'")):
            print("DUP_VERSION not set in environment.\nSet DUP_VERSION and try again")
            sys.exit(1)

        if self.dry_run:
            print("Dry run, no changes will be made.")

        # .TH DUPLICITY 1 "$reldate" "Version $version" "User Manuals" \"  -*- nroff -*-
        self.version_source(
            r"""\.TH\ DUPLICITY\ 1\ "(?P<reldate>[^"]*)"\ "Version\ (?P<version>[^"]*)"\ "User\ Manuals"\ \\"\ """
            r"""\ \-\*\-\ nroff\ \-\*\-""",
            r"""\.TH\ DUPLICITY\ 1\ "(?P<reldate>[^"]*)"\ "Version\ (?P<version>[^"]*)"\ "User\ Manuals"\ \\"\ """
            r"""\ \-\*\-\ nroff\ \-\*\-""",
            os.path.join("man", "duplicity.1"),
        )

        # __version__ = "$version"
        self.version_source(
            r'__version__: str = "(?P<version>[^"]*)"',
            r'__reldate__: str = "(?P<reldate>[^"]*)"',
            os.path.join("duplicity", "__init__.py"),
        )

        # version: $version
        self.version_source(
            r"version: (?P<version>.*)\n",
            None,
            os.path.join("snap", "snapcraft.yaml"),
        )

        # Version: str = "$version"
        self.version_source(
            r'Version: str = "(?P<version>[^\"]*)"',
            None,
            os.path.join(".", "setup.py"),
        )

        # version = "$version"
        self.version_source(
            r'version = "(?P<version>[^\"]*)"',
            None,
            os.path.join(".", "pyproject.toml"),
        )

    def version_source(self, version_patt: str, reldate_patt: str, pathname: str):
        """
        Copy source to dest, substituting current version with Version
        current release date with today's date, i.e. December 28, 2008.
        """
        with open(pathname, "rt") as fd:
            buffer = fd.read()

        # process version
        if version_patt:
            if m := re.search(version_patt, buffer):
                version_sub = re.escape(m.group("version"))
                newbuffer = re.sub(version_sub, Version, buffer)
                if newbuffer == buffer:
                    print(f"ERROR: version unchanged in {pathname}.", file=sys.stderr)
                else:
                    buffer = newbuffer
                    if self.verbose:
                        print(f"Substituted '{version_sub}' with '{Version}' in {pathname}.")
            else:
                print(f"ERROR: {version_patt} not found in {pathname}.", file=sys.stderr)
                sys.exit(1)

        # process reldate
        if reldate_patt:
            if m := re.search(reldate_patt, buffer):
                reldate_sub = re.escape(m.group("reldate"))
                newbuffer = re.sub(reldate_sub, reldate, buffer)
                if newbuffer == buffer:
                    print(f"ERROR: reldate unchanged in {pathname}.", file=sys.stderr)
                else:
                    buffer = newbuffer
                    if self.verbose:
                        print(f"Substituted '{reldate_sub}' with '{reldate}' in {pathname}.")
            else:
                print(f"ERROR: {reldate_patt} not found in {pathname}.", file=sys.stderr)
                sys.exit(1)

        if not self.dry_run:
            with open(pathname, "w") as fd:
                fd.write(buffer)


setup(
    packages=[
        "duplicity",
        "duplicity.backends",
        "duplicity.backends.pyrax_identity",
    ],
    package_dir={
        "duplicity": "duplicity",
        "duplicity.backends": "duplicity/backends",
    },
    ext_modules=ext_modules,
    data_files=get_data_files(),
    include_package_data=True,
    tests_require=[
        "fasteners",
        "pexpect",
        "pytest",
        "pytest-runner",
    ],
    test_suite="testing",
    cmdclass={
        "build_ext": BuildExtCommand,
        "setversion": SetVersionCommand,
    },
)

cleanup()
