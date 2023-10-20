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
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.install import install
from setuptools.command.sdist import sdist
from setuptools.command.test import test


# check that we can function here
if not (sys.version_info[0] == 3 and sys.version_info[1] >= 8):
    print("Sorry, duplicity requires version 3.8 or later of Python3.")
    sys.exit(1)


Version = "2.1.4"
scm_version_args = {
    "tag_regex": r"^(?P<prefix>rel.)?(?P<version>[^\+]+)(?P<suffix>.*)?$",
    "local_scheme": "no-local-version",
    "fallback_version": Version,
}
try:
    from setuptools_scm import get_version  # pylint: disable=import-error

    Version = get_version(**scm_version_args)
except Exception as e:
    pass
Reldate = time.strftime("%B %d, %Y", time.gmtime(int(os.environ.get("SOURCE_DATE_EPOCH", time.time()))))


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
                "bin/duplicity.1",
            ],
        ),
        (
            f"share/doc/duplicity-{Version}",
            [
                "CHANGELOG.md",
                "CONTRIBUTING.md",
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


def VersionedCopy(source, dest):
    """
    Copy source to dest, substituting $version with version
    $reldate with today's date, i.e. December 28, 2008.
    """
    with open(source, "rt") as fd:
        buffer = fd.read()

    buffer = re.sub("\$version", Version, buffer)
    buffer = re.sub("\$reldate", Reldate, buffer)

    with open(dest, "wt") as fd:
        fd.write(buffer)


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
        assert not os.chmod(os.path.join(tardir, "bin", "duplicity"), 0o755)

        # recopy the unversioned files and add correct version
        VersionedCopy(
            os.path.join("bin", "duplicity.1"),
            os.path.join(tardir, "bin", "duplicity.1"),
        )
        VersionedCopy(
            os.path.join("duplicity", "__init__.py"),
            os.path.join(tardir, "duplicity", "__init__.py"),
        )
        VersionedCopy(
            os.path.join("snap", "snapcraft.yaml"),
            os.path.join(tardir, "snap", "snapcraft.yaml"),
        )

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


class InstallCommand(install):
    def run(self):
        # Normally, install will call build().  But we want to delete the
        # testing dir between building and installing.  So we manually build
        # and mark ourselves to skip building when we run() for real.
        self.run_command("build")
        self.skip_build = True

        # remove testing dir
        top_dir = os.path.dirname(os.path.abspath(__file__))
        if self.build_lib != top_dir:
            testing_dir = os.path.join(self.build_lib, "testing")
            shutil.rmtree(testing_dir)

        install.run(self)


class InstallDataCommand(install_data):
    def run(self):
        install_data.run(self)

        # version the man pages
        for tup in self.data_files:
            base, filenames = tup
            if base == "share/man/man1":
                for fn in filenames:
                    fn = os.path.split(fn)[-1]
                    path = os.path.join(self.install_dir, base, fn)
                    VersionedCopy(path, path)


class BuildExtCommand(build_ext):
    """Build extension modules."""

    def run(self):
        # build the _librsync.so module
        print("Building extension for librsync...")
        self.inplace = True
        build_ext.run(self)


with open("README.md") as fh:
    long_description = fh.read()


setup(
    name="duplicity",
    version=Version,
    description="Encrypted backup using rsync algorithm",
    long_description=long_description,
    long_description_content_type="text/plain",
    author="Ben Escoto <ben@emrose.org>",
    author_email="ben@emrose.org",
    maintainer="Kenneth Loafman <kenneth@loafman.com>",
    maintainer_email="kenneth@loafman.com",
    url="http://duplicity.us",
    python_requires=">=3.8, <4",
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
    scripts=[
        "bin/duplicity",
    ],
    data_files=get_data_files(),
    include_package_data=True,
    install_requires=[
        "fasteners",
        "setuptools_scm",
    ],
    tests_require=[
        "fasteners",
        "mock",
        "pexpect",
        "pytest",
        "pytest-runner",
    ],
    test_suite="testing",
    cmdclass={
        "build_ext": BuildExtCommand,
        "install": InstallCommand,
        "install_data": InstallDataCommand,
        "sdist": SdistCommand,
        "test": TestCommand,
    },
    classifiers=[
        "Development Status :: 6 - Mature",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: C",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Archiving :: Backup",
    ],
)

cleanup()
