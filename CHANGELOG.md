## rel.2.0.0rc2 (2023-07-24)

### Changes

* Fix format strings in idrivedbackend.py. [Kenneth Loafman]

* Add additional CLI checks. [Kenneth Loafman]

* Fix format strings in idrivedbackend.py. [Kenneth Loafman]

* Fix format string in statistics.py. [Kenneth Loafman]

* Remove kerberos from snap builds. [Kenneth Loafman]

  kerberos will not build in snapcraft.

* Changes to allow building snaps. [Kenneth Loafman]

  Found another bug in snapcraft, see:
  https://bugs.launchpad.net/snapcraft/+bug/2028303


## rel.2.0.0rc1 (2023-07-17)

### Changes

* Update CHANGELOG.md. [Kenneth Loafman]

* Fix implied command handling. [Kenneth Loafman]

* Create regression test dir from old scripts. [Kenneth Loafman]


## rel.2.0.0rc0 (2023-07-10)

### Changes

* Update CHANGELOG.md. [Kenneth Loafman]

### Fix

* Finish conversions to f-strings. [Kenneth Loafman]

  See https://github.com/ikamensh/flynt/issues/185

* Convert to f-strings via 'flynt -tc -tj'. [Kenneth Loafman]

* With py2 gone remove unicode string adornments. [Kenneth Loafman]

* Fix implied command when target is empty. [Kenneth Loafman]


## rel.2.0.0b2 (2023-07-02)

### Changes

* Update CHANGELOG.md. [Kenneth Loafman]

* Fix syntax error in .gitlab-ci.yml. [Kenneth Loafman]

* Fix website to only run with WEBSITE\_TRIGGER\_TOKEN. [Kenneth Loafman]

* Fix PEP8 issue.  Update CHANGELOG.md. [Kenneth Loafman]

* Resolve some minor merge issues. [Kenneth Loafman]

* Whoops, used f-string to fix #716. Fixed. [Kenneth Loafman]

* Fix #716.  Print filename on read error. [Kenneth Loafman]

* Fix #709.  Add docs on passphrase encryption used. [Kenneth Loafman]

* Fixes for handling snaps again. [Kenneth Loafman]

  Use requirements.txt instead of internal list.

* Fix #707 for test\_get\_stats\_string. [Kenneth Loafman]

  Move UTC set/unset to testing.__init__.

* Fix #707 for test\_get\_stats\_string. [Kenneth Loafman]

  Base time on UTC rather than where the test is run.

* Fix #707 for test\_get\_stats\_string. [Kenneth Loafman]

  Base time on UTC rather than where the test is run.

* Fix #707 for rclone backend testing. [Kenneth Loafman]

  Create 'duptest' config if needed, then remove after   tests are
  complete.
  Add some more pytest options to tox.ini.

* Comment out test\_path:test\_compare, flaky. [Kenneth Loafman]

  Fixes #707 - 1.2.3 test failure

* Force cryptography<3.4 for py2 support. [Kenneth Loafman]

* Test if requirements.txt changes. [Kenneth Loafman]

* Revert back to tox < 4.0. [Kenneth Loafman]

### Fix

* Fix #710. Missing Content-Type header on webdav. [Kenneth Loafman]

* S3 filename encoding. [Thomas Laubrock]

* Fix #712 "if cache lost. `*.sigtar.gpg` files not accessible" [Thomas Laubrock]

  solution, do not add signature files to glacier

* Handle read-only remote parent folder better in gio backend. [Michael Terry]


## rel.2.0.0b1 (2023-06-30)

### Changes

* Update CHANGELOG.md. [Kenneth Loafman]

* Some basic PEP8 and code cleanup. [Kenneth Loafman]

* Set socket default timeout in CLI. [Kenneth Loafman]

* Fixes for deprecated/changed options. [Kenneth Loafman]


## rel.2.0.0b0 (2023-06-24)

### Changes

* Misc changes for compatibility. [Kenneth Loafman]

* Fix #24.  Allow users to tune copy block size. [Kenneth Loafman]

  - Added --copy-blocksize, default 128k to options.   - Added tests for
  same and improved other testss.

* Fix .gitlab-ci.yml to skip website step if no token. [Kenneth Loafman]


## rel.2.0.0a2 (2023-06-14)

### Changes

* Remove pathvalidate from use.  Fixes #27. [Kenneth Loafman]


## rel.2.0.0a1 (2023-06-14)

### Changes

* More CLI improvements. [Kenneth Loafman]

  - Improve error message for implied commands.   - Code and testing
  clean up.   - Remove deprecated option handling.

* Add implied backup/restore back. [Kenneth Loafman]

* CLI improvements and cleanup. [Kenneth Loafman]

  - Remove 'backup' command.   - Preparse options for config.

* Minor cleanup, rm dead code. [Kenneth Loafman]

* RcloneBackendTest now creates its own config. [Kenneth Loafman]

* "--ignore-errors" gets proper handling in CLI. [Kenneth Loafman]

### Fix

* Fix #22, “--no-compression” doesn't have effect. [Kenneth Loafman]

* Fix .gitlab-ci.yml file syntax error. [Kenneth Loafman]


## rel.2.0.0a0 (2023-06-01)

### Changes

* Fix initial version. [Kenneth Loafman]

* Give up. Let setup mangle as it will. [Kenneth Loafman]

* Use semver tags, let setup mangle. [Kenneth Loafman]

* Make PEP 440 compatible, not semver yet. [Kenneth Loafman]

* Changes to allow alpha, beta, rc prerelease. [Kenneth Loafman]

* Update gitlab-ci.yml. [Kenneth Loafman]

* Update gitlab-ci.yml. [Kenneth Loafman]

* Remove 'rdiffdir'.  Not used. [Kenneth Loafman]

* Add 'make sdist' to Makefile. [Kenneth Loafman]

* Update .gitignore. [Kenneth Loafman]

* Setuptools\_scm.get\_version now uses 'fallback\_version'. [Kenneth Loafman]

* Remove old s3\_boto\_backend.py. [Kenneth Loafman]

  Deprecated options:   --s3-multipart-max-timeout   --s3-use-
  multiprocessing   --s3-use-server-side-encryption   --s3-use-server-
  side-kms-encryption
  Retired error codes:   boto_old_style = 24   boto_lib_too_old = 25
  boto_calling_format = 26

* Remove spaces in version specs. [Kenneth Loafman]

* Cleanup py2 cruft and more. [Kenneth Loafman]

* Cleanup py2 cruft and more. [Kenneth Loafman]

* Uncomment log.test\_command\_line\_error. [Kenneth Loafman]

* Raise CommandLineError on deprecated/changed options. [Kenneth Loafman]

* Whoops, don't move import\_backends. [Kenneth Loafman]

* Fix code, tests, and do cleanup. [Kenneth Loafman]

* Requirements and code cleanup. [Kenneth Loafman]

* Whoops, fix code style. [Kenneth Loafman]

* Add error/ignored msg for deprecated options. [Kenneth Loafman]

* Some cli cleanup for subcommands. [Kenneth Loafman]

* Normalize error handling in cli\_util.py. [Kenneth Loafman]

* Some small command line fixes. [Michael Terry]

  - Fix --verbosity   - Fix --log-fd   - Fix list-current-files

* Clean out the last py2 cruft, I hope. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Some py2 to py3 cleanup. [Kenneth Loafman]

  Ran '2to3 -f filter -f map -f xrange -f zip -f idioms'.  It put some
  list calls around some of the stuff that returns iterators (redundant
  in most cases I think).  Mainly it converted code to idiomatic python.

* Update a couple of lists in conf.py. [Kenneth Loafman]

* Whoops, still need Makefile in docs. [Kenneth Loafman]

* Port ReadTheDocs changes from main branch. [Kenneth Loafman]

* Port ReadTheDocs changes from main branch. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Fix version and required python version. [Kenneth Loafman]

* Fix version and required python version. [Kenneth Loafman]

* More refactoring and cleanup after merge. [Kenneth Loafman]

* Change optparse to argparse.  Checkpoint. [Kenneth Loafman]

* Change optparse to argparse.  Checkpoint. [Kenneth Loafman]

* Change optparse to argparse.  Checkpoint. [Kenneth Loafman]

* Change optparse to argparse.  Checkpoint. [Kenneth Loafman]

* Change optparse to argparse.  Checkpoint. [Kenneth Loafman]

* Change optparse to argparse. Checkpoint. [Kenneth Loafman]

* Fix version and required python version. [Kenneth Loafman]

* More refactoring and cleanup after merge. [Kenneth Loafman]

* Change optparse to argparse.  Checkpoint. [Kenneth Loafman]

  chg:usr: Change optparse to argparse.  Checkpoint.
  chg:usr: Change optparse to argparse.  Checkpoint.
  chg:usr: Change optparse to argparse.  Checkpoint.
  chg:usr: Change optparse to argparse.  Checkpoint.

* Add Note on --time-separator in manpage. [Kenneth Loafman]

* Remove refs to --old/short-filenames.  Fix CI. [Kenneth Loafman]

* Remove deprecated --short-filenames code. [Kenneth Loafman]

* Remove deprecated --old-filenames code. [Kenneth Loafman]

* Remove deprecated --gio code. [Kenneth Loafman]

* Remove globbing deprecated code. [Kenneth Loafman]

* Remove stdin deprecated code. [Kenneth Loafman]

* Remove incomplete replicate command. [Kenneth Loafman]

* Remove LINGUAS.  Replace with globbing. [Kenneth Loafman]

* More cleanup from inspections. [Kenneth Loafman]

* Util.fsdecode ==> os.fsdecode. [Kenneth Loafman]

* Remove par2+ from target schema.  Does not matter. [Kenneth Loafman]

* Add limits to chardet and urlllib to keep requests quiet. [Kenneth Loafman]

* Lower test to ulimit 2048 and reverse filename order. [Kenneth Loafman]

### Fix

* Add a missing super() call in path.py. [Kenneth Loafman]

* Add a missing method to some super calls. [Michael Terry]

* Add missing ':''. [Kenneth Loafman]

* Remove requirement for kerberos. [Kenneth Loafman]

  - it's an optional package in webdavbackend.py   - it does not install
  properly under Docker

* Remove most 'pylint: disable=import-error'. [Kenneth Loafman]

  - add packages to requirements   - 'gi' is not available on PyPi

* Fix more py3 problems. [Kenneth Loafman]

  - remove import future in some places,   - fix azurebackend.py to use
  new azure.

* Recurse glob to include duplicity/backends. [Kenneth Loafman]

* Remove extra print statement. [Kenneth Loafman]

* Add back test\_unadorned...  Cleanup. [Kenneth Loafman]

* Fix pylint code issue. [Kenneth Loafman]

* Fix case where gpg return code is None. [Kenneth Loafman]

* Add pydevd-pycharm to requirements.txt. [Kenneth Loafman]

* Fix to allow using PyCharm or LiClipse pydevd. [Kenneth Loafman]

* Fix doctests to run again. [Kenneth Loafman]

* Remove redundant code. [Kenneth Loafman]

* Print stderr on gpg fail plus error code and string. [Kenneth Loafman]

* Fix handling of gpg\_error\_codes. [Kenneth Loafman]

  - return an 'unknown error code' message if not found   - ignore error
  2 GPG_ERR_UNKNOWN_PACKET, was "invalid packet (ctb=14)"

* Add \_() for translations of msgs in gpg\_error\_codes.py. [Kenneth Loafman]

* Add stderr\_fp back in.  Too much noise otherwise. [Kenneth Loafman]

* Remove stderr\_fp and use process return code to report errors. [Kenneth Loafman]

  - Added file make_gpg_error_codes.py which creates gpg_error_codes.py.
  - Modded gpg.py to remove use of stderr_fp, thus reducing FDs used.

* Remove status\_fd if no sign\_key in gpg.py. [Kenneth Loafman]

  - updated issue125.sh to use testing/gnupg keys   - issue125.sh passes
  with `ulimit 1024`

* Cleanup, remove all uses of logger\_fd. [Kenneth Loafman]

* Add back status\_fd for signature verification. [Kenneth Loafman]

* Remove unused GPG file handles. [Kenneth Loafman]

  - removed status and logger filehandles for decrypt   -
  testing/manual/issue125 now runs with 'ulimit -n 1536'

* Fix indentation cause by adorning. [Kenneth Loafman]

* Adorn python strings to make merges easier. [Kenneth Loafman]

* Remove extra newline in print. [Kenneth Loafman]

* Add list\_python\_files to tools. [Kenneth Loafman]

* Move find/fix un/adorned to tools. [Kenneth Loafman]

* Unadorn bin/duplicity and bin/rdiffdir. [Kenneth Loafman]

* Recover and add find/fix un/adorned strings. [Kenneth Loafman]

* Fix PEP8 issue. [Kenneth Loafman]

* Optimize imports. [Kenneth Loafman]

  - Remove 'from __future__ import .*'   - Remove 'from past.utils
  import old_div'   - Replace old_div with / or // as needed.

* Optimize imports. [Kenneth Loafman]

* Use os modules fsencode/fsdecode not ours. [Kenneth Loafman]

* Cleanup, remove test\_2to3. [Kenneth Loafman]

* Remove support for Python 2.7.  Second pass. [Kenneth Loafman]

  - remove test_unadorned_string_literals   - remove
  find/fix_unadorned_strings.py   - fix u'string' to be just 'string'

* Remove support for Python 2.7.  First pass. [Kenneth Loafman]

  - remove 'import future' and its call   - remove 'import builtin *'
  - remove conditionals based on sys.version_info   - remove mentions in
  readme and other docs

### Other

* Merge remote-tracking branch 'alpha/duplicity-py3' into duplicity-py3. [Kenneth Loafman]

  # Conflicts:   #     duplicity/cli_main.py

* Merge branch 'main' into branch 'duplicity-py3' [Kenneth Loafman]

* Merge branch 'main' into branch 'duplicity-py3' [Kenneth Loafman]

* Merge branch main into branch duplicity-py3. [Kenneth Loafman]

* Merge branch cleanup into branch duplicity-py3. [Kenneth Loafman]

* Merge main into duplicity-py3. [Kenneth Loafman]

* Merge main into branch duplicity-py3. [Kenneth Loafman]


## rel.1.2.3 (2023-05-09)

### New

* Xorriso backend for optical media. [T. K]

* Onedrive for Business Support. [Tobias Simetsreiter]

### Changes

* Fix tools release-prep & makechangelog. [Kenneth Loafman]

* Fix tools/release-prep. [Kenneth Loafman]

* Run po/update-pot. [Kenneth Loafman]

* Update readthedocs.yaml. [Kenneth Loafman]

* More ReadTheDocs changes. [Kenneth Loafman]

* More ReadTheDocs changes. [Kenneth Loafman]

