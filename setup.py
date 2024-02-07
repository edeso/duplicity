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

from distutils.command.build_scripts import build_scripts
from distutils.command.install_data import install_data
from setuptools import setup, Extension, Command
from setuptools.command.build_ext import build_ext
from setuptools.command.sdist import sdist
from setuptools.command.test import test

import setuptools_scm as scm

# check that we can function here
if not ((3, 8) <= sys.version_info[:2] <= (3, 12)):
    print("Sorry, duplicity requires version 3.8 thru 3.12 of Python.")
    sys.exit(1)

scm_version_args: dict = {
    "tag_regex": r"^(?P<prefix>rel\.)?(?P<version>[^\+]+)(?P<suffix>.*)?$",
    "version_scheme": "guess-next-dev",
    "local_scheme": "no-local-version",
}

Version: str = "2.2.2"
try:
    Version = scm.get_version(**scm_version_args)
except Exception:
    print(
        f"ERROR: Could not parse version from local git repository.\nUsing fallback version: {Version}",
        file=sys.stderr,
    )

reldate: str = time.strftime("%B %d, %Y", time.gmtime(int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))))

# READTHEDOCS uses setup.py sdist but can't handle extensions
ext_modules = list()
incdir_list = list()
libdir_list = list()
if not os.environ.get("READTHEDOCS") == "True":
    # set incdir and libdir for librsync
    if os.name == "posix":
        LIBRSYNC_DIR = os.environ.get("LIBRSYNC_DIR", "")
        args = sys.argv[:]
        for arg in args:
            if arg.startswith("--librsync-dir="):
                LIBRSYNC_DIR = arg.split("=")[1]
                sys.argv.remove(arg)
        if LIBRSYNC_DIR:
            incdir_list = [os.path.join(LIBRSYNC_DIR, "include")]
            libdir_list = [os.path.join(LIBRSYNC_DIR, "lib")]

    # build the librsync extension
    ext_modules = [
        Extension(
            name=r"duplicity._librsync",
            sources=[r"duplicity/_librsyncmodule.c"],
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
        assert not os.system(f"cp po/{lang}.po po/{lang}"), lang
        assert not os.system(f"msgfmt po/{lang}.po -o po/{lang}/duplicity.mo"), lang

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
                try:
                    shutil.rmtree(os.path.join("po", lang))
                except Exception:
                    pass


class BuildExtCommand(build_ext):
    """Build extension modules."""

    def run(self):
        # build the _librsync.so module
        print("Building extension for librsync...")
        self.inplace = True
        build_ext.run(self)


class SCMVersionSourceCommand(Command):
    """
    Mod the versioned files and add correct scmversion
    """

    description: str = "Version souce based on SCM tag"

    user_options: list = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
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

        # fallback_version = "$version"
        self.version_source(
            r'fallback_version = "(?P<version>[^\"]*)"',
            None,
            os.path.join(".", "pyproject.toml"),
        )

    def version_source(self, version_patt: str, reldate_patt: str, pathname: str):
        """
        Copy source to dest, substituting current version with scmversion
        current release date with today's date, i.e. December 28, 2008.
        """
        with open(pathname) as fd:
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


class SdistCommand(sdist):
    def run(self):
        sdist.run(self)

        orig = f"{self.dist_dir}/duplicity-{Version}.tar.gz"
        tardir = f"duplicity-{Version}"
        tarball = f"{self.dist_dir}/duplicity-{Version}.tar.gz"

        assert not os.system(f"tar -xf {orig}")
        assert not os.remove(orig)

        # make sure executables are
        assert not os.chmod(os.path.join(tardir, "setup.py"), 0o755)
        assert not os.chmod(os.path.join(tardir, "duplicity", "__main__.py"), 0o755)

        # set COPYFILE_DISABLE to disable appledouble file creation
        os.environ["COPYFILE_DISABLE"] = "true"

        # make the new tarball and remove tardir
        assert not os.system(
            f"""tar czf {tarball} \
                                 --exclude '.*' \
                                 --exclude Makefile \
                                 --exclude debian \
                                 --exclude docs \
                                 --exclude readthedocs.yaml \
                                 --exclude testing/docker \
                                 --exclude testing/manual \
                                 --exclude testing/regression \
                                 --exclude tools \
                                 {tardir}
                              """
        )
        assert not shutil.rmtree(tardir)


class TestCommand(test):
    def run(self):
        # Make sure all modules are ready
        build_cmd = self.get_finalized_command("build_py")
        build_cmd.run()
        # And make sure our scripts are ready
        build_scripts_cmd = self.get_finalized_command("build_scripts")
        build_scripts_cmd.run()

        # make symlinks for test data
        if build_cmd.build_lib != top_dir:
            for path in ["source_files.tar.gz", "gnupg"]:
                src = os.path.join(top_dir, "testing", path)
                target = os.path.join(build_cmd.build_lib, "testing", path)
                try:
                    os.symlink(src, target)
                except Exception:
                    pass

        os.environ["PATH"] = f"{os.path.abspath(build_scripts_cmd.build_dir)}:{os.environ.get('PATH')}"

        test.run(self)

        cleanup()


with open("README.md") as fh:
    long_description = fh.read()


setup(
    name="duplicity",
    version=Version,
    url="http://duplicity.us",
    platforms=["any"],
    packages=[
        "duplicity",
        "duplicity.backends",
        "duplicity.backends.pyrax_identity",
        "testing",
        "testing.functional",
        "testing.unit",
    ],
    package_dir={
        "duplicity": "duplicity",
        "duplicity.backends": "duplicity/backends",
    },
    package_data={
        "testing": [
            "testing/gnupg",
            "testing/gnupg/.gpg-v21-migrated",
            "testing/gnupg/README",
            "testing/gnupg/gpg-agent.conf",
            "testing/gnupg/gpg.conf",
            "testing/gnupg/private-keys-v1.d",
            "testing/gnupg/private-keys-v1.d/1DBE767B921015FD5466978BAC968320E5BF6812.key",
            "testing/gnupg/private-keys-v1.d/4572B9686180E88EA52ED65F1416E486F7A8CAF5.key",
            "testing/gnupg/private-keys-v1.d/7229722CD5A4726D5CC5588034ADA07429FDECAB.key",
            "testing/gnupg/private-keys-v1.d/910D6B4035D3FEE3DA5960C1EE573C5F9ECE2B8D.key",
            "testing/gnupg/private-keys-v1.d/B29B24778338E7F20437B21704EA434E522BC1FE.key",
            "testing/gnupg/private-keys-v1.d/D2DF6D795DFD90DB4F7A109970F506692731CA67.key",
            "testing/gnupg/pubring.gpg",
            "testing/gnupg/random_seed",
            "testing/gnupg/secring.gpg",
            "testing/gnupg/trustdb.gpg",
            "testing/overrides",
            "testing/overrides/__init__.py",
            "testing/overrides/bin",
            "testing/overrides/bin/hsi",
            "testing/overrides/bin/lftp",
            "testing/overrides/bin/ncftpget",
            "testing/overrides/bin/ncftpls",
            "testing/overrides/bin/ncftpput",
            "testing/overrides/bin/tahoe",
        ],
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
        "sdist": SdistCommand,
        "test": TestCommand,
        "scmversion": SCMVersionSourceCommand,
    },
)

cleanup()
