# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#

import os
import sys

import pytest


@pytest.fixture(scope="function")
def redirect_stdin():
    """GPG requires stdin to be open and have real file descriptor, which interferes with pytest's capture facility.
    Work around this by redirecting /dev/null to stdin temporarily.

    Activate this fixture on unittest test methods and classes by means of:
    @pytest.mark.usefixtures("redirect_stdin")."""
    try:
        targetfd_save = os.dup(0)
        stdin_save = sys.stdin

        nullfile = open(os.devnull, "r")
        sys.stdin = nullfile
        os.dup2(nullfile.fileno(), 0)
        yield
    finally:
        os.dup2(targetfd_save, 0)  # pylint: disable=used-before-assignment
        sys.stdin = stdin_save  # pylint: disable=used-before-assignment
        os.close(targetfd_save)
        nullfile.close()  # pylint: disable=used-before-assignment