* More ReadTheDocs changes. [Kenneth Loafman]

* More ReadTheDocs changes. [Kenneth Loafman]

* More ReadTheDocs changes. [Kenneth Loafman]

* More ReadTheDocs changes. [Kenneth Loafman]

* More ReadTheDocs changes. [Kenneth Loafman]

* Change readthedocs.yaml. [Kenneth Loafman]

* Change readthedocs.yaml. [Kenneth Loafman]

* Update CHANGELOG.md. [Kenneth Loafman]

* Fix spelling errors. [Barak A. Pearlmutter]

* Chg:pkg:  Cleanup.  Add 'unsquashfs -l' test from @ede. [Kenneth Loafman]

* Update Makefile 'make clean' list. [Kenneth Loafman]

* Fix run website ci call after pushes/releases. [ede]

  [skip_tests]

* Update version for Launchpad. [Kenneth Loafman]

### Fix

* Use cryptography == 3.4.8. [Kenneth Loafman]

  Fixes #703 - use same version as python3-cryptography in apt.

* Warn rather than fail on op-not-supported restore errors. [Michael Terry]

* Fixes #701 - unable to resume full backup to B2. [Kenneth Loafman]

  Now tries .name and .uc_name before failing.

* Fixes #698 - backups without GPG decryption key. [Kenneth Loafman]

  Added option --no-check-remote to skip checking the   remote manifest.
  The default is to check.

* Fixes #698 - backups without GPG decryption key. [Kenneth Loafman]

  Added option --no-check-remote to skip checking the   remote manifest.
  The default is to check.

* Fixes #686 - PCA backend does not unseal volumes. [Kenneth Loafman]

  Patch supplied by Bertrand Marc, user @bmarc.

* Skip test\_path::test\_compare on non-native. [Kenneth Loafman]

  Skip on GitLab and Launchpad build systems.   Works fine on Linux and
  macOS.

* Skip test\_path::test\_compare on non-native. [Kenneth Loafman]

  Skip on GitLab and Launchpad build systems.   Works fine on Linux and
  macOS.

* Skip test\_path::test\_compare on non-native. [Kenneth Loafman]

  Skip on GitLab and Launchpad build systems.   Works fine on Linux and
  macOS.

* Skip test\_path::test\_compare on non-native. [Kenneth Loafman]

  Skip on GitLab and Launchpad build systems.   Works fine on Linux and
  macOS.

* Skip test\_path::test\_compare on non-native. [Kenneth Loafman]

  Skip on GitLab and Launchpad build systems.   Works fine on Linux and
  macOS.

* Skip test\_path::test\_compare on non-native. [Kenneth Loafman]

  Skip on GitLab and Launchpad build systems.   Works fine on Linux and
  macOS.

* Skip test\_path::test\_compare on non-native. [Kenneth Loafman]

  Skip on GitLab and Launchpad build systems.   Works fine on Linux and
  macOS.

* Skip test\_path::test\_compare on non-native. [Kenneth Loafman]

  Skip on GitLab and Launchpad build systems.   Works fine on Linux and
  macOS.

* Revert to medieval string formatting. [Kenneth Loafman]

* Revert to medieval string formatting. [Kenneth Loafman]

* Revert to medieval string formatting. [Kenneth Loafman]

* Revert to medieval string formatting. [Kenneth Loafman]

* Remove dependency scanner. [Kenneth Loafman]

* Fix PEP8 and todo issues. [Kenneth Loafman]

* Misc fixes to testing/build environ. [Kenneth Loafman]

  start_debugger now supports multiprocess debug.   restore
  testing.unit.test_path.test_compare

* Encoding errors when logging.  Fixes #693. [Kenneth Loafman]

  Use os.fsdecode/os.fsencode when in py3.

* Onedrive may hang indefinitely.  Fixes #695. [Kenneth Loafman]

### Other

* Fix typo. [ede]

* Try to fix. [ede]

  Executing "step_script" stage of the job script   00:00   Using docker
  image sha256:3148ec916ea71d90f1beae623b3c5eb4a2db5a585db3178d9619bc2fe
  b8f5f49 for curlimages/curl:latest with digest curlimages/curl@sha256:
  f7f265d5c64eb4463a43a99b6bf773f9e61a50aaa7cefaf564f43e42549a01dd ...
  /bin/sh: eval: line 136: apt-get: not found


## rel.1.2.2 (2023-01-26)

### Changes

* \_runtest\_dir on Darwin may use TMPDIR for testing. [Kenneth Loafman]

* Update duplicity.pot. [Kenneth Loafman]

### Fix

* Fix to work with b2sdk 1.19.0. [Adam Jacobs]

* Fix #692.  Redundant --encrypt option added in gpg.py. [Kenneth Loafman]

  Been around forever.  GPG 2.2.x is the first to detect.  Added   only
  when both recipients and hidden_recipients present.

* Fix super() call in test\_selection.py. [Kenneth Loafman]

* Regression on issue #147, change password for incremental. [Kenneth Loafman]

  Changed testcase issue147.sh to need incremental.
  Fixed dup_collections.py to bail with fatal error.

* Crash if a socket is listed with --files-from.  Fixes #689. [Kenneth Loafman]

  Patch supplied by Jethro Donaldson (@jeth-ro).

### Other

* Add detailed step-by-step instructions. [ede]


## rel.1.2.1 (2022-12-02)

### Changes

* More changes to get release process working. [Kenneth Loafman]

* Fix for setuptools changes.  Add testing data files to mix. [Kenneth Loafman]


## rel.1.2.0 (2022-12-01)

### New

* Add rsync style --files-from=FILE. Fixes #151. [Kenneth Loafman]

* Add literal include/excludes. Fixes #138. [Kenneth Loafman]

### Changes

* Update duplicity.pot. [Kenneth Loafman]

* Add test case for issue #683. [Kenneth Loafman]

* Don't run start\_debugger till after logging started. [Kenneth Loafman]

* Always run pipeline after MR approval. [Kenneth Loafman]

* Remove gpg\_error\_codes.py / update duplicity.pot. [Kenneth Loafman]

* Fix name in .gitlab-ci.yml. [Kenneth Loafman]

* Go back to standard tests, no master image. [Kenneth Loafman]

* Go back to standard tests, no master image. [Kenneth Loafman]

* Go back to standard tests, no master image. [Kenneth Loafman]

* Go back to standard tests, no master image. [Kenneth Loafman]

* Go back to standard tests, no master image. [Kenneth Loafman]

* Go back to standard tests, no master image. [Kenneth Loafman]

* Add testing for Python 3.11. [Kenneth Loafman]

* Update deprecation messages.  Cleanup. [Kenneth Loafman]

* Reformat / cleanup Makefile. [Kenneth Loafman]

* Fixup help entries in Makefile. [Kenneth Loafman]

* Remove targets xlate-*.  Add target pot. [Kenneth Loafman]

* Change Crowdin commit message. [Kenneth Loafman]

* Update po/duplicity.pot. [Kenneth Loafman]

* Cleanup and make sure setup cleans po dir. [Kenneth Loafman]

* Fix version, oversight in previious commit. [ede]

  [ci_skip]

* Fix snap build for non-amd64 archs. [ede]

  [ci_skip]

* Add filter mode to log line.  #138. [Kenneth Loafman]

* Fix emacs mode line. [Kenneth Loafman]

### Fix

* Fix for issue #683. [Kenneth Loafman]

  - ngettext() is returning empty string on plural and zero counts.   -
  go back to plain gettext() and use just a single translation.   -
  modify test to run backup using all translations we have.

* Azure Blob Storage backend fails to resume.  Fixes #149. [Kenneth Loafman]

* Went to aggressive on cleanup(). [Kenneth Loafman]

* Fix about 20 pep8 issues. [Kenneth Loafman]

* More fixes to po/update-po. [Kenneth Loafman]

* Fix po/update-pot to leave po/LINGUAS in po. [Kenneth Loafman]

* Run po/update-pot. [Kenneth Loafman]


## rel.1.0.1 (2022-10-03)

### Changes

* Various cleanups to code and tests. [Kenneth Loafman]

* Accept all .po files for update-pot. [Kenneth Loafman]

* Build control files for update-pot. [Kenneth Loafman]

* Accept all .po files for LINGUAS gen. [Kenneth Loafman]

* Build control files for update-pot. [Kenneth Loafman]

* Add tags to commit message. [Kenneth Loafman]

### Fix

* Revert changes to gpg\_failed(). [Kenneth Loafman]

  - fixes #147 - Regression: change of encryption password.   - note -
  GPG only returns 0,1,2.  Not sufficient for errors.   - also added
  testing/manual/issue147.sh.

### Other

* Update Crowdin configuration file. [Kenneth Loafman]

* Update Crowdin configuration file. [Kenneth Loafman]

* Update Crowdin configuration file. [Kenneth Loafman]

* Update Crowdin configuration file. [Kenneth Loafman]

  Update Crowdin configuration file
  Update Crowdin configuration file


## rel.1.0.0 (2022-09-23)

### Changes

* Update README-SNAP.md to show options. [Kenneth Loafman]

* Add instructions for building snaps. [Kenneth Loafman]

* Add missing license metadata. [ede]

  [ci_skip]

* More docker cleanup. [Kenneth Loafman]

  - Add rclone to package installs.

* Trigger website rebuild on pushes/tags. [ede]

* More docker cleanup. [Kenneth Loafman]

  - remove copy of setup.py, not used   - add testit.py for basic
  testing

* More docker cleanup. [Kenneth Loafman]

  - use 'docker compose' not docker-compose   - remove more unused items

* Optimize build of duplicity\_test image. [Kenneth Loafman]

  - use buildkit to speed up build,   - split huge layers into smaller
  ones   - changes in testing dir trigger pipeline

* Fold requirements.dev into requirements.txt.  Del requirements.dev. [Kenneth Loafman]

* Fold requirements.dev into requirements.txt.  Del requirements.dev. [Kenneth Loafman]

* Fold requirements.dev into requirements.txt.  Del requirements.dev. [Kenneth Loafman]

* Extend code\_test to testing directory. [Kenneth Loafman]

  - Fix or mark issues found.   - Will not run under py27.

* Fix .md formatting. [Kenneth Loafman]

* Mark slow tests > 10sec.  Use -m "not slow". [Kenneth Loafman]

* Ref requirements.dev in install. [Kenneth Loafman]

* Ref requirements files instead of listing in duplicate. [Kenneth Loafman]

* Action and Audience must be lowercased. [Kenneth Loafman]

* Nuke skip tests and skip ci in CHANGELOG.md. [Kenneth Loafman]

* New os\_options for SWIFT backend. [Florian Perrot]

* Clarify when --s3-endpoint-url,-region-name are needed. [ede]

* Change from master to main branch naming. [Kenneth Loafman]

* Better defaults for S3 mac procs and chunk sizing. [Josh Goebel]

* --s3\_multipart\_max\_procs applies to BOTO3 backend also. [Josh Goebel]

* Migrate to unittest.mock. [Gwyn Ciesla]

* Fix modeline, change utf8 to utf-8 to make emacs happy. [Kenneth Loafman]

* Replace pexpect.run with subprocess\_popen in par2backend. [Kenneth Loafman]

* Fix PEP8 issue. [Kenneth Loafman]

* Add py310 to list of versions supported. [Kenneth Loafman]

* Fix script pushsnap to handle errors. [Kenneth Loafman]

* Add returncode to BackendException for rclonebackend. [Kenneth Loafman]

* Snap use core20 coreutils if none in PATH env var. [ede]

  add "/snap/core20/current/usr/bin" to PATH

* Need to install python3 for pages. [Kenneth Loafman]

* Don't push to savannah any more. [Kenneth Loafman]

* Fix version for builds. [Kenneth Loafman]

### Fix

* Replace pydrive with pydrive2. Fixes #62. [Kenneth Loafman]

* GDrive backend: Add environment args for configuring oauth flow. [Patrick Riley]

* GDrive backend: For Google OAuth, switch to loopback flow. [Patrick Riley]

* Reduce number of GPG file descriptors, add GPG translatable errors. [Kenneth Loafman]

* Remove sign-build step.  Does not work. [Kenneth Loafman]

* Add back overzealous removal of 'import re'. [Kenneth Loafman]

* Webdav listing failed on responses with namespace 'ns0' [Felix Prüter]

* Fix build of apsw/sqlite3 bundle.  Don't store apsw in repo. [Kenneth Loafman]

* Make sure that FileChunkIO#name is a string, not a bytes-like object. [Josh Goebel]

* Fix possible memory leaks.  Fixes #128.  Fixes #129. [Kenneth Loafman]

* Additional fixes/checks for pexpect version.  Fixes #125. [Kenneth Loafman]

  - Add check to ssh_pexpect_backend, par2backend, for version < 4.5.0
  - Skip test for par2backend instance if version < 4.5.0

* Fixes #125.  Add use\_poll=True to pexpect.run in par2backend. [Kenneth Loafman]

  - allows way too many incrementals to operate.   - regression test,
  issue125.sh, added to manual.

* Fix issue #78 - Retry on SHA1 mismatch. [Kenneth Loafman]

* Add missing double quote. [ede]

* Install requirements.dev. [Kenneth Loafman]

### Other

* Doc: some reformatting for better readability. [ede]

* Doc: clarify when --s3-endpoint-url,-region-name are need. [ede]


## rel.0.8.23 (2022-05-15)

### New

* Add --webdav-headers to webdavbackend.  Fixes #94. [Kenneth Loafman]

* Add tests for Python 3.10. [Kenneth Loafman]

* Make sdist only provide necessary items for build. [Kenneth Loafman]

* Add changelog to deploy stage to build CHANGELOG.md. [Kenneth Loafman]

  - make job changelog to run tools/makechangelog in CI/CD.   - make
  jobs build_pip and build_snap require changelog.

* Document rclone option setting via env vars. [edeso]

* Enable CI snapcraft amd64 builds with docker. [edeso]

  .gitlab-ci.yml   job build_snap based on a working docker image
  commented 'only:' limitiation, it's manual anyway   used split out
  tools/installsnap step   upload artifact (duplicity-*.snap) regardless
  - so it can be downloaded and debugged   - keep it for 30 deays by
  default
  snap/snapcraft.yaml   - fixup PYTHONPATH
  new 'tools/installsnap' that detects and works with docker
  tools/testsnap   remove installation step   remove double test entries
  change testing to use gpg and compression

* Document rclone option setting via env vars. [edeso]

* Fix other archs, expose rdiffdir. [edeso]

  fix remote build of armhf, arm64, ppc64el   arm64 was tested on Debian
  11 arm64   rdiffdir now avail as /snap/bin/duplicity.rdiffdir   remove
  obsolete folder /usr/lib/python3.9/ in snap

