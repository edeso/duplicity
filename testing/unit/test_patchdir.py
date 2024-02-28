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


import io
import platform
import unittest

from duplicity import diffdir
from duplicity import patchdir
from duplicity import selection
from duplicity.path import *  # pylint: disable=unused-wildcard-import,redefined-builtin
from testing import _runtest_dir
from . import UnitTestCase


class PatchingTest(UnitTestCase):
    """Test patching"""

    def setUp(self):
        super().setUp()
        self.unpack_testfiles()

    def copyfileobj(self, infp, outfp):
        """Copy in fileobj to out, closing afterwards"""
        blocksize = 32 * 1024
        while True:
            buf = infp.read(blocksize)
            if not buf:
                break
            outfp.write(buf)
        assert not infp.close()
        assert not outfp.close()

    def test_total(self):
        """Test cycle on dirx"""
        self.total_sequence(
            [
                f"{_runtest_dir}/testfiles/dir1",
                f"{_runtest_dir}/testfiles/dir2",
                f"{_runtest_dir}/testfiles/dir3",
            ]
        )

    def get_sel(self, path):
        """Get selection iter over the given directory"""
        return selection.Select(path).set_iter()

    def total_sequence(self, filelist):
        """Test signatures, diffing, and patching on directory list"""
        assert len(filelist) >= 2
        sig = Path(f"{_runtest_dir}/testfiles/output/sig.tar")
        diff = Path(f"{_runtest_dir}/testfiles/output/diff.tar")
        seq_path = Path(f"{_runtest_dir}/testfiles/output/sequence")
        new_path, old_path = None, None  # set below in for loop

        # Write initial full backup to diff.tar
        for dirname in filelist:
            old_path, new_path = new_path, Path(dirname)
            if old_path:
                sigblock = diffdir.DirSig(self.get_sel(seq_path))
                diffdir.write_block_iter(sigblock, sig)
                deltablock = diffdir.DirDelta(self.get_sel(new_path), sig.open("rb"))
            else:
                deltablock = diffdir.DirFull(self.get_sel(new_path))
            diffdir.write_block_iter(deltablock, diff)

            patchdir.Patch(seq_path, diff.open("rb"))
            # print "#########", seq_path, new_path
            assert seq_path.compare_recursive(new_path, 1)

    def test_block_tar(self):
        """Test building block tar from a number of files"""

        def get_fileobjs():
            """Return iterator yielding open fileobjs of tar files"""
            for i in range(1, 4):
                p = Path(f"{_runtest_dir}/testfiles/blocktartest/test{i}.tar")
                fp = p.open("rb")
                yield fp
                fp.close()

        tf = patchdir.TarFile_FromFileobjs(get_fileobjs())
        namelist = []
        for tarinfo in tf:
            namelist.append(tarinfo.name)
        for i in range(1, 6):
            assert f"tmp/{int(i)}" in namelist, namelist

    def test_doubledot_hole(self):
        """Test for the .. bug that lets tar overwrite parent dir"""

        def make_bad_tar(filename):
            """Write attack dup_tarfile to filename"""
            tf = dup_tarfile.TarFile(name=filename, mode="w")

            # file object will be empty, and tarinfo will have path
            # "snapshot/../warning-security-error"
            assert not os.system(f"cat /dev/null > {_runtest_dir}/testfiles/output/file")
            path = Path(f"{_runtest_dir}/testfiles/output/file")
            path.index = (b"diff", b"..", b"warning-security-error")
            ti = path.get_tarinfo()
            fp = io.StringIO("")
            tf.addfile(ti, fp)

            tf.close()

        make_bad_tar(f"{_runtest_dir}/testfiles/output/bad.tar")
        os.mkdir(f"{_runtest_dir}/testfiles/output/temp")

        self.assertRaises(
            patchdir.PatchDirException,
            patchdir.Patch,
            Path(f"{_runtest_dir}/testfiles/output/temp"),
            open(f"{_runtest_dir}/testfiles/output/bad.tar", "rb"),
        )
        assert not Path(f"{_runtest_dir}/testfiles/output/warning-security-error").exists()


class index(object):
    """Used below to test the iter collation"""

    def __init__(self, index):
        self.index = index


class CollateItersTest(UnitTestCase):
    def setUp(self):
        super().setUp()
        self.unpack_testfiles()

    def test_collate(self):
        """Test collate_iters function"""
        indicies = [index(i) for i in [0, 1, 2, 3]]
        helper = lambda i: indicies[i]

        makeiter1 = lambda: iter(indicies)
        makeiter2 = lambda: map(helper, [0, 1, 3])
        makeiter3 = lambda: map(helper, [1, 2])

        outiter = patchdir.collate_iters([makeiter1(), makeiter2()])
        assert Iter.equal(
            outiter,
            iter(
                [
                    (indicies[0], indicies[0]),
                    (indicies[1], indicies[1]),
                    (indicies[2], None),
                    (indicies[3], indicies[3]),
                ]
            ),
        )

        assert Iter.equal(
            patchdir.collate_iters([makeiter1(), makeiter2(), makeiter3()]),
            iter(
                [
                    (indicies[0], indicies[0], None),
                    (indicies[1], indicies[1], indicies[1]),
                    (indicies[2], None, indicies[2]),
                    (indicies[3], indicies[3], None),
                ]
            ),
            1,
        )

        assert Iter.equal(
            patchdir.collate_iters([makeiter1(), iter([])]),
            iter([(i, None) for i in indicies]),
        )
        assert Iter.equal(
            [(i, None) for i in indicies],
            patchdir.collate_iters([makeiter1(), iter([])]),
        )

    def test_tuple(self):
        """Test indexed tuple"""
        i = patchdir.IndexedTuple((1, 2, 3), ("a", "b"))
        i2 = patchdir.IndexedTuple((), ("hello", "there", "how are you"))

        assert i[0] == "a"
        assert i[1] == "b"
        assert i2[1] == "there"
        assert len(i) == 2 and len(i2) == 3
        assert i2 < i, i2 < i

    def test_tuple_assignment(self):
        a, b, c = patchdir.IndexedTuple((), (1, 2, 3))
        assert a == 1
        assert b == 2
        assert c == 3


class TestInnerFuncs(UnitTestCase):
    """Test some other functions involved in patching"""

    def setUp(self):
        super().setUp()
        self.unpack_testfiles()
        self.check_output()

    def check_output(self):
        """Make {0}/testfiles/output exists"""
        out = Path(f"{_runtest_dir}/testfiles/output")
        if not (out.exists() and out.isdir()):
            out.mkdir()
        self.out = out

    def snapshot(self):
        """Make a snapshot ROPath, permissions 0o600"""
        ss = self.out.append("snapshot")
        fout = ss.open("wb")
        fout.write(b"hello, world!")
        assert not fout.close()
        ss.chmod(0o600)
        ss.difftype = "snapshot"
        return ss

    def get_delta(self, old_buf, new_buf):
        """Return delta buffer from old to new"""
        sigfile = librsync.SigFile(io.BytesIO(old_buf))
        sig = sigfile.read()
        assert not sigfile.close()

        deltafile = librsync.DeltaFile(sig, io.BytesIO(new_buf))
        deltabuf = deltafile.read()
        assert not deltafile.close()
        return deltabuf

    def delta1(self):
        """Make a delta ROPath, permissions 0o640"""
        delta1 = self.out.append("delta1")
        fout = delta1.open("wb")
        fout.write(self.get_delta(b"hello, world!", b"aonseuth aosetnuhaonsuhtansoetuhaoe"))
        assert not fout.close()
        delta1.chmod(0o640)
        delta1.difftype = "diff"
        return delta1

    def delta2(self):
        """Make another delta ROPath, permissions 0o644"""
        delta2 = self.out.append("delta1")
        fout = delta2.open("wb")
        fout.write(
            self.get_delta(
                b"aonseuth aosetnuhaonsuhtansoetuhaoe",
                b"3499 34957839485792357 458348573",
            )
        )
        assert not fout.close()
        delta2.chmod(0o644)
        delta2.difftype = "diff"
        return delta2

    def deleted(self):
        """Make a deleted ROPath"""
        deleted = self.out.append("deleted")
        assert not deleted.exists()
        deleted.difftype = "deleted"
        return deleted

    def test_normalize(self):
        """Test normalizing a sequence of diffs"""
        ss = self.snapshot()
        d1 = self.delta1()
        d2 = self.delta2()
        de = self.deleted()

        seq1 = [ss, d1, d2]
        seq2 = [ss, d1, d2, de]
        seq3 = [de, ss, d1, d2]
        seq4 = [de, ss, d1, d2, ss]
        seq5 = [de, ss, d1, d2, ss, d1, d2]

        def try_seq(input_seq, correct_output_seq):
            normed = patchdir.normalize_ps(input_seq)
            assert normed == correct_output_seq, (normed, correct_output_seq)

        try_seq(seq1, seq1)
        try_seq(seq2, [de])
        try_seq(seq3, seq1)
        try_seq(seq4, [ss])
        try_seq(seq5, seq1)

    # TODO: fix test_patch_seq2ropath for macOS, maybe others.
    #       Fails under pytest, and pydevd
    # ----------
    #     def testseq(seq, perms, buf):
    #         result = patchdir.patch_seq2ropath(seq)
    # >       assert result.getperms() == perms, (result.getperms(), perms)
    # E       AssertionError: ('501:0 600', '501:20 600')
    # E       assert '501:0 600' == '501:20 600'
    # E         - 501:0 600
    # E         + 501:20 600
    @unittest.skipUnless(platform.platform().startswith("Linux"), "Skip on non-Linux systems")
    def test_patch_seq2ropath(self):
        """Test patching sequence"""

        def testseq(seq, perms, buf):
            result = patchdir.patch_seq2ropath(seq)
            assert result.getperms() == perms, (result.getperms(), perms)
            fout = result.open("rb")
            contents = fout.read()
            assert not fout.close()
            assert contents == buf, (contents, buf)

        ids = f"{int(os.getuid())}:{int(os.getgid())}"

        testseq([self.snapshot()], f"{ids} 600", b"hello, world!")
        testseq(
            [self.snapshot(), self.delta1()],
            f"{ids} 640",
            b"aonseuth aosetnuhaonsuhtansoetuhaoe",
        )
        testseq(
            [self.snapshot(), self.delta1(), self.delta2()],
            f"{ids} 644",
            b"3499 34957839485792357 458348573",
        )


if __name__ == "__main__":
    unittest.main()