* Demote boto backend to legacy ... [ede]

  usable via boto+s3:// or boto+gs:// now only   removed s3+http://
  scheme   added --s3-endpoint-url option as replacement   added
  --s3-use-deep-archive option   changes are document in man page commit
  of the same patch set

* Promote boto3 backend to default s3:// backend ... [ede]

  add --s3-unencrypted-connection support

* Man page, major sorting, reformatting, S3/GCS documentation update. [ede]

  some updates, added s3 options, clarifications   updated Notes on S3
  and Google Cloud Storage usage   sort Options, Url Formats, Notes on
  alphabetically   consistently use "NOTE:"   indent properly all over

### Changes

* Use cicd image hosted on GitLab. [Kenneth Loafman]

* Create singular container for testing. [Kenneth Loafman]

* Fix PEP8 issue. [Kenneth Loafman]

* Remove build on merge request and unused variables. [Kenneth Loafman]

* Cosmetic changes only. [Kenneth Loafman]

* Make pages manual deploy. [Kenneth Loafman]

* Changelog removed, remove needs. [Kenneth Loafman]

* Only build pip and snap, don't push. [Kenneth Loafman]

* Fix misspelled stage name. [Kenneth Loafman]

* Fix deps format. [Kenneth Loafman]

* Fix deps format. [Kenneth Loafman]

* Add requirements.dev to tox.ini. [Kenneth Loafman]

* Include pydevd in requirements.txt. [Kenneth Loafman]

* Go back to ubuntudesktop/gnome-3-38-2004. [Kenneth Loafman]

* Add tools dir to changes list in deploy-template. [Kenneth Loafman]

* Try snap with utuntu:20.04. Fix artifacts loc. [Kenneth Loafman]

* Some debugging statements. [Kenneth Loafman]

* Some debugging statements. [Kenneth Loafman]

* Set up the SSH key and the known\_hosts file. [Kenneth Loafman]

* Set up config for git. [Kenneth Loafman]

* Clone repo so setuptools-scm works properly. [Kenneth Loafman]

* Move setuptools* to .dev.  Nuke report.xml artifact. [Kenneth Loafman]

* Add some more requirements. [Kenneth Loafman]

* Install git and intltool for changelog. [Kenneth Loafman]

* Add changes: to deploy-template. [Kenneth Loafman]

* Fix syntax. [Kenneth Loafman]

* Minimize CI/CD overhead. [Kenneth Loafman]

* Split requirements into .txt and .dev. [Kenneth Loafman]

  .txt - normal user   .dev - developer

* Standardize startup sequence. [Kenneth Loafman]

* Remove deploy jobs needing secret keys. [Kenneth Loafman]

* Do not supply user/password to twine, just access token. [Kenneth Loafman]

* Do not supply user/password to twine, just access token. [Kenneth Loafman]

* Add default never to .test-template. [Kenneth Loafman]

* Change PYPI\_ACCESS\_TOKEN back to variable and just echo it. [Kenneth Loafman]

* Just cp PYPI\_ACCESS\_TOKEN to \~/.pypirc. [Kenneth Loafman]

* Fix usage of PYPI\_ACCESS\_TOKEN. [Kenneth Loafman]

* Set to run deploy only after a push event. [Kenneth Loafman]

* Whoops, can't run deploy on source branch to merge. [Kenneth Loafman]

* Use rules in templates.  Always run on merge requests. [Kenneth Loafman]

* Always run pipeline on merge request event. [Kenneth Loafman]

* Make sure we run all during merge requests. [Kenneth Loafman]

* Add deploy-template to only run when source changes. [Kenneth Loafman]

* Fix to only run tests if source code changes. [Kenneth Loafman]

* If no changes, exit 0 to allow pip and snap builds. [Kenneth Loafman]

* Set up pypi access token for uploading. [Kenneth Loafman]

* Keep pip build artifacts for 30 days as pipeline artifacts. [ede]

* Skip tests, not ci, so we can build snaps, pips, pages, etc. [Kenneth Loafman]

* Allow non-Docker environs to sign snaps. [Kenneth Loafman]

* Allow GitLab CI to upload snaps to the store. [Kenneth Loafman]

  still have not figured out how to store sign key on GitLab

* Update or add copyright and some cosmetic changes. [Kenneth Loafman]

* Remove install of snapcraft, snap, snapd. [Kenneth Loafman]

* Add grpcio-tools to top to get latest version. [Kenneth Loafman]

  This leaves two unresolvable problems (upper version conflicts):
  ERROR: mediafire 0.6.0 has requirement requests<=2.11.1,>=2.4.1, but
  you'll have requests 2.27.1 which is incompatible.   ERROR: python-
  novaclient 2.27.0 has requirement pbr<2.0,>=1.6, but   you'll have pbr
  5.8.1 which is incompatible.

* Remove conflicting build env variable.  Nuke evil tabs. [Kenneth Loafman]

* Allow duplicity-core20 to run deploy steps, for now. [Kenneth Loafman]

* Install snapcraft snap snapd. [Kenneth Loafman]

* Allow pip and snap builds from branches for now. [Kenneth Loafman]

* Add build\_snap and build\_pip back. [Kenneth Loafman]

* More tests for tools/testsnap. [Kenneth Loafman]

  add backup/verify runs to check major pathways   add multi-lib check
  to avoid SnapCraft bug 1965814

* More snapcraft.yaml fixups. [Kenneth Loafman]

  break up long strings for better readability   preload pbr and
  requests to avoid most version warnings   pbr and requests are now at
  latest version, not ancient

* Add further checks to testing for backup and multi-lib. [Kenneth Loafman]

* Remove SNAPCRAFT\_PYTHON\_INTERPRETER per edso, no change on U20. [Kenneth Loafman]

* Try to force Python 3.8 only. [Kenneth Loafman]

* More detailed error message. [Kenneth Loafman]

* Divide makesnap into makesnap, testsnap, and pushsnap. [Kenneth Loafman]

* Revert to core18.  core20 is still unusable. [Kenneth Loafman]

### Fix

* Fix LP bug #1970124 - obscure error message. [Kenneth Loafman]

  Fixes handling of error message with real path, not temp path.

* Nuke a couple of false pylint errors, use inline disable. [Kenneth Loafman]

* Nuke a couple of false pylint errors, fix spelling. [Kenneth Loafman]

* Nuke a couple of false pylint errors. [Kenneth Loafman]

* Minor formatting fix. [ede]

  /builds/duplicity/duplicity/duplicity/backends/s3_boto3_backend.py:93:
  81: W291 trailing whitespace

* Fixup some minor formatting issues. [ede]

  /builds/duplicity/duplicity/duplicity/backends/s3_boto3_backend.py:92:
  121: E501 line too long (159 > 120 characters)   /builds/duplicity/dup
  licity/duplicity/backends/s3_boto3_backend.py:227:58: W292 no newline
  at end of file   /builds/duplicity/duplicity/duplicity/backends/s3_bot
  o_backend.py:34:1: W391 blank line at end of file

### Other

* Pkg:fix: make extra sure correct python binary is used. [edeso]

  remove unmaintained changelog   add shell wrapper(launcher.sh)   add
  debug script   use shell wrapper as snap binary ignores PATH for
  python binary on debian

* Optimize CI/CD to only run when needed. [Kenneth Loafman]

* Upgrade to base core20. [Kenneth Loafman]

* Switch website to gitlab.io, promote duplicity.us. [ede]

* Fix website link. [ede]


## rel.0.8.22 (2022-03-04)

### New

* Minimize testing/manual/issue98.sh for issue #98. [Kenneth Loafman]

* Add testing/manual/issue98.sh to test issue #98. [Kenneth Loafman]

* Add Getting Versioned Source to README-REPO.md. [Kenneth Loafman]

  [no ci]

* Test case for issue 103 multi-backend prefix affinity. [Kenneth Loafman]

* Add --use-glacier-ir option for instant retrieval.  Fixes #102. [Kenneth Loafman]

* Add --par2-volumes entry to man page. [Kenneth Loafman]

* Add manual test for issue 100. [Kenneth Loafman]

* Add option --show-changes-in-set <index> to collection-status. [Kenneth Loafman]

  Patches provided by Peter Canning (@pcanning).  Closes #99.

### Changes

* Changes to run on Focal with core20. [Kenneth Loafman]

* Use multiple -m options on commit to split comment. [Kenneth Loafman]

* Remove build-pip and build-snap.  Build locally for now. [Kenneth Loafman]

* Remove build-pip and build-snap.  Build locally for now. [Kenneth Loafman]

* Swap over to image 'cibuilds/snapcraft:core20`. [Kenneth Loafman]

* Swap over to image 'cibuilds/snapcraft:core20`. [Kenneth Loafman]

* Swap over to image 'cibuilds/snapcraft:core20`. [Kenneth Loafman]

* Swap over to image 'cibuilds/snapcraft:core20`. [Kenneth Loafman]

* Swap over to image 'cibuilds/snapcraft:core20`. [Kenneth Loafman]

* Swap over to image 'cibuilds/snapcraft:core20`. [Kenneth Loafman]

* Remove sudo. [Kenneth Loafman]

* Swap over to image 'cibuilds/snapcraft:core20`. [Kenneth Loafman]

* Core20 usess py38, not py36. [Kenneth Loafman]

* Core20 usess py38, not py36. [Kenneth Loafman]

* Attempt core20 again. [Kenneth Loafman]

* Fix syntax. [Kenneth Loafman]

* Remove unneeded Dockerfiles.  Rename. [Kenneth Loafman]

* Try remote snap build. [Kenneth Loafman]

* Remove unneeded Dockerfiles.  Rename. [Kenneth Loafman]

* Cosmetic fixes. [Kenneth Loafman]

* Try forcing snaps to use python3.6 in 18.04. [Kenneth Loafman]

* Add check for correct platform. [Kenneth Loafman]

* Use snapcraft snap instead of deb.  See LP bug 1948597. [Kenneth Loafman]

* Use snapcraft snap instead of deb.  See LP bug 1948597. [Kenneth Loafman]

* Use snapcraft snap instead of deb.  See LP bug 1948597. [Kenneth Loafman]

* Use snapcraft snap instead of deb.  See LP bug 1948597. [Kenneth Loafman]

* Use snapcraft snap instead of deb.  See LP bug 1948597. [Kenneth Loafman]

* Use snapcraft snap instead of deb.  See LP bug 1948597. [Kenneth Loafman]

* Use snapcraft snap instead of deb.  See LP bug 1948597. [Kenneth Loafman]

* Use snapcraft snap instead of deb.  See LP bug 1948597. [Kenneth Loafman]

* Add warning for replicate command.  See issue #98. [Kenneth Loafman]

* Minor tweaks. [Kenneth Loafman]

* Add wheels to .gitignore. [Kenneth Loafman]

* Cosmetic changes. [Kenneth Loafman]

* Add collection-status at end of test. [Kenneth Loafman]

* Remove gpg socket files during clean. [Kenneth Loafman]

* Back off to default image. [Kenneth Loafman]

  [skip-tests]

* Try adding apt-get upgrade. [Kenneth Loafman]

  [skip-tests]

* Add .test-template to allow skipping qual and tests. [Kenneth Loafman]

  [skip-tests]

* Try build with apt-get update. [Kenneth Loafman]

* Try building snap on 20.04. [Kenneth Loafman]

* Add targets to manually import/export translations. [Kenneth Loafman]

* Update duplicity.pot for LP translation. [Kenneth Loafman]

* Revert "Put out first 'post' release to fix pypi issue". [Kenneth Loafman]

* Put out first 'post' release to fix pypi issue. [Kenneth Loafman]

* Rename AUTHORS to CONTRIBUTING.md. [Kenneth Loafman]

* Rename dist dir to tools to avoid collision with setuptools. [Kenneth Loafman]

* Add line wrap to changelog process, body and subject. [Kenneth Loafman]

### Fix

* Add --no-files-changed option.  Fixes issue #110. [Kenneth Loafman]

* Fix use of sorted() builtin (does not sort in place). [Kenneth Loafman]

* Revert snapcraft.yaml to build on core18.  core20 was flakey. [Kenneth Loafman]

* Fix #107 - TypeError in restart\_position\_iterator. [Kenneth Loafman]

* Need to pass kwargs to BaseIdentitu. [Kenneth Loafman]

* Fix \_\_init\_\_ in hubic.py.  Fixes #106. [Kenneth Loafman]

* Try building snap on core20. [Kenneth Loafman]

* Try building snap on core20. [Kenneth Loafman]

* Somehow missed boto when doing #102.  Now supported. [Kenneth Loafman]

* Fix logic of skipIf test. [Kenneth Loafman]

* Fix data\_files AUTHORS to CONTRIBUTING.md. [Kenneth Loafman]

### Other

* Revert "chg:dev:core20 usess py38, not py36." [Kenneth Loafman]

  This reverts commit b5e4baac09b4533c2395aa392a0b8c170fb1a052.

* Slate Backend. [Shr1ftyy]

* Skip tests for ppc64le also. [Mikel Olasagasti Uranga]


## rel.0.8.21 (2021-11-09)

### New

* Add release-prep.sh for release preparation. [Kenneth Loafman]

* Add py310 to envlist to test against python 3.10. [Kenneth Loafman]

* Add update of API docs to deploy step. [Kenneth Loafman]

### Changes

* When buiilding for amd64 build snap locally, else remote. [Kenneth Loafman]

* Fix build of pages. [Kenneth Loafman]

* Switch over to sphinx-rtd-theme. [Kenneth Loafman]

* Fix command line warning messages. [Kenneth Loafman]

* Fix clean command to include module doc .rst files. [Kenneth Loafman]

* Nuke generated .rst files. [Kenneth Loafman]

* Nuke before\_script.  [ci skip] [Kenneth Loafman]

* Move html to public dir. [Kenneth Loafman]

* Forgot to add myst-parser.  Comment out tests for now. [Kenneth Loafman]

* Back to alabaster theme.  Port changes from sqlite branch. [Kenneth Loafman]

* Remove Dockerfiles for .10 versions. [Kenneth Loafman]

* Fix some rst errors in docstrings.  Add doctest module. [Kenneth Loafman]

* Fixes to make API docs work right. [Kenneth Loafman]

* Whoops, left out import sys. [Kenneth Loafman]

* Skip test to allow py27 and py35 to pass. [Kenneth Loafman]

* Some tweaks to run cleaner. [Kenneth Loafman]

* Fix typo in test selection. [Kenneth Loafman]

* Remove redundant call to pre\_process\_download\_batch. [Kenneth Loafman]

* Fix mismatch between pre\_process\_download[\_batch] calls. [Kenneth Loafman]

  Implement both in backend and multibackend if hasattr True.

### Fix

* Fix #93 - dupliicity wants private encryption key. [Kenneth Loafman]

* PAR2 backend failes to create par2 file with spaces in name. [Kenneth Loafman]

* Fix bug 930151 - Restore symlink changes target attributes (2) [Kenneth Loafman]

* Fix LP bug 930151 - Restore a symlink changes target attributes. [Kenneth Loafman]

* Fix #89 part 2 - handle small input files where par2 fails. [Kenneth Loafman]

* Fix theme name, sphinx\_rtd\_theme. [Kenneth Loafman]

* Fix PEP8 issue. [Kenneth Loafman]

* Fix #90 - rclone backend fails with spaces in pathnames. [Kenneth Loafman]

* Fix #89 - Add PAR2 number volumes option. [Kenneth Loafman]

* Fix #88 - Add PAR2 creation failure error message. [Kenneth Loafman]

* Fix bug #87, Restore fails and stops on corrupted backup volume. [Kenneth Loafman]

* Fix bug #86, PAR2 backend fails on restore, with patch supplied. [Kenneth Loafman]

* Fixed Catch-22 in pyrax\_identity.hubic.  Debian bug #996577. [Kenneth Loafman]

  Name error on backend HubiC (Baseidentity).  Cannot avoid importing
  pyrax since HubicIdentity requires pyrax.base_identity.BaseIdentity.

* Fix PEP8 style errors. [Kenneth Loafman]

* Fix issue #81 - Assertion fail when par2 prefix forgotten. [Kenneth Loafman]

* Test with mirror and stripe modes. [Kenneth Loafman]

* Fix issue #79 - Multibackend degradation. [Kenneth Loafman]

* Add verbose exception on progress file failure. [Kenneth Loafman]

### Other

* Resolve os option key naming mismatch. [Johannes Winter]

* Set up gdrive client credentials scope correctly. [Christopher Haglund]

* Don't query for filesize. [Johannes Winter]

* Upgrade docker test environment. [Johannes Winter]

* Merge branch 'master' of gitlab.com:duplicity/duplicity. [Kenneth Loafman]

* Fix TypeError. [Clemens Fuchslocher]

* SSHPExpectBackend: Implement \_delete\_list method. [Clemens Fuchslocher]

* MultiBackend: Don't log username and password. [Clemens Fuchslocher]

* Fix NameError. [Clemens Fuchslocher]

* Onedrive: Support using an external client id / refresh token. [Michael Terry]

* Fix functional tests when \_runtestdir is not /tmp. [Guillaume Girol]

* Allow to override manpage date with SOURCE\_DATE\_EPOCH. [Bernhard M. Wiedemann]

  in order to make builds reproducible.   See https://reproducible-
  builds.org/ for why this is good   and https://reproducible-
  builds.org/specs/source-date-epoch/   for the definition of this
  variable.
  Also use UTC/gmtime to be independent of timezone.

* Improved management of volumes unsealing for PCA backend For PCA
backend, unseal all volumes at once when restoring them instead of
unsealing once at a time. Use pre\_process\_download method already
available in dup\_main. Need to implement it on BackendWrapper and
Multibackend as well. [Erwan B]


## rel.0.8.20 (2021-06-26)

### New

* Better looping.  Increase to 100 loops. [Kenneth Loafman]

### Changes

* Build\_ext now builds inplace for development ease. [Kenneth Loafman]

* Log difftar filename where kill happened. [Kenneth Loafman]

* Remove lockfile to avoid user confusion. [Kenneth Loafman]

* Allow customization. [Kenneth Loafman]

* Fix Support DynamicLargeObjects inside swift backend. [Mathieu Le Marec - Pasquet]

  Use high levels APIS to both:
  - correctly delete multipart uploads   - correctly handle multipart
  uploads
  This fixes [launchpad
  #557374](https://answers.launchpad.net/duplicity/+question/557374)

* Fix makechangelog to output actual problems. [Kenneth Loafman]

* Add dependency scanning. [Kenneth Loafman]

* Make sure changelog is only change to commit. [Kenneth Loafman]

* Fix indentation. [Kenneth Loafman]

* Add support for --s3-multipart-chunk-size, default 25MB. [Kenneth Loafman]

  Fixes issue #61

* Add interruptable:true as default. [Kenneth Loafman]

* Fix snapcraft commands. [Kenneth Loafman]

* Fix snaplogin file use. [Kenneth Loafman]

* Add deployment for pip and snap builds. [Kenneth Loafman]

* Add build\_pip job. [Kenneth Loafman]

* Fix PEP8 issue. [Kenneth Loafman]

* More cleanup for snap builds. [Kenneth Loafman]

* Move arch selection to dist/makesnap. [Kenneth Loafman]

* Try snap build on all architectures. [Kenneth Loafman]

* Build for i386, amd64, armhf. [Kenneth Loafman]

* Move to remote build of armfh and amd64. [Kenneth Loafman]

* Attempt remote build of armfh. [Kenneth Loafman]

* More cleanup on requirements. [Kenneth Loafman]

* Megatools no longer supports py35. [Kenneth Loafman]

* Get more stuff from pypi than repo.  Some cleanup. [Kenneth Loafman]

* Fix spaces before inline comments. [Kenneth Loafman]

* Enable access-member-before-definition in pylintrc. [Kenneth Loafman]

* Fix indentation. [Kenneth Loafman]

* Fix formatting in A NOTE ON GDRIVE BACKEND.  Minor. [Kenneth Loafman]

* Module gdata still does not work on py3. [Kenneth Loafman]

* Tweak requirements for gdrivebackend.  Cosmetic changes. [Kenneth Loafman]

### Fix

* Fix test file count after deleting lockfile. [Kenneth Loafman]

* Release lockfile only once. [Kenneth Loafman]

* Release lockfile only once. [Kenneth Loafman]

* Support -o{Global,User}KnownHostsFile in --ssh-options. [Kenneth Loafman]

  Fixes issue #60

* Add pydrive2 to requirements.txt. [Kenneth Loafman]

  Fixes #62.  pydrivebackend was updated to pydrive 2 over a year ago,
  but   the requirements.txt file was not updated to reflect this.

* Fix error message on gdrivebackend. [Kenneth Loafman]

* Fix issue #57 SSH backends - IndexError: list index out of range. [Kenneth Loafman]

### Other

* Don't skip CI. [Kenneth Loafman]

* Add support for new b2sdk V2 API. [Adam Jacobs]

* Have duplicity retry validate\_block so object storage can report
correct size. [Doug Thompson]

* Replace b2sdk private API references in b2backend with public API. [Adam Jacobs]

* Update b2 backend to use *public* b2sdk API. [Adam Jacobs]

* B2sdk 1.8.0 refactored minimum\_part\_size to recommended\_part\_size
(the value used stays the same) [Adam Jacobs]

  It's a breaking change that makes duplicity fail with the new SDK.
  This fix makes duplicity compatible with both pre- and post- 1.8.0
  SDKs.

* Added Google MyDrive support updated man pages and --help text. [Anthony Uphof]


## rel.0.8.19 (2021-04-29)

### Changes

* Display merge comments.  Better formatting. [Kenneth Loafman]

* Clean up readability.  Minor changes. [Kenneth Loafman]

* Cosmetic chnges. [Kenneth Loafman]

* Make testing/manual/bug1893481 into a tarball, not directory. [Kenneth Loafman]

* Add Makefile and update docs. [Kenneth Loafman]

* Remove installs common between before\_script: and script: [Kenneth Loafman]

* Remove installs common between before\_script: and script: [Kenneth Loafman]

### Fix

* Gdata module passes on py27 only. [Kenneth Loafman]

* Restore pylintrc, add requirement. [Kenneth Loafman]

* Fix unadorned string in restored pylint test. [Kenneth Loafman]

* Restored pylint test.  Fixed one issue found. [Kenneth Loafman]

* More py27 packages bit the dust. [Kenneth Loafman]

* Util.uexec() will return u'' if no err msg in e.args. [Kenneth Loafman]

* Util.uexec() should check for e==None on entry. [Kenneth Loafman]

* Mark skip those not usable on py27. Fix version. [Kenneth Loafman]

* Uncomment backends.  Mark skip those not usable on py27. [Kenneth Loafman]

* Lock in some module versions to last supporting py27. [Kenneth Loafman]

* Allow py27 to fail CI.  Restrict mock pkg to 3.05. [Kenneth Loafman]

* Fix bug #1547458 - more consistent passphrase prompt. [Kenneth Loafman]

* Fixes bug #1454136 - SX backend issues. [Kenneth Loafman]

* Fixes bug 1918981 - option to skip trash on delete on mediafire. [Kenneth Loafman]

  Added --mf-purge option to bypass trash

* Fix bug 1919017 - MultiBackend reports failure on file deletion. [Kenneth Loafman]

* Recomment, py2 does not support all backends. [Kenneth Loafman]

* Add azure-storage module requirement.  Uncomment all. [Kenneth Loafman]

* Remove requirement for python3-pytest-runner.  Not used. [Kenneth Loafman]

* Install older version of pip before py35 deprecation. [Kenneth Loafman]

* Add py27 and py35 back to CI. [Kenneth Loafman]

* Fix setup.py to handle Python 2 properly. [Kenneth Loafman]

* Fixes #41 - par2+rsync (non-ssh) fails. [Kenneth Loafman]

### Other

* Fix "Giving up after 5 attempts. timeout: The read operation timed
out" [Christian Perreault]

* Don't sync when removing old backups. [Matthew Marting]

* Fix util.uexc: do not return None. [Michael Kopp]

* Implement Box backend. [Jason Wu]

* Implement megav3 backend to to cater for change in MEGACmd. [Jason Wu]

* Fix documentation for azure backend. [Michael Kopp]

* Fix typo. [Moses Miller]

* Add IDrive backend. [SmilingM]

* Progress bar improvements. [Moses Miller]

* Fix;usr:Fixes bug #1652953 - seek(0) on /dev/stdin crashes. [Kenneth Loafman]

* Add a new Google Drive backend (gdrive:) [Jindřich Makovička]

  - Removes the PyDrive/PyDrive2 dependencies, and depends only on the
  Google API client libraries commonly available in distributions.
  - Uses unchanged JSON secret files as downloaded from GCP
  - Updates the Google Drive API to V3

* Replaced original azure implementation. [Erwin Bovendeur]

* Fixed code smells. [Erwin Bovendeur]

* Azure v12 support. [Erwin Bovendeur]

* Revert "fix:pkg:Remove requirement for python3-pytest-runner.  Not
used." [Kenneth Loafman]

  This reverts commit c7cbc6bd531f90be1ea9a65cc237e1017dd935f4.

* List required volumes when called with 'restore --dry-run' [Matthias Blankertz]

  When restoring in dry-run mode, and with the manifest available, list
  the volumes that would be gotten from the backend when actually
  performing the operation.   This is intended to aid users of e.g. the
  S3 backend with (deep) glacier   storage, allowing the following
  workflow to recover files, optionally at   a certain time, from a
  long-term archive:   1. duplicity restore --dry-run [--file-to-restore
  <file/dir>] [--time <time>] boto3+s3://...   2. Start a Glacier
  restore process for all the listed volumes   3. duplicity restore
  [--file-to-restore <file/dir>] [--time <time>] boto3+s3://...

* Fix sorting of BackupSets by avoiding direct comparison. [Stefan Wehrmeyer]

  Sorting should only compare their time/end_time, not BackupSets
  directly   Closes #42

* Update mailing list link. [Chris Coutinho]

* Fixes #16 - Move from boto to boto3. [Kenneth Loafman]

* Py27 EOL 01/2020, py35 EOL 01/2021, remove tests. [Kenneth Loafman]

* Remove 2to3 from ub16 builds. [Kenneth Loafman]

* Move py35 back to ub16, try 2. [Kenneth Loafman]

* Move py35 back to ub16. [Kenneth Loafman]

* Move py27 tests to ub16 and py35 tests to ub18. [Kenneth Loafman]

* Fixes #16 - Move from boto to boto3. [Kenneth Loafman]

* Py27 EOL 01/2020, py35 EOL 01/2021, remove tests. [Kenneth Loafman]

* Move py27 tests to ub16 and py35 tests to ub18. [Kenneth Loafman]

  Move py35 back to ub16.
  Move py35 back to ub16, try 2.
  Remove 2to3 from ub16 builds.

* Fixes #33, remove quotes from identity filename option. [Kenneth Loafman]

* Fix to correctly build \_librsync.so. [Kenneth Loafman]

* Fix to add --inplace option to build\_ext. [Kenneth Loafman]

* Rename pylintrc to .pylintrc. [Kenneth Loafman]

* Multibackend: fix indentation error that was preventing from
registering more than one affinity prefix per backend. [KheOps]

* Move testfiles dir to a temp location. [Kenneth Loafman]

  - was crashing LiClipse/Eclipse when present in project.   - so far
  only Darwin and Linux are supported, default Linux.   - Darwin uses
  'getconf DARWIN_USER_TEMP_DIR' for temp dir.   - Linux uses TMPDIR,
  TEMP, or defaults to /tmp.

* Update .gitlab-ci.yml to need code test to pass. [Kenneth Loafman]

* Remove basepython in code and coverage tests. [Kenneth Loafman]

* Add report.xml. [Kenneth Loafman]

* Bulk replace testfiles with /tmp/testfiles. [Kenneth Loafman]

* Skip unicode tests that fail on non-Linux systems like macOS. [Kenneth Loafman]


## rel.0.8.18 (2021-01-09)

### Other

* Onedrive: Support using an external client id / refresh token. [Michael Terry]

* Update .gitlab-ci.yml to need code test to pass. [Kenneth Loafman]

* Fix issue #26 Backend b2 backblaze fails with nameprefix restrictions. [Kenneth Loafman]

* Fix issue #29 Backend b2 backblaze fails with nameprefix restrictions. [Kenneth Loafman]

* Fix unadorned strings. [Kenneth Loafman]

* Report errors if B2 backend does exist but otherwise fails to import. [Phil Ruffwind]

  Sometimes import can fail because one of B2's dependencies is broken.
  The trick here is to query the "name" attribute of ModuleNotFoundError
  to see if B2 is the module that failed. Unfortunately this only works
  on   Python 3.6+. In older versions, the original behavior is
  retained.
  This partially mitigates the issue described in
  https://github.com/henrysher/duplicity/issues/14.

* Add report.xml. [Kenneth Loafman]

* Remove basepython in code and coverage tests. [Kenneth Loafman]

* Fix pep8 warning. [Kenneth Loafman]

* Added option --log-timestamp to prepend timestamp to log entry. [Kenneth Loafman]

  The default is off so not to break anything, and is set to on when the
  option is present.  A Catch-22 hack was made since we had to get
  options   for the log before adding a formatter, yet the commandline
  parser needs   the logger.  Went old school on it.

* Improve. [Gwyn Ciesla]

* Improve patch for Python 3.10. [Gwyn Ciesla]

* Conditionalize for Python version. [Gwyn Ciesla]

* Patch for Python 3.10. [Gwyn Ciesla]


## rel.0.8.17 (2020-11-11)

### Other

* Fixup ignore\_regexps for optional text. [Kenneth Loafman]

* Fix issue #26 (again) - duplicity does not clean up par2 files. [Kenneth Loafman]

* Fix issue #26 - duplicity does not clean up par2 files. [Kenneth Loafman]

* Fix issue #25 - Multibackend not deleting files. [Kenneth Loafman]

* Adjust setup.py for changelog changes. [Kenneth Loafman]

* Delete previous manual changelogs. [Kenneth Loafman]

* Tools to make a CHANGELOG.md from git commits. [Kenneth Loafman]

  $ [sudo] pip install gitchangelog

* Make exclude-if-present more robust. [Michael Terry]

  Specifically, handle all the "common errors" when listing a directory
  to see if the mentioned file is in it. Previously, we had done a
  check for read access before listing. But it's safe to try to list
  and just catch the errors that happen.

* Drop default umask of 0077. [Michael Terry]

  For most backends, it doesn't actually take effect. And it can be
  confusing for people that back up to a drive that is ext4-formatted
  but then try to restore on a new system.
  If folks are worried about others accessing the backup files,
  encryption is the recommended path for that.
  https://gitlab.com/duplicity/duplicity/-/issues/24

* Comment out RsyncBackendTest, again. [Kenneth Loafman]

* Fix some unadorned strings. [Kenneth Loafman]

* Fixed RsyncBackendTeest with proper URL. [Kenneth Loafman]

* Fix issue #23. [Yump]

  Fix unicode crash on verify under python3, when symlinks have changed
  targets since the backup was taken.

* Rclonebackend now logs at the same logging level as duplicity. [Kenneth Loafman]

* Allow sign-build to fail on walk away.  Need passwordless option. [Kenneth Loafman]

* Fix --rename typo. [Michael Terry]

* Move back to VM build, not remote.  Too many issues with remote. [Kenneth Loafman]

* Escape single quotes in machine-readable log messages. [Michael Terry]

  https://gitlab.com/duplicity/duplicity/-/issues/21

* Uncomment review-tools for snap. [Kenneth Loafman]

* Whoops, missing wildcard '*'. [Kenneth Loafman]

* Changes to allow remote build of snap on LP. [Kenneth Loafman]

* Changes to allow remote build of snap on LP. [Kenneth Loafman]

* Add a pylint disable-import-error flag. [Kenneth Loafman]

* Change urllib2 to urllib.request in parse\_digest\_challenge(). [Kenneth Loafman]

* Fix Python 3.9 test in .gitlab-ci.yaml. [Kenneth Loafman]

* Fix Python 3.9 test in .gitlab-ci.yaml. [Kenneth Loafman]

* Add Python 3.9 to .gitlab-ci.yaml. [Kenneth Loafman]

* Add Python 3.9 to the test suite.  It tests sucessfuly. [Kenneth Loafman]

* Fix bug #1893481 again for Python2.  Missed include. [Kenneth Loafman]

* Fix bug #1893481 Error when logging improperly encoded filenames. [Kenneth Loafman]

  - Reconfigure stdout/stderr to use errors='surrogateescape' in Python3
  and errors='replace' in Python2.     - Add a manual test case to check
  for regression.


## rel.0.8.16 (2020-09-29)

### Other

* Merged in s3-unfreeze-all. [Kenneth Loafman]

* Wait for Glacier batch unfreeze to finish. [Marco Herrn]

  The ThreadPoolExecutor starts the unfreezing of volumes in parallel.
  However we can wait until it finishes its work for all volumes.
  This currently does _not_ wait until the unfreezing process has
  finished, but only until the S3 'restore()' operations have finished
  (which can take a bit time).
  The actual (sequential) pre_processing of the volumes to restore then
  waits for the actual unfreezing to finish by regularly checking the
  state of the unfreezing.

* Adorn string as unicode. [Marco Herrn]

* Utilize ThreadPoolExecutor for S3 glacier unfreeze. [Marco Herrn]

  Starting one thread per file to unfreeze from Glacier can start a huge
  amounts of threads in large backups.   Using a thread pool should cut
  this down to a more appropriate number of   threads.

* Refine codestyle according to PEP-8. [Marco Herrn]

* Adorn strings as unicode. [Marco Herrn]

* S3 unfreeze all files at once. [Marco Herrn]

  When starting a restore from S3 Glacier, start the unfreezing of all
  volumes at once by calling botos 'restore()' method for each volume in
  a   separate thread.
  This is only implemented in the boto backend, not in the boto3
  backend.

* Add boto3 to list of requirements. [Kenneth Loafman]

* Remove ancient CVS Id macro. [Kenneth Loafman]

* Merged in OutlawPlz:paramiko-progress. [Kenneth Loafman]

* Fixes paramiko backend progress bar. [Matteo Palazzo]

* Merged in lazy init for Boto3 network connections. [Kenneth Loafman]

* Initial crack at lazy init for Boto3. [Carl Alexander Adams]

* Record the hostname, not the fqdn, in manifest files. [Michael Terry]

  We continue to check the fqdn as well, to keep backward
  compatibility.
  https://bugs.launchpad.net/duplicity/+bug/667885

* Avoid calling stat when checking for exclude-if-present files. [Michael Terry]

  If a folder with rw- permissions (i.e. read and write, but no exec)
  is examined for the presence of an exclude-if-present file, we would
  previously throw an exception when trying to stat the file during
  Path object construction.
  But we don't need to stat in this case. This patch just calls
  listdir() and checks if the file is in that result.

* Fix build control files after markdown conversion. [Kenneth Loafman]

* Recover some changes lost after using web-ide. [Kenneth Loafman]

* Paperwork. [Kenneth Loafman]

* Set default values for s3\_region\_name and s3\_endpoint\_url. [Marco Herrn]

  Fixes #12

* Allow setting s3 region and endpoint. [Marco Herrn]

  This commit introduces the new commandline options     --s3-region-
  name     --s3-endpoint-url   to specify these parameters. This allows
  using s3 compatible providers   like Scaleway or OVH.
  It is probably useful for Amazon accounts, too, to have more fine
  grained influence on the region to use.

* Update README-REPO.md. [Kenneth Loafman]

* Make code view consistent. [Kenneth Loafman]

* Update setup.py. [Kenneth Loafman]

* Update README.md. [Kenneth Loafman]

* Paperwork. [Kenneth Loafman]

* Revert "Merge branch 's3-boto3-region-and-endpoint' into 'master'" [Kenneth Loafman]

  This reverts commit 16947e6aa490fd0cb96f1954b410c003c6a5b101,
  reversing   changes made to cf8bb66e8b87cf8b57680d6ab7a8a83ca9c955f9.

* Bump version for LP dev build. [Kenneth Loafman]


## rel.0.8.15 (2020-07-27)

### Other

* Always paperwork. [Kenneth Loafman]

* Allow setting s3 region and endpoint. [Marco Herrn]

  This commit introduces the new commandline options     --s3-region-
  name     --s3-endpoint-url   to specify these parameters. This allows
  using s3 compatible providers   like Scaleway or OVH.
  It is probably useful for Amazon accounts, too, to have more fine
  grained influence on the region to use.

* Fix missing FileNotUploadedError in pydrive backend. [Martin Sucha]

  Since 69eb0376ef6a1b32b8d6bf0f075247d49f06719e, FileNotUploadedError
  is not imported anymore, resulting in an exception in case   some of
  the files failed to upload. Adding the import back.

* Fixed indentation. [Joshua Chan]

* Added shared drive support to existing `pydrive` backend instead of a
new backend. [Joshua Chan]

* PydriveShared backend is identical to Pydrive backend, except that it
works on shared drives rather than personal drives. [Joshua Chan]

* Include the query when parsing the backend URL string, so users can
use it to pass supplementary info to the backend. [Joshua Chan]

* Fix caps on X-Python-Version. [Kenneth Loafman]

* Fix issue #10 - ppa:duplicity-*-git fails to install on Focal Fossa. [Kenneth Loafman]

  - Set correct version requirements in debian/control.

* Remove python-cloudfiles from suggestions. [Jairo Llopis]

  This dependency cannot be installed on Python 3:
  ```   #12 19.82   Downloading python-cloudfiles-1.7.11.tar.gz (330 kB)
  #12 20.00     ERROR: Command errored out with exit status 1:   #12
  20.00      command: /usr/local/bin/python -c 'import sys, setuptools,
  tokenize; sys.argv[0] = '"'"'/tmp/pip-install-2iwvh4bp/python-
  cloudfiles/setup.py'"'"'; __file__='"'"'/tmp/pip-
  install-2iwvh4bp/python-cloudfiles/setup.py'"'"';f=getattr(tokenize,
  '"'"'open'"'"', open)(__file__);code=f.read().replace('"'"'\r\n'"'"',
  '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))'
  egg_info --egg-base /tmp/pip-pip-egg-info-b1gvstfs   #12 20.00
  cwd: /tmp/pip-install-2iwvh4bp/python-cloudfiles/   #12 20.00
  Complete output (9 lines):   #12 20.00     Traceback (most recent call
  last):   #12 20.00       File "<string>", line 1, in <module>   #12
  20.00       File "/tmp/pip-install-2iwvh4bp/python-
  cloudfiles/setup.py", line 6, in <module>   #12 20.00         from
  cloudfiles.consts import __version__   #12 20.00       File "/tmp/pip-
  install-2iwvh4bp/python-cloudfiles/cloudfiles/__init__.py", line 82,
  in <module>   #12 20.00         from cloudfiles.connection     import
  Connection, ConnectionPool   #12 20.00       File "/tmp/pip-
  install-2iwvh4bp/python-cloudfiles/cloudfiles/connection.py", line 13,
  in <module>   #12 20.00         from    urllib    import urlencode
  #12 20.00     ImportError: cannot import name 'urlencode' from
  'urllib' (/usr/local/lib/python3.8/urllib/__init__.py)   #12 20.00
  ----------------------------------------   #12 20.00 ERROR: Command
  errored out with exit status 1: python setup.py egg_info Check the
  logs for full command output.   ```
  Also, it is no longer supported. Rackspace uses `pyrax` nowadays.
  Removing to avoid confusions.

* Update azure requirement. [Jairo Llopis]

  Trying to install `azure` today prints this error:
  ```   Collecting azure     Downloading azure-5.0.0.zip (4.6 kB)
  ERROR: Command errored out with exit status 1:        command:
  /usr/local/bin/python -c 'import sys, setuptools, tokenize;
  sys.argv[0] = '"'"'/tmp/pip-install-gzzfb6dp/azure/setup.py'"'"';
  __file__='"'"'/tmp/pip-install-
  gzzfb6dp/azure/setup.py'"'"';f=getattr(tokenize, '"'"'open'"'"',
  open)(__file__);code=f.read().replace('"'"'\r\n'"'"',
  '"'"'\n'"'"');f.close();exec(compile(code, __file__, '"'"'exec'"'"'))'
  egg_info --egg-base /tmp/pip-pip-egg-info-1xop0k3_            cwd:
  /tmp/pip-install-gzzfb6dp/azure/       Complete output (24 lines):
  Traceback (most recent call last):         File "<string>", line 1, in
  <module>         File "/tmp/pip-install-gzzfb6dp/azure/setup.py", line
  60, in <module>           raise RuntimeError(message)
  RuntimeError:
  Starting with v5.0.0, the 'azure' meta-package is deprecated and
  cannot be installed anymore.       Please install the service specific
  packages prefixed by `azure` needed for your application.
  The complete list of available packages can be found at:
  https://aka.ms/azsdk/python/all
  Here's a non-exhaustive list of common packages:
  -  azure-mgmt-compute (https://pypi.python.org/pypi/azure-mgmt-
  compute) : Management of Virtual Machines, etc.       -  azure-mgmt-
  storage (https://pypi.python.org/pypi/azure-mgmt-storage) : Management
  of storage accounts.       -  azure-mgmt-resource
  (https://pypi.python.org/pypi/azure-mgmt-resource) : Generic package
  about Azure Resource Management (ARM)       -  azure-keyvault-secrets
  (https://pypi.python.org/pypi/azure-keyvault-secrets) : Access to
  secrets in Key Vault       -  azure-storage-blob
  (https://pypi.python.org/pypi/azure-storage-blob) : Access to blobs in
  storage accounts
  A more comprehensive discussion of the rationale for this decision can
  be found in the following issue:       https://github.com/Azure/azure-
  sdk-for-python/issues/10646
  ----------------------------------------   ```
  So it's better to update this suggestion to `azure-mgmt-storage`
  instead.

* Fix bug #1211481 with merge from Raffaele Di Campli. [Kenneth Loafman]

  - Ignores the uid/gid from the archive and keeps the current user's
  one.     - Recommended for restoring data to mounted filesystem which
  do not       support Unix ownership or when root privileges are not
  available.

* Added `--do-not-restore-ownership` option. [Jacotsu]

  Ignores the uid/gid from the archive and keeps the current user's one.
  Recommended for restoring data to mounted filesystem which do not
  support Unix ownership or when root privileges are not available.
  Solves launchpad bug #1211481

* Fix bug #1887689 with patch from Matthew Barry. [Kenneth Loafman]

  - Cleanup with Paramiko backend does not remove files due to missing
  filename byte decoding

* Bump version for LP build. [Kenneth Loafman]

* Fix check for s3 glacier/deep. [Michael Terry]

  This allows encryption validation to continue to work outside of
  those s3 glacier/deep scenarios.

* Change from push to upload. [Kenneth Loafman]

* Add specific version for six. [Kenneth Loafman]


## rel.0.8.14 (2020-07-04)

### Other

* Set deprecation version to 0.9.0 for short filenames. [Kenneth Loafman]

* Fixes for issue #7, par2backend produces badly encoded filenames. [Kenneth Loafman]

* Added a couple of fsdecode calls for issue #7. [Kenneth Loafman]

* Generalize exception for failed get\_version() on LaunchPad. [Kenneth Loafman]

* Ignore *.so files. [Kenneth Loafman]

* Update docs. [Kenneth Loafman]

* Catch up on paperwork. [Kenneth Loafman]

* Fix --rename encoding. [Michael Terry]

* Skip tests failing on py27 under 18.04 (timing error). [Kenneth Loafman]

* Fix code style issue. [Kenneth Loafman]

* Add PATHS\_FROM\_ECLIPSE\_TO\_PYTHON to environ whan starting pydevd. [Kenneth Loafman]

* Add *.pyc to .gitignore. [Kenneth Loafman]

* Replace compilec.py with 'setup.py build\_ext', del compilec.py. [Kenneth Loafman]

* Fix unadorned string. [Kenneth Loafman]

* Fix usage of TOXPYTHON and overrides/bin shebangs. [Kenneth Loafman]

* Use default 'before\_script' for py27. [Kenneth Loafman]

* Don't collect coverage unless needed. [Kenneth Loafman]

* Support PyDrive2 library in the pydrive backend. [Jindrich Makovicka]

  Unlike PyDrive, the PyDrive2 fork is actively maintained.

* Tidy .gitlab-ci.yml, fix py3.5 test, add py2.7 test (allowed to fail) [Aaron Whitehouse]

* Test code instead of py27 since py27 is tested elsewhere. [Kenneth Loafman]

* Fix RdiffdirTest to use TOXPYTHON as well. [Kenneth Loafman]

* Set TOXPYTHON before tests. [Kenneth Loafman]

* Put TOXPYTHON in passed environment. [Kenneth Loafman]

* More fixes for bug #1877885 - Catch quota overflow on Mega upload. [Kenneth Loafman]

* More fixes for bug #1877885 - Catch quota overflow on Mega upload. [Kenneth Loafman]

* Undo: Try forcing python version to match tox testing version. [Kenneth Loafman]

* Always upgrade pip. [Kenneth Loafman]

* Try forcing python version to match tox testing version. [Kenneth Loafman]

* Uncomment all tests. [Kenneth Loafman]

* Test just py27 for now. [Kenneth Loafman]

* Replace bzr with git. [Kenneth Loafman]

* Don't load repo version of future, let pip do it. [Kenneth Loafman]

* Hmmm, Gitlab yaml does not like continuation lines.  Fix it. [Kenneth Loafman]

* Fix typo. [Kenneth Loafman]

* Update to use pip as module and add py35 test. [Kenneth Loafman]

* Add py35 to CI tests. [Kenneth Loafman]

* More changes to support Xenial. [Kenneth Loafman]

* Fix typo. [Kenneth Loafman]

* Fix duplicity to run under Python 3.5. [Kenneth Loafman]

* Fix duplicity to run under Python 3.5. [Kenneth Loafman]

* Update .gitlab-ci.yml to update pip before installing other pip
packages (to try to fix more-itertools issue:
https://github.com/pytest-dev/pytest/issues/4770 ) [Aaron Whitehouse]

* Don't include .git dir when building docker images. [Kenneth Loafman]

* Upgrade pip before installing requirements with it. Fixes more-
itertools error as newer versions of pip identify that the latest
more-itertools are incompatible with python 2. [Aaron Whitehouse]

* Patched in a megav2backend.py to update to MEGAcmd tools. [Kenneth Loafman]

  - Author: Jose L. Domingo Lopez <github@24x7linux.com>     - Man
  pages, docs, etc. were included.

* Change log.Warning to log.Warn.  Whoops! [Kenneth Loafman]

* Fixed bug #1875937 - validate\_encryption\_settings() fails w/S3
glacier. [Kenneth Loafman]

  - Skip validation with a warning if S3 glacier or deep storage
  specified

* Restore commented our backend requirements. [Kenneth Loafman]

* Fixes for rclonebackend from Francesco Magno (original author) [Kenneth Loafman]

  - copy command has been replaced with copyto, that is a specialized
  version for single file operation. Performance-wise, we don't have
  to include a single file in the local side directory, and we don't
  have to list all the files in the remote to check what to
  syncronize.       Additionally, we don't have to mess up with renaming
  because the       copy command didn't support changing filename during
  transfer       (because was oriented to transfer whole directories).
  - delete command has been replaced with deletefile. Same here, we
  have a specialized command for single file operation. Much more
  efficient.     - ls command has been replaced with lsf, that is a
  specialized version       that returns only filenames. Since duplicity
  needs only those, less       bytes to transfer, and less parsing to
  do.     - lastly, I have reintroduced a custom subprocess function
  because the   one       inherithed from base class is checked, and
  throws an exception in   case of       non zero return code. The ls
  command family returns a non zero value   if       the directory does
  not exist in the remote, so starting a new backup       in a non
  existent directory is impossible at the moment because ls   fails
  repeatedly until duplicity gives up. This is a bug in the current
  implementation.       There is the same problem (but less severe) in
  _get method, using   the default       self.subprocess_popen a non
  zero return code will throw an exception   before we       can cleanup
  the partially downloaded file, if any.

* Version man pages during setup.py install. [Kenneth Loafman]

* More fixes for Launchpad build limitations. [Kenneth Loafman]

* More fixes for Launchpad build limitations. [Kenneth Loafman]

* Move setuptools\_scm to setup\_requires. [Kenneth Loafman]

* Back off requirements for fallback\_version in setup.py. [Kenneth Loafman]

* Add some requirements for LP build. [Kenneth Loafman]

* Make sure we get six from pip to support dropbox. [Kenneth Loafman]

* Provide fallback\_version for Launchpad builder. [Kenneth Loafman]

* Remove python3-setuptools-scm from setup.py. [Kenneth Loafman]

* Add python3-setuptools-scm to debian/control. [Kenneth Loafman]

* Try variation with hyphen seperator. [Kenneth Loafman]

* Try python3\_setuptools\_scm (apt repo name).  Probably too old. [Kenneth Loafman]

* Add setuptools\_scm to install\_requires. [Kenneth Loafman]


## rel.0.8.13 (2020-05-05)

### Other

* Fixed release date. [Kenneth Loafman]

* Fixed bug #1876446 - WebDAV backend creates only tiny or 0 Byte files. [Kenneth Loafman]

* Fix to run with --dist-dir command. [Kenneth Loafman]

* Fixed bug #1876778 - byte/str issues in megabackend.py. [Kenneth Loafman]

* Fix to use 'setup.py develop' instead of sdist. [Kenneth Loafman]

* Fix to run with --dist-dir command. [Kenneth Loafman]

* Fixed bug #1875529 - Support hiding instead of deletin on B2. [Kenneth Loafman]

* Uncomment upload and sign. [Kenneth Loafman]

* Reworked versioning to be git tag based. [Kenneth Loafman]

* Migrate bzr to git. [Kenneth Loafman]

* Fixed bug #1872332 - NameError in ssh\_paramiko\_backend.py. [ken]

* Fix spelling error. [ken]

* Fixed bug #1869921 - B2 backup resume fails for TypeError. [ken]

* More changes for pylint. * Resolved conflict between duplicity.config
and testing.manual.config * Normalized emacs mode line to have
encoding:utf8 on all *.py files. [Kenneth Loafman]

* More changes for pylint. * Remove copy.com refs. [Kenneth Loafman]

* More changes for pylint. [Kenneth Loafman]

* More changes for pylint. [Kenneth Loafman]

* Enable additional pylint warnings.  Make 1st pass at correction.   -
unused-argument,     unused-wildcard-import,     redefined-builtin,
bad-indentation,     mixed-indentation. [Kenneth Loafman]

* Fixed bug #1868414 - timeout parameter not passed to   BlobService for
Azure backend. [Kenneth Loafman]


## rel.0.8.12 (2020-03-19)

### Other

* Fixed bug #1867742 - TypeError: fsdecode()   takes 1 positional
argument but 2 were given   with PCA backend. [Kenneth Loafman]

* Fixed bug #1867529 - UnicodeDecodeError: 'ascii'   codec can't decode
byte 0x85 in position 0:   ordinal not in range(128) with PCA. [Kenneth Loafman]

* Fixed bug #1867468 - UnboundLocalError (local   variable 'ch\_err'
referenced before assignment)   in ssh\_paramiko\_backend.py. [Kenneth Loafman]

* Fixed bug #1867444 - UnicodeDecodeError: 'ascii'   codec can't decode
byte 0x85 in position 0:   ordinal not in range(128) using PCA backend. [Kenneth Loafman]

* Fixed bug #1867435 - TypeError: must be str,   not bytes using PCA
backend. [Kenneth Loafman]

* Move pylint config from test\_code to pylintrc. [Kenneth Loafman]

* Cleaned up some setup issues where the man pages   and snapcraft.yaml
were not getting versioned. [Kenneth Loafman]

* Fixed bug #1769267 - [enhancement] please consider   using rclone as
backend. [Kenneth Loafman]

* Fixed bug #1755955 - best order is unclear,   of exclude-if-present
and exclude-device-files   - Removed warning and will now allow these
two to     be in any order.  If encountered outside of the     first
two slots, duplicity will silently move     them to be in the first
two slots.  Within those     two slots the order does not matter. [ken]

* Fixed a couple of file history bugs:   - #1044715 Provide a file
history feature     + removed neutering done between series   -
#1526557 --file-changed does not work     + fixed str/bytes issue
finding filename. [ken]

* Fixed bug #1865648 - module 'multiprocessing.dummy' has   no attribute
'cpu\_count'.   - replaced with module psutil for cpu\_count() only
- appears Arch Linux does not support multiprocessing. [ken]

* Mod to get focal build on LP working. [ken]

* Mod to get focal build on LP working. [ken]

* Mod to get focal build on LP working. [ken]


## rel.0.8.11 (2020-02-24)

### Other

* Fixed to work around par2 0.8.1 core dump on short name   -
https://github.com/Parchive/par2cmdline/issues/145. [ken]

* Fixed bug #1857818 - startswith first arg must be bytes   - use
util.fsdecode on filename. [ken]

* Fixed bug #1863018 - mediafire backend fails on py3   - Fixed handling
of bytes filename in url. [ken]

* Add rclone requirement to snapcraft.yaml. [ken]

* Fixed bug #1236248 - --extra-clean clobbers old backups   - Removed
--extra-clean, code, and docs. [ken]

* Fixed bug #1862672 - test\_log does not respect TMPDIR   - Patch
supplied by Jan Tojnar. [ken]

* Fixed bug #1860405 - Auth mechanism not supported   - Added
python3-boto3 requirement to snapcraft.yaml. [ken]

* More readthedocs munges. [ken]

* Don't format the po files for readthedocs. [ken]

* Add readthedocs.yaml config file, try 3. [ken]

* Add readthedocs.yaml config file, try 2. [ken]

* Add readthedocs.yaml config file. [ken]

* Remove intltool for readthedocs builder. [ken]

* Add python-gettext for readthedocs builder. [ken]

* Add gettext/intltool for readthedocs builder. [ken]

* Add gettext for readthedocs builder. [ken]

* Add intltool for readthedocs builder. [ken]

* Add intltools for readthedocs builder. [ken]

* Add intltools for readthedocs builder. [ken]

* Point readthedocs.io to this repo. [ken]

* Renamed botobackend.py to s3\_boto\_backend.py. [ken]

* Renamed MulitGzipFile to GzipFile to avoid future problems with
upstream author of mgzip fixing the Mulit -> Multi typo. [Byron Hammond]

* Adding missed mgzip import and adjusting untouched unit tests. [Byron Hammond]

* Adding multi-core support by using mgzip instead of gzip. [Byron Hammond]

* Missing comma. [ken]

* Some code cleanup and play with docs. [ken]

* Uncomment snapcraft sign-build.  Seems it's fixed now. [ken]

* Fix argument order on review-tools. [ken]

* Reworked setup.py to build a pip-compatible   distribution tarball of
duplicity. * Added dist/makepip for convenience. [ken]

* Adjust Dockerfiles to new requirements. [ken]

* Fix bug #1861287 - Removing old backup chains   fails using
pexpect+sftp. [ken]

* Adjust Dockerfiles to new requirements. [ken]

* Enhance setup.py/cfg to allow install by pip. [ken]

* Enhance setup.py/cfg to allow install by pip. [ken]

* Enhance setup.py/cfg to allow install by pip. [ken]

* Bump version. [Kenneth Loafman]

* Gave up fighting the fascist version control   munging on
snapcraft.io.  Duplicity now has the   form 0.8.10.1558, where the
last number is the   bzr revno.  Can't do something nice like having
a dev/fin indicator like 0.8.10dev1558 for dev   versions and a fin
for release or final. [Kenneth Loafman]


## rel.0.8.10 (2020-01-23)

### Other

* Fixed bug #1858207 missing targets in multibackend   - Made it
possible to return default value instead     of taking a fatal
exception on an operation by     operation approach.  The only use
case now is for     multibackend to be able to list all targets and
report back on the ones that don't work. [Kenneth Loafman]

* Fixed bug #1858204 - ENODEV should be added to   list of recognized
error stringa. [Kenneth Loafman]

* Comment out test\_compare, again. [Kenneth Loafman]

* Clean up deprecation errors in Python 3.8. [Kenneth Loafman]

* Clean up some TODO tasks in testing code. [kenneth@loafman.com]

* Skip functional/test\_selection::TestUnicode if   python version is
less than 3.7. [kenneth@loafman.com]

* Fixed bug #1859877 - syntax warning on python 3.8. [kenneth@loafman.com]

* Move to single-sourceing the package version   - Rework setup.py,
dist/makedist, dist/makesnap,     etc., to get version from
duplicity/\_\_init\_\_.py   - Drop dist/relfiles.  It was problematic. [kenneth@loafman.com]

* Fixed bug #1859304 with patch from Arduous   - Backup and restore do
not work on SCP backend. [kenneth@loafman.com]

* Revert last change to duplicity.\_\_init\_\_.py. [kenneth@loafman.com]

* Py27 supports unicode returns for translations   - remove install that
does not incude unicode   - Removed some unneeded includes of gettext. [kenneth@loafman.com]

* Fixed bug #1858713 - paramiko socket.timeout   - chan.recv() can
return bytes or str based on     the phase of the moon.  Make
allowances. [kenneth@loafman.com]

* Switched to python3 for snaps. [kenneth@loafman.com]

* Fix unadorned string. [kenneth@loafman.com]


## rel.0.8.09 (2020-01-07)

### Other

* Change of plans.  Skip test if rclone not present. [kenneth@loafman.com]

* Add rclone to setup testing requirements. [kenneth@loafman.com]

* Revert to testing after build. [kenneth@loafman.com]

* Fixed bug #1855736 again - Duplicity fails to start   - remove decode
from unicode string. [kenneth@loafman.com]

* Fixed bug #1858295 - Unicode error in source filename   - decode arg
if it comes in as bytes. [kenneth@loafman.com]

* Add snapcraft login to makesnap. [kenneth@loafman.com]

* Fix bug #1858153 with patch from az   - mega backend: fails to create
directory. [kenneth@loafman.com]

* Fix bug #1857734 - TypeError in ssh\_paramiko\_backend   - conn.recv()
can return bytes or string, make string. [kenneth@loafman.com]

* Fix bytes/string differences in subprocess\_popen()   - Now returns
unicode string not bytes, like python2. [kenneth@loafman.com]

* Convert all shebangs to python3 for bug #1855736. [kenneth@loafman.com]

* Fixed bug #1857554 name 'file' is not defined   - file() calls
replaced by open() in 3 places. [kenneth@loafman.com]

* Original rclonebackend.py from Francesco Magno for Python 2.7. [kenneth@loafman.com]

* Fix manpage indention clarify difference between boto backends add
boto+s3:// for future use when boto3+s3:// will become default s3
backend. [ed.so]

* Renamed testing/infrastructure to testing/docker. [kenneth@loafman.com]

* Fixed a mess I made.  setup.py was shebanged to   Py3, duplicity was
shebanged to Py2.  This meant   that duplicity ran as Py2 but could
not find its   modules because they were under Py3.  AArgh! [kenneth@loafman.com]

* Fixed bug #1855736 - duplicity fails to start   - Made imports
absolute in dup\_main.py. [kenneth@loafman.com]

* Fixed bug #1856447 with hint from Enno L   - Replaced with formatted
string. [kenneth@loafman.com]

* Fixed bug #1855736 with help from Michael Terry   - Decode Popen
output to utf8. [kenneth@loafman.com]

* Fixed bug #1855636 with patch from Filip Slunecko   - Wrong buf type
returned on error.  Make bytes. [kenneth@loafman.com]


## rel.0.8.08 (2019-12-08)

### Other

* Merged in translation updates. [kenneth@loafman.com]

* Removed abandoned ref in README * Comment out signing in makesnap. [kenneth@loafman.com]

* Fixed bug #1854554 with help from Tommy Nguyen   - Fixed a typo made
during Python 3 conversion. [kenneth@loafman.com]

* Fixed bug #1855379 with patch from Daniel González Gasull   - Issue
warning on temporary connection loss. * Fixed misc coding style
errors. [kenneth@loafman.com]

* Disabling autotest for LP build.  I have run tests on all Ubuntu
releases since 18.04, so the code works.  To run tests manually, run
tox from the main directory.  Maybe LP build will work again soon. [kenneth@loafman.com]

* Update to manpage. [Carl A. Adams]

* BUGFIX: list should retun byte strings, not unicode strings. [Carl A. Adams]

* Updating comments. [Carl A. Adams]

* Select boto3/s3 backend via url scheme rather than by CLI option.  Doc
changes to support this. [Carl A. Adams]

* Renaming boto3 backend file. [Carl A. Adams]

* Adding support for AWS Glacier Deep Archive.  Fixing some typos. [Carl A. Adams]

* Manpage updates.  Cleaning up the comments to reflect my current
plans. Some minor clean-ups. [Carl A. Adams]

* Updating comments. [Carl A. Adams]

* SSE options comitted. AES tested, KMS not tested. [Carl A. Adams]

* Handling storage class on backup. [Carl A. Adams]

* Handling storage class on backup. [Carl A. Adams]

* Minor clean-ups. [Carl A. Adams]

* Rename boto3 backend py file. [Carl A. Adams]

* Removing 'todo' comment for multi support.  Defaults in Boto3 chunk
the upload and attempt to use multiple threads.  See https://boto3.ama
zonaws.com/v1/documentation/api/latest/reference/customizations/s3.htm
l#boto3.s3.transfer.TransferConfig. [Carl A. Adams]

* Format fix. [Carl A. Adams]

* Fixing status reporting.  Cleanup. [Carl A. Adams]

* Better exception handling. Return -1 for unknwon objects in \_query. [Carl A. Adams]

* Updating comment. [Carl A. Adams]

* Making note of a bug. [Carl A. Adams]

* Removing unused imports. [Carl A. Adams]

* Implementing \_query for boto3. [Carl A. Adams]

* Minor clean-up. [Carl A. Adams]

* Some initial work on a boto3 back end. [Carl A. Adams]

* Convert debian build to Python 3. [kenneth@loafman.com]

* Replace python with python3 in shebang. [kenneth@loafman.com]

* Convert debian build to Python 3. [kenneth@loafman.com]

* Fixed bug #1853809 - Tests failing with Python 3.8 / Deprecation
warnings   - Fixed the deprecation warnings with patch from Sebastien
Bacher   - Fixed test\_globmatch to handle python 3.8 same as 3.7   -
Fixed tox.ini to include python 3.8 in future tests. [kenneth@loafman.com]

* Fixed bug #1853655 - duplicity crashes with --exclude-older-than   -
The exclusion setup checked for valid string only.  Made     the code
comprehend datetime (int) as well. [kenneth@loafman.com]

* Just some cosmetic changes. [kenneth@loafman.com]

* Fixed bug #1851668 with help from Wolfgang Rohdewald   - Applied
patches to handle translations. [kenneth@loafman.com]

* Fixed bug #1852876 '\_io.BufferedReader' object has no attribute
'uc\_name'   - Fixed a couple of instances where str() was used in
place of util.uexc()   - The file was opened with builtins, so use
name, not uc\_name. [kenneth@loafman.com]

* Added build signing to dist/makesnap. [kenneth@loafman.com]

* Fixed bug #1852848 with patch from Tomas Krizek   - B2 moved the API
from "b2" package into a separate "b2sdk" package.     Using the old
"b2" package is now deprecated. See link:     https://github.com/Backb
laze/B2\_Command\_Line\_Tool/blob/master/b2/\_sdk\_deprecation.py   -
b2backend.py currently depends on both "b2" and "b2sdk", but use of
"b2"     is enforced and "b2sdk" isn't used at all.   - The attached
patch uses "b2sdk" as the primary dependency. If the new     "b2sdk"
module isn't available, it falls back to using the old "b2" in
order to keep backward compatibility with older installations. [kenneth@loafman.com]


## rel.0.8.07 (2019-11-14)

### Other

* Fixed bug #1851727 - InvalidBackendURL for multi backend   - Encode to
utf8 only on Python2, otherwise leave as unicode. [kenneth@loafman.com]

* Fix resuming without a passphrase when using just an encryption key. [Michael Terry]

* Fix bytes/string issue in pydrive backend upload. [Michael Terry]

* Fixed bug #1851167 with help from Aspen Barnes   - Had Popen() to
return strings not bytes. [kenneth@loafman.com]

* Added dist/makesnap to make spaps automagically. [kenneth@loafman.com]

* Fixed bug #1850990 with suggestion from Jon Wilson   - --s3-use-
glacier and --no-encryption cause slow backups. [kenneth@loafman.com]

* Fix header in CHANGELOG. [kenneth@loafman.com]

* Added b2sdk to snapcraft.yaml * Fixed bug #1850440 - Can't mix strings
and bytes. [kenneth@loafman.com]


## rel.0.8.06 (2019-11-05)

### Other

* Updated snapcraft.yaml to remove python-lockfile and fix spelling. [kenneth@loafman.com]

* Updated snapcraft.yaml to remove rdiffdir and add libaft1 to stage. [kenneth@loafman.com]

* Updated snapcraft.yaml to include rdiffdir and did some reformatting. [kenneth@loafman.com]

* Updated snapcraft.yaml to include rdiffdir and did some reformatting. [kenneth@loafman.com]

* Removed file() call in swiftbackend.  It's been deprecated since py2. [kenneth@loafman.com]

* Revisited bug #1848783 - par2+webdav raises TypeError on Python 3   -
Fixed so bytes filenames were compared as unicode in re.match() [kenneth@loafman.com]

* Removed a couple of disables from pylint code test.   - E1103 - Maybe
has no member   - E0712 - Catching an exception which doesn't inherit
from BaseException. [kenneth@loafman.com]

* Added additional fsdecode's to uses of local\_path.name and
source\_path.name in b2backend's \_get() and \_put.  See bug
#1847885 for more details. [kenneth@loafman.com]

* Fixed bug #1849661 with patch from Graham Cobb   - The problem is that
b2backend uses 'quote\_plus' on the     destination URL without
specifying the 'safe' argument as     '/'. Note that 'quote' defaults
'safe' to '/', but     'quote\_plus' does not! [kenneth@loafman.com]

* Fixed bug #1848166 - Swift backend fails on string concat   - added
util.fsdecode() where needed. [kenneth@loafman.com]

* Fixed bug #1848783 with patch from Jacob Middag   - Don't use b''
strings in re.* [kenneth@loafman.com]

* Fixed bug #1848783 with patch from Jacob Middag   - Don't use b''
strings in re.* [kenneth@loafman.com]

* Fixed bug #1626061 with patch from Michael Apozyan   - While doing
multipart upload to s3 we need to report the     total size of
uploaded data, and not the size of each part     individually.  So we
need to keep track of all parts     uploaded so far and sum it up on
the fly. [kenneth@loafman.com]

* Removed revision 1480 until patch is validated. [kenneth@loafman.com]

* Fixed bug #1626061 with patch from Michael Apozyan   - While doing
multipart upload to s3 we need to report the     total size of
uploaded data, and not the size of each part     individually.  So we
need to keep track of all parts     uploaded so far and sum it up on
the fly. [kenneth@loafman.com]

* Fixed bug #1848203 with patch from Michael Apozyan   - convert to
integer division. [kenneth@loafman.com]

* Fix unadorned string. [kenneth@loafman.com]

* Fix unadorned string. [kenneth@loafman.com]

* Update changelogs. [Adam Jacobs]

* In version 1 of the B2sdk, the list\_file\_names method is removed
from the B2Bucket class. [Adam Jacobs]

  This change makes the b2 backend backwards-compatible with the old
  version 0 AND forward-compatible with the new version 1.

* Complete fix for string concatenation in b2 backend. [Adam Jacobs]

* Fixed Resouce warnings when using paramiko.  It turns out   that
duplicity's ssh\_paramiko\_backend.py was not handling   warning
suppression and ended up clearing all warnings,   including those that
default to off. [kenneth@loafman.com]

* Fixed Resouce warnings when using paramiko.  It turns out   that
duplicity's ssh\_paramiko\_backend.py was not handling   warning
suppression and ended up clearing all warnings,   including those that
default to off. [kenneth@loafman.com]


## rel.0.8.05 (2019-10-07)

### Other

* Removed a setting in tox.ini that causes coverage to   be activated
during testing duplicity. [kenneth@loafman.com]

* Fixed bug #1846678 - --exclude-device-files and -other-filesystems
crashes   - assuming all options had arguments was fixed. [kenneth@loafman.com]

* Fixed bug #1844950 - ssh-pexpect backend syntax error   - put the
global before the import. [kenneth@loafman.com]

* Fixed bug #1846167 - webdavbackend.py: expected bytes-like object, not
str   - base64 now returns bytes where it used to be strings, so just
decode(). [kenneth@loafman.com]

* Fixed bug reported on maillist - Python error in Webdav backend.  See:
https://lists.nongnu.org/archive/html/duplicity-
talk/2019-09/msg00026.html. [kenneth@loafman.com]

* Fix bug #1844750 - RsyncBackend fails if used with multi-backend.   -
used patch provided by KDM to fix. [kenneth@loafman.com]

* Fix bug #1843995 - B2 fails on string concatenation.   - use
util.fsdecode() to get a string not bytes. [kenneth@loafman.com]

* Clean up some pylint warnings. [kenneth@loafman.com]

* Add testenv:coverage and took it out of defaults.  Some cleanup. [kenneth@loafman.com]

* Fix MacOS tempfile selection to avoid /tmp and /var/tmp.  See thread:
https://lists.nongnu.org/archive/html/duplicity-
talk/2019-09/msg00000.html. [kenneth@loafman.com]

* Sort of fix bugs #1836887 and #1836888 by skipping the   tests under
question when running on ppc64el machines. [kenneth@loafman.com]

* Added more python future includes to support using   python3 code
mixed with python2. [kenneth@loafman.com]

* Fix exc.args handling.  Sometimes it's (message, int),   other times
its (int, message).  We look for the   message and use that for the
exception report. [kenneth@loafman.com]

* Adjust exclusion list for rsync into duplicity\_test. [kenneth@loafman.com]

* Set to allow pydevd usage during tox testing. [kenneth@loafman.com]

* Don't add extra newline when building dist/relfiles.txt. [kenneth@loafman.com]

* Changed dist/makedist to fall back to dist/relfiles.txt   in case bzr
or git is not available to get files list.   Tox sdist needs setup.py
which needs dist/makedist. * Updatated LINGUAS file to add four new
translations. [kenneth@loafman.com]


## rel.0.8.04 (2019-08-31)

### Other

* Made some changes to the Docker infrastructure:   - All scripts run
from any directory, assuming directory     structure remains the same.
- Changed from Docker's COPY internal command which is slow to
using external rsync which is faster and allows excludes.   - Removed
a couple of unused files. [kenneth@loafman.com]

* Run compilec.py for code tests, it needs the import. [kenneth@loafman.com]

* Simplify README-TESTING and change this to recommend using the Docker
images to test local branches in a known-good environment. [Aaron A Whitehouse]

* Convert Dockerfile-19.10 to new approach (using local folder instead
of remote repo) * run-tests passes on 19.10 Docker (clean: commands
succeeded; py27: commands succeeded; SKIPPED: py36:
InterpreterNotFound: python3.6; py37: commands succeeded; report:
commands succeeded) [Aaron A Whitehouse]

* Convert Dockerfile-19.04 to new approach (using local folder instead
of remote repo) * run-tests passes on 19.04 Docker (clean: commands
succeeded; py27: commands succeeded; SKIPPED:  py36:
InterpreterNotFound: python3.6;  py37: commands succeeded; report:
commands succeeded) [Aaron A Whitehouse]

* Edit Dockerfile-18.10 to use the local folder. * Tests all pass on
18.10 except for the same failures as trunk (4 failures on python 3.6:
TestUnicode.test\_unicode\_filelist;
TestUnicode.test\_unicode\_paths\_asterisks;
TestUnicode.test\_unicode\_paths\_non\_globbing;
TestUnicode.test\_unicode\_paths\_square\_brackets) [Aaron A Whitehouse]

* Use local folder instead of bzr revision, so remove the revision
arguments in the setup script. * Modify Dockerfile and
Dockerfile-18.04 to copy the local folder rather than the remote
repository. * Tests all pass on 18.04 except for the same failures as
trunk (4 failures on python 3.6: TestUnicode.test\_unicode\_filelist;
TestUnicode.test\_unicode\_paths\_asterisks;
TestUnicode.test\_unicode\_paths\_non\_globbing;
TestUnicode.test\_unicode\_paths\_square\_brackets) [Aaron A Whitehouse]

* Fix .bzrignore. [kenneth@loafman.com]

* Encode Azure backend file names. [Frank Fischer]

* Change README-TESTING to be correct for running individual tests now
that we have moved to Pytest. [Aaron A Whitehouse]

* Fix debian/rules file. [kenneth@loafman.com]

* Fix setup.py shebang. [kenneth@loafman.com]

* Fix debian/rules file. [kenneth@loafman.com]

* Fix debian/rules file. [kenneth@loafman.com]

* Fix debian/rules file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Ran futurize selectively filter-by-filter to find the ones that work. [kenneth@loafman.com]

* Fixed build on Launchpad for 0.8.x, so now there is a new PPA at
https://launchpad.net/\~duplicity-team/+archive/ubuntu/daily-dev-trunk. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Fix debian/control file. [kenneth@loafman.com]

* Add snap package creation files * Modify dist/makedist to version the
snapcraft.yaml. [Aaron A Whitehouse]

* Remove a mess I made. [Kenneth Loafman]

* Fixed bug #1839886 with hint from denick   - Duplicity crashes when
using --file-prefix * Removed socket.settimeout from backend.py.   It
was already set in commandline.py. * Removed pycryptopp from README
requirements. [kenneth@loafman.com]

* Fixed bug #1839728 with info from Avleen Vig   - b2 backend requires
additional import. [kenneth@loafman.com]

* Convert the docker duplicity\_test image to pull the local branch into
the container, rather than lp:duplicity. This allows the use of the
duplicity Docker testing containers to test local changes in a known-
good environment before they are merged into trunk. The equivalent of
the old behaviour can be achieved by starting with a clean branch from
lp:duplicity. * Expand Docker context to parent branch folder and use
-f in the docker build command to point to the Dockerfile. * Simplify
build-duplicity\_test.sh now that the whole folder is copied
(individual files no longer need to be copied) [Aaron A Whitehouse]


## rel.0.8.03 (2019-08-09)

### Other

* More changes to provide Python test coverage:   - Moved bulk of code
from bin/duplicity to     duplicity/dup\_main.py for coverage. * Fixed
some 2to3 issues in dup\_main.py * Fixed division differences with
futurize. [kenneth@loafman.com]

* More changes to provide Python test coverage:   - Moved bulk of code
from bin/duplicity to     duplicity/dup\_main.py for coverage. * Fixed
some 2to3 issues in dup\_main.py * Fixed division differences with
futurize. [kenneth@loafman.com]

* More changes to provide Python test coverage:   - Moved bulk of code
from bin/duplicity to     duplicity/dup\_main.py for coverage. * Fixed
some 2to3 issues in dup\_main.py. [kenneth@loafman.com]

* More changes to provide Python test coverage:   - Now covers
functional tests spawning duplicity   - Does not cover bin/duplicity
for some reason. [kenneth@loafman.com]

* Fixed bugs #1838427 and #1838702 with a fix   suggested by Stephen
Miller.  The fix was to   supply tarfile with a unicode grpid, not
bytes. [kenneth@loafman.com]

* Some changes to provide Python test coverage:   - Coverage runs with
every test cycle   - Does not cover functional tests that spawn
duplicity itself.  Next pass.   - After a run use 'coverage report
html' to see     an overview list and links to drill down.  It
shows up in htmlcov/index.html. [kenneth@loafman.com]


## rel.0.8.02 (2019-07-31)

### Other

* Fix dist/makedist to run on python2/3. [kenneth@loafman.com]

* Fix dist/makedist to run on python3. [kenneth@loafman.com]

* Fix dist/makedist to run on python3. [kenneth@loafman.com]

* One last change for bug #1829416 from charlie4096. [kenneth@loafman.com]

* Enhanced build\_duplicity\_test.sh   - Use -h to get help and defaults
- Takes arguments for distro, revno, help   - Distros supported are
18.04, 18.10, 19.04, 19.10   - Revnos are passed to bzr -r option. [kenneth@loafman.com]

* Fix so Docker image duplicity\_test will update and pull   new bzr
revisions if changed since last build. [kenneth@loafman.com]

* Remove speedup in testing backup.  The math was correct,   but it's
failing on Docker and Launchpad testing. [kenneth@loafman.com]

* Move pytest-runner setup requirement to a test requirement. [Michael Terry]

* Removed python-gettext from setup.py.  Whoops! [kenneth@loafman.com]

* Optimize loading backup chains; reduce file\_naming.parse calls. [Matthew Glazar]

  For each filename in filename_list,
  CollectionsStatus.get_backup_chains calls file_naming.parse   (through
  BackupSet.add_filename) between 0 and len(sets)*2   times. In the
  worst case, this leads to a *ton* of redundant   calls to
  file_naming.parse.
  For example, when running 'duplicity collection-status' on   one of my
  backup directories:
  * filename_list contains 7545 files   * get_backup_chains creates 2515
  BackupSet-s   * get_backup_chains calls file_naming.parse 12650450
  times!
  This command took 9 minutes and 32 seconds. Similar   commands, like
  no-op incremental backups, also take a long   time. (The directory
  being backed up contains only 9 MiB   across 30 files.)
  Avoid many redundant calls to file_naming.parse by hoisting   the call
  outside the loop over BackupSet-s. This   optimization makes
  'duplicity collection-status' *20 times   faster* for me (572 seconds
  -> 29 seconds).
  Aside from improving performance, this commit should not   change
  behavior.

* Correct types for os.join in Dropbox backend. [Gwyn Ciesla]

* Fixed bug #1836829 progress.py: old\_div not defined   - also fixed
old\_div in \_boto\_multi.py. [kenneth@loafman.com]

* Fixed bug #1836829 progress.py: old\_div not defined   - also fixed
old\_div in \_boto\_multi.py. [kenneth@loafman.com]

* Remove python-gettext from requirements.txt.  Normal   Python
installation includes gettext. * Mod README to include Python 3.6 and
3.7. [kenneth@loafman.com]


## rel.0.8.01 (2019-07-14)

### Other

* Comment out HSIBackendTest since shim is not up-to-date. [kenneth@loafman.com]

* Install python3.6 and 3.7 explicitly in Dockerfile.  Tox and Docker
now support testing Python 2,7, 3.6, and 3.7. [kenneth@loafman.com]

* Make sure test filenames are bytes not unicode. * Fix
test\_glob\_to\_regex to work on Python 3.7. [kenneth@loafman.com]

* Going back to original.  No portable way to ignore warning. [kenneth@loafman.com]

* Another unadorned string. [kenneth@loafman.com]

* Cleanup some trailing spaces/lines in Docker files. [kenneth@loafman.com]

* Fix so we start duplicity with the base python we run under. [kenneth@loafman.com]

* Adjust POTFILES.in for compilec.py move. [kenneth@loafman.com]

* Ensure \_librsync.so is regenned before toc testing. [kenneth@loafman.com]

* Add encoding to logging.FileHandler call to make log file utf8. [kenneth@loafman.com]

* Fix warning in \_librsync.c module. [kenneth@loafman.com]

* Fix some issues found by test\_code.py (try 2) [kenneth@loafman.com]

* Fix some issues found by test\_code.py. [kenneth@loafman.com]

* Fix reversed port assignments (FTP & SSH) in docker-compose.yml. [kenneth@loafman.com]

* Fix reimport problem where "from future.builtins" was being treated
the differently than "from builtins".  They are both the same, so
converted to shorter form "from builtins" and removed duplicates. [kenneth@loafman.com]

* Fix s3 backups by encoding remote filenames. [Michael Terry]

* Add 2to3 as a dependency to dockerfile. [Aaron A. Whitehouse]

* Add tzdata back in as a dependency and set
DEBIAN\_FRONTEND=noninteractive so no tzdata prompt. [Aaron A. Whitehouse]

* Set docker container locale to prevent UTF-8 errors. [Aaron A. Whitehouse]

* Change dockerfile to use 18.04 instead of 16.04 and other fixes. [Aaron A. Whitehouse]

* Fix s3 backups by importing the boto module. [Michael Terry]

* Normalize shebang to just python, no version number * Fix so most
testing/*.py files have the future suggested lines   - from
\_\_future\_\_ import print\_function     from future import
standard\_library     standard\_library.install\_aliases() [kenneth@loafman.com]

* Fixed failing test in testing/unit/test\_globmatch.py   - Someone is
messing with regex.  Fix same.   - See
https://bugs.python.org/issue29995 for details. [kenneth@loafman.com]

* Fixed bug #1833559 0.8 test fails with 'duplicity not found' errors
- Fixed assumption that duplicity/rdiffdir were in $PATH. [kenneth@loafman.com]

* Fixed bug #1833573 0.8.00 does not work on Python 2   - Fixed shebang
to use /usr/bin/python instead of python2. [kenneth@loafman.com]

* Fix some test\_code errors that slipped by. [kenneth@loafman.com]

* Fix Azure backend for python 3. [Frank Fischer]

  By definition, the list of keys from "list" is byte-formatted.   As
  such we have to decode the parameter offered to "get"

* Fixed bug #1831178 sequence item 0: expected str instance, int found
- Simply converted int to str when making list. [kenneth@loafman.com]

* Fix some import conflicts with the "past" module   - Rename
collections.py to dup\_collections.py   - Remove all "from
future.utils import old\_div"   - Replace old\_div() with "//" (in
py27 for a while).   - All tests run for py3, unit tests run for py3.
The new     import fail is "from future import standard\_library" [kenneth@loafman.com]

* Spaces to tabs for makefile. [Kenneth Loafman]

* Change to python3 for build. [kenneth@loafman.com]

* Have uexc to always return a string. [Michael Terry]

  This fixes unhandled exception reporting

* Add requirements for python-gettext. [kenneth@loafman.com]

* Fix gio and pydrive backends to use fsdecode. [Michael Terry]

* Remove unnecessary sleeping after running backups in tests. [Matthew Glazar]

  ptyprocess' 'PtyProcess.close' function [1] closes the   terminal,
  then terminates the process if it's still alive.   Before checking if
  the process is alive, ptyprocess   unconditionally sleeps for 100
  milliseconds [2][3].
  In 'run_duplicity', after we call 'child.wait()', we know   that the
  process is no longer alive. ptyprocess' 100 ms   sleep just slows down
  tests. Tell ptyprocess to not sleep.
  [1] pexpect uses ptyprocess. 'PtyProcess.close' is called by
  'PtyProcess.__del__', so 'PtyProcess.close' is called       when
  'run_duplicity' returns.   [1] https://github.com/pexpect/ptyprocess/b
  lob/3931cd45db50ee8533b8b0fef424b8d75f7ba1c2/ptyprocess/ptyprocess.py#
  L403   [2] https://github.com/pexpect/ptyprocess/blob/3931cd45db50ee85
  33b8b0fef424b8d75f7ba1c2/ptyprocess/ptyprocess.py#L173

* Minimize time spent sleeping between backups. [Matthew Glazar]

  During testing, if a backup completes at time 10:49:30.621,   the next
  call to 'backup' sleeps to ensure the new backup   has a different
  integer time stamp (10:49:31). Currently,   'backup' sleeps for an
  entire second, even though the next   integer time stamp is less than
  half a second away (0.379   seconds). This extra sleeping causes tests
  to take longer   than they need to.
  Make tests run faster by sleeping only enough to reach the   next
  integer time stamp.

* Ensure all duplicity output is captured in tests. [Matthew Glazar]

  The loop in 'run_duplicity' which captures output has a race
  condition. If duplicity writes output then exits before
  'child.isalive()' is called, then 'run_duplicity' exits the   loop
  before calling 'child.readline()'. This means that some   output is
  not read into the 'lines' list.
  Fix this race condition by reading all output until EOF,   then
  waiting for the child to exit.

* Fix TestGlobToRegex.test\_glob\_to\_regex for py3.6 and above   - see
https://bugs.python.org/issue29995 for details. [kenneth@loafman.com]

* Some more work on unadorned strings   - Fixed
test\_unadorned\_string\_literals to list all strings found   - Added
bin/duplicity and bin/rdiffdir to list of files tested   - All
unadorned strings have now been adorned. [kenneth@loafman.com]

* Fixed bug #1828662 with patch from Bas Hulsken   - string.split() had
been deprecated in 2, removed in 3.7. [kenneth@loafman.com]

* Setup.py: allow python 2.7 again. [Mike Gorse]

* Bug #1828869: update CollectionsStatus after sync. [Mike Gorse]

* Imap: python 3 fixes. [Mike Gorse]

* Sync: handle parsed filenames without start/end times. [Mike Gorse]

  Signatures set time, rather than start_time and end_time, so
  comparisons   against the latter generate an exception on Python 3.

* More PEP 479 fixes. [Mike Gorse]

* Fix some unadorned strings. [kenneth@loafman.com]

* Fix some unadorned strings. [kenneth@loafman.com]

* Fix to allow >=2.7 or >=3.5. [kenneth@loafman.com]

* Fix to always compile \_librsync before testing. [kenneth@loafman.com]

* Manual merge of lp:\~yajo/duplicity/duplicity   - Support partial
metadata sync.   - Fixes bug #1823858 by letting the user to choose
partial syncing. Only the metadata for the target chain     will be
downloaded. If older (or newer) chains are encrypted with a different
passphrase, the user will     be able to restore to a given time by
supplying only the passphrase for the chain selected by     the
`--restore-time` option when using this new option.   - A side effect
is that using this flag reduces dramatically the sync time when moving
files from one to     another location, in cases where big amounts of
chains are found. [kenneth@loafman.com]

* Change to Python >= 3.5. [kenneth@loafman.com]

* Added documentation on how to use the new AWS S3 Glacier option. [Brandon Anderson]

* Fixed a typo in prior commit. [Brandon Anderson]

* Added support for AWS glacier storage class. [Brandon Anderson]

* Fix bug #1811114 with revised onedrivebackend.py from David Martin   -
Adapt to new Microsoft Graph API. [kenneth@loafman.com]

* Removed last mention of copy.com from man page with help from edso. [kenneth@loafman.com]

* Fix pylint style issues (over-indented text, whitespace on blank lines
etc) * Removed "pylint: disable=bad-string-format-type" comment, which
was throwing an error and does not seem to be needed. [Aaron A Whitehouse]

* Accomodate unicode input for uexc and add test for this. [Aaron A Whitehouse]

* Convert deprecated .message to args[0] [Aaron A Whitehouse]

* Add test case for lp:1770929 * Added fix (though using deprecated
.message syntax) [Aaron A Whitehouse]

* Attempt to port sx backend to python 3. [Mike Gorse]

  Untested, but likely needed changes similar to some other backends.

* Rsync: py3 fixes. [Mike Gorse]

* Ncftp: py3 fixes. [Mike Gorse]

* Test\_selection.py: fix an invalid escape sequence on py3. [Mike Gorse]

* Fix sync\_archive on python 3. [Mike Gorse]

  The recognized suffixes were being stored as unicode, but they were
  being   compared against filenames that are stored as bytes, so the
  comparisons   were failing.

* Ssh\_pexpect: py3 fixes. [Mike Gorse]

* Fixed bug #1817375 with hint from mgorse   - Added 'global pexpect' at
end of imports. [kenneth@loafman.com]


