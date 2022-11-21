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

u"""Parse command line, check for consistency, and set config"""

import argparse
import io
import os
import re
import sys
from hashlib import md5
from pathvalidate import sanitize_filepath
from pathvalidate import is_valid_filepath

import errors
from duplicity import commandline
from duplicity import config
from duplicity import dup_time
from duplicity import errors
from duplicity import log
from duplicity import path

select_opts = []  # Will hold all the selection options
select_files = []  # Will hold file objects when filelist given

# commands and type of positional args expected
commands = {
    u"cleanup": [u"target_url"],
    u"collection-status": [u"target_url"],
    u"full": [u"source_dir", u"target_url"],
    u"incremental": [u"source_dir", u"target_url"],
    u"list-current-files": [u"target_url"],
    u"remove-older-than": [u"remove_time", u"target_url"],
    u"remove-all-but-n-full": [u"count", u"target_url"],
    u"remove-all-inc-of-but-n-full": [u"count", u"target_url"],
    u"restore": [u"source_url", u"target_dir"],
    u"verify": [u"source_url", u"target_dir"],
}

class CommandLineError(errors.UserError):
    pass


class AddSelectionAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(AddSelectionAction, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        print('%r %r %r' % (namespace, values, option_string))
        addarg = os.fsdecode(value) if isinstance(values, bytes) else values
        select_opts.append((os.fsdecode(option_string), addarg))


class AddFilistAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(AddFilistAction, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        print('%r %r %r' % (namespace, values, option_string))
        select_opts.append((os.fsdecode(s), os.fsdecode(filename)))
        try:
            select_files.append(io.open(filename, u"rt", encoding=u"UTF-8"))
        except Exception as e:
            raise argparse.ArgumentError(str(e))


class AddRenameAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(AddRenameAction, self).__init__(option_strings, dest, **kwargs)
    def __call__(self, parser, namespace, values, option_string=None):
        print('%r %r %r' % (namespace, values, option_string))
        key = os.fsencode(os.path.normcase(os.path.normpath(values[0])))
        config.rename[key] = os.fsencode(values[1])


def check_count(val):
    return int(val)


def check_remove_time(val):
     return dup_time.genstrtotime(val)


def check_source_dir(val):
    if u"://" in val:
        command_line_error(f"Source should be directory, not url.  Got '{val}' instead.")
    if is_valid_filepath(val):
        val = sanitize_filepath(val)
        val = expand_fn(val)
    else:
        command_line_error(f"Source '{val}' is not a valid file path.")
    if not os.path.isdir(val):
        command_line_error(f"Argument source_dir '{val}' does not exist or is not a directory.")
    return val


def check_source_url(val):
    if u"://" not in val:
        command_line_error(f"Source should be url, not directory.  Got '{val}' instead.")
    return val


def check_target_dir(val):
    if u"://" in val:
        command_line_error(f"Target should be directory, not url.  Got '{val}' instead.")
    if is_valid_filepath(val):
        val = sanitize_filepath(val)
        val = expand_fn(val)
    else:
        command_line_error(f"Target '{val}' is not a valid file path.")
    if not os.path.isdir(val):
        command_line_error(f"Argument target_dir '{val}' does not exist or or is not a directory.")
    return val


def check_target_url(val):
    if u"://" not in val:
        command_line_error(f"Source should be url, not directory.  Got '{val}' instead.")
    return val


def expand_fn(filename):
    return os.path.expanduser(os.path.expandvars(filename))


def expand_archive_dir(archdir, backname):
    u"""
    Return expanded version of archdir joined with backname.
    """
    assert config.backup_name is not False, \
        u"expand_archive_dir() called prior to config.backup_name being set"

    return expand_fn(os.path.join(archdir, os.fsencode(backname)))


def generate_default_backup_name(backend_url):
    u"""
    @param backend_url: URL to backend.
    @returns A default backup name (string).
    """
    # For default, we hash args to obtain a reasonably safe default.
    # We could be smarter and resolve things like relative paths, but
    # this should actually be a pretty good compromise. Normally only
    # the destination will matter since you typically only restart
    # backups of the same thing to a given destination. The inclusion
    # of the source however, does protect against most changes of
    # source directory (for whatever reason, such as
    # /path/to/different/snapshot). If the user happens to have a case
    # where relative paths are used yet the relative path is the same
    # (but duplicity is run from a different directory or similar),
    # then it is simply up to the user to set --archive-dir properly.
    burlhash = md5()
    burlhash.update(backend_url.encode())
    return burlhash.hexdigest()


def check_file(value):
    return os.fsencode(expand_fn(value))


def check_time(value):
    try:
        return dup_time.genstrtotime(value)
    except dup_time.TimeException as e:
        raise argparse.ArgumentError(str(e))


def check_verbosity(value):
    # TODO: normalize logging to Python standards
    fail = False

    value = value.lower()
    if value in [u'e', u'error']:
        verb = log.ERROR
    elif value in [u'w', u'warning']:
        verb = log.WARNING
    elif value in [u'n', u'notice']:
        verb = log.NOTICE
    elif value in [u'i', u'info']:
        verb = log.INFO
    elif value in [u'd', u'debug']:
        verb = log.DEBUG
    else:
        try:
            verb = int(value)
            if verb < 0 or verb > 9:
                fail = True
        except ValueError:
            fail = True

    if fail:
        # TRANSL: In this portion of the usage instructions, "[ewnid]" indicates which
        # characters are permitted (e, w, n, i, or d); the brackets imply their own
        # meaning in regex; i.e., only one of the characters is allowed in an instance.
        raise argparse.ArgumentError(
            u"Verbosity must be one of: digit [0-9], character [ewnid], "
            u"or word ['error', 'warning', 'notice', 'info', 'debug']. "
            u"The default is 4 (Notice).  It is strongly recommended "
            u"that verbosity level is set at 2 (Warning) or higher.")

    return verb


def set_log_fd(fd):
    if fd < 1:
        raise argparse.ArgumentError(u"log-fd must be greater than zero.")
    log.add_fd(fd)
    return fd


def set_log_file(fn):
    fn = check_file(fn)
    log.add_file(fn)
    return fn


def set_volsize(v):
    setattr(config, u"volsize", v * 1024 * 1024)
    # if mp_size was not explicity given, default it to volsize
    if not getattr(config, u'mp_set', False):
        setattr(config, u"mp_segment_size", int(config.mp_factor * p.values.volsize))


def set_mpsize(v):
    setattr(config, u"mp_segment_size", v * 1024 * 1024)
    setattr(config, u"mp_set", True)


def set_megs(num):
    return int(num) * 1024 * 1024


def print_ver(value):
    print(u"duplicity %s" % config.version)
    sys.exit(0)


def parse_cmdline_options(arglist):
    u"""Parse argument list"""

    parser = argparse.ArgumentParser(
        prog=u'duplicity',
        usage=usage(),
        argument_default=False,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Add commands and their args to the parser.
    # We grab the command and all the args with '*'.
    parser.add_argument(u'positional', type=str, nargs=u"*")

    # allow different sources to same target url, not recommended
    parser.add_argument(u"--allow-source-mismatch", action=u"store_true")

    # Set to the path of the archive directory (the directory which
    # contains the signatures and manifests of the relevent backup
    # collection), and for checkpoint state between volumes.
    # TRANSL: Used in usage help to represent a Unix-style path name. Example:
    # --archive-dir <path>
    parser.add_argument(u"--archive-dir", type=check_file,
                        default=config.archive_dir, metavar=_(u"path"))

    # config dir for future use
    parser.add_argument(u"--config-dir", type=check_file,
                        default = config.archive_dir, metavar = _(u"path"))

    # Asynchronous put/get concurrency limit
    # (default of 0 disables asynchronicity).
    parser.add_argument(u"--asynchronous-upload", action=u"store_const", const=1)

    # force verify to compare data, not just hashes
    parser.add_argument(u"--compare-data", action=u"store_true")

    # When symlinks are encountered, the item they point to is copied rather than
    # the symlink.
    parser.add_argument(u"--copy-links", action=u"store_true")

    # Don't actually do anything, but still report what would be done
    parser.add_argument(u"--dry-run", action=u"store_true")

    # TRANSL: Used in usage help to represent an ID for a GnuPG key. Example:
    # --encrypt-key <gpg_key_id>
    parser.add_argument(u"--encrypt-key", metavar=_(u"gpg-key-id"),
                        action=u"append")

    # secret keyring in which the private encrypt key can be found
    parser.add_argument(u"--encrypt-secret-keyring", metavar=_(u"path"))

    parser.add_argument(u"--encrypt-sign-key", metavar=_(u"gpg-key-id"),
                        action=u"append")

    # TRANSL: Used in usage help to represent a "glob" style pattern for
    # matching one or more files, as described in the documentation.
    # Example:
    # --exclude <shell_pattern>
    parser.add_argument(u"--exclude", metavar=_(u"shell_pattern"), action=AddSelectionAction)

    parser.add_argument(u"--exclude-device-files", action=AddSelectionAction)

    parser.add_argument(u"--exclude-filelist", type=check_file,
                        metavar=_(u"filename"),
                        action=AddFilistAction)

    # TRANSL: Used in usage help to represent the name of a file. Example:
    # --log-file <filename>
    parser.add_argument(u"--exclude-if-present", metavar=_(u"filename"),
                        type=check_file, action=AddSelectionAction)

    parser.add_argument(u"--exclude-other-filesystems", action=AddSelectionAction)

    # TRANSL: Used in usage help to represent a regular expression (regexp).
    parser.add_argument(u"--exclude-regexp", metavar=_(u"regular_expression"),
                        action=AddSelectionAction)

    # Exclude any files with modification dates older than this from the backup
    parser.add_argument(u"--exclude-older-than", type=check_time, metavar=_(u"time"),
                        action=AddSelectionAction)

    # used to provide a prefix on top of the defaul tar file name
    parser.add_argument(u"--file-prefix", metavar="string", action=u"store")

    # used to provide a suffix for manifest files only
    parser.add_argument(u"--file-prefix-manifest", metavar="string", action=u"store")

    # used to provide a suffix for archive files only
    parser.add_argument(u"--file-prefix-archive", metavar="string", action=u"store")

    # used to provide a suffix for sigature files only
    parser.add_argument(u"--file-prefix-signature", metavar="string", action=u"store")

    # If set, restore only the subdirectory or file specified, not the
    # whole root.
    # TRANSL: Used in usage help to represent a Unix-style path name. Example:
    # --archive-dir <path>
    parser.add_argument(u"--file-to-restore", u"-r", type=check_file, metavar=_(u"path"))

    # Used to confirm certain destructive operations like deleting old files.
    parser.add_argument(u"--force", action=u"store_true")

    # FTP data connection type
    parser.add_argument(u"--ftp-passive", action=u"store_const", const=u"passive", dest=u"ftp_connection")

    parser.add_argument(u"--ftp-regular", action=u"store_const", const=u"regular", dest=u"ftp_connection")

    # If set, forces a full backup if the last full backup is older than
    # the time specified
    parser.add_argument(u"--full-if-older-than", type=check_time, dest=u"full_force_time", metavar=_(u"time"))

    parser.add_argument(u"--gpg-binary", type=check_file, metavar=_(u"path"))

    parser.add_argument(u"--gpg-options", action=u"append", metavar=_(u"options"))

    # TRANSL: Used in usage help to represent an ID for a hidden GnuPG key. Example:
    # --hidden-encrypt-key <gpg_key_id>
    parser.add_argument(u"--hidden-encrypt-key", metavar=_(u"gpg-key-id"))

    # Fake-root for iDrived backend
    parser.add_argument(u"--idr-fakeroot", dest=u"fakeroot", type=check_file, metavar=_(u"path"))

    # ignore (some) errors during operations; supposed to make it more
    # likely that you are able to restore data under problematic
    # circumstances. the default should absolutely always be False unless
    # you know what you are doing.
    parser.add_argument(u"--ignore-errors", action=u"store_true")

    # Whether to use the full email address as the user name when
    # logging into an imap server. If false just the user name
    # part of the email address is used.
    parser.add_argument(u"--imap-full-address", action=u"store_true")

    # Name of the imap folder where we want to store backups.
    # Can be changed with a command line argument.
    # TRANSL: Used in usage help to represent an imap mailbox
    parser.add_argument(u"--imap-mailbox", metavar=_(u"imap_mailbox"))

    parser.add_argument(u"--include", metavar=_(u"shell_pattern"), action=AddSelectionAction)

    parser.add_argument(u"--include-filelist", type=check_file, metavar=_(u"filename"), action=AddFilistAction)

    parser.add_argument(u"--include-regexp", metavar=_(u"regular_expression"), action=AddSelectionAction)

    parser.add_argument(u"--log-fd", type=set_log_fd, metavar=_(u"file_descriptor"))

    # TRANSL: Used in usage help to represent the name of a file. Example:
    # --log-file <filename>
    parser.add_argument(u"--log-file", type=set_log_file, metavar=_(u"log_filename"))

    # log option to add timestamp and level to log entries
    parser.add_argument(u"--log-timestamp", action=u"store_true")

    # Maximum block size for large files
    parser.add_argument(u"--max-blocksize", type=int, metavar=_(u"number"))

    # TRANSL: Used in usage help (noun)
    parser.add_argument(u"--name", dest=u"backup_name",
                        default=config.backup_name, metavar=_(u"backup name"))

    # If set to false, then do not encrypt files on remote system
    parser.add_argument(u"--no-encryption", action=u"store_false", dest=u"encryption")

    # If set to false, then do not compress files on remote system
    parser.add_argument(u"--no-compression", action=u"store_false", dest=u"compression")

    # If set, print the statistics after every backup session
    parser.add_argument(u"--no-print-statistics", action=u"store_false", dest=u"print_statistics")

    # If true, filelists and directory statistics will be split on
    # nulls instead of newlines.
    parser.add_argument(u"--null-separator", action=u"store_true")

    # number of retries on network operations
    # TRANSL: Used in usage help to represent a desired number of
    # something. Example:
    # --num-retries <number>
    parser.add_argument(u"--num-retries", type=int, metavar=_(u"number"))

    # File owner uid keeps number from tar file. Like same option in GNU tar.
    parser.add_argument(u"--numeric-owner", action=u"store_true")

    # Do no restore the uid/gid when finished, useful if you're restoring
    # data without having root privileges or Unix users support
    parser.add_argument(u"--do-not-restore-ownership", action=u"store_true")

    # Sync only required metadata
    parser.add_argument(u"--metadata-sync-mode",
                        default=u"partial",
                        choices=(u"full", u"partial"))

    # Level of Redundancy in % for Par2 files
    parser.add_argument(u"--par2-redundancy", type=int, metavar=_(u"number"))

    # Verbatim par2 options
    parser.add_argument(u"--par2-options", action=u"append", metavar=_(u"options"))

    # Number of par2 volumes
    parser.add_argument(u"--par2-volumes", type=int, metavar=_(u"number"))

    # Used to display the progress for the full and incremental backup operations
    parser.add_argument(u"--progress", action=u"store_true")

    # Used to control the progress option update rate in seconds. Default: prompts each 3 seconds
    parser.add_argument(u"--progress-rate", type=int, metavar=_(u"number"))

    # option to rename files during restore
    parser.add_argument(u"--rename", type=check_file, nargs=2, action=AddRenameAction)

    # Restores will try to bring back the state as of the following time.
    # If it is None, default to current time.
    # TRANSL: Used in usage help to represent a time spec for a previous
    # point in time, as described in the documentation. Example:
    # duplicity remove-older-than time [options] target_url
    parser.add_argument(u"--restore-time", u"--time", u"-t", type=check_time, metavar=_(u"time"))

    # user added rsync options
    parser.add_argument(u"--rsync-options", action=u"append", metavar=_(u"options"))

    # Whether to create European buckets (sorry, hard-coded to only
    # support european for now).
    parser.add_argument(u"--s3-european-buckets", action=u"store_true")

    # Whether to use S3 Reduced Redundancy Storage
    parser.add_argument(u"--s3-use-rrs", action=u"store_true")

    # Whether to use S3 Infrequent Access Storage
    parser.add_argument(u"--s3-use-ia", action=u"store_true")

    # Whether to use S3 Glacier Storage
    parser.add_argument(u"--s3-use-glacier", action=u"store_true")

    # Whether to use S3 Glacier IR Storage
    parser.add_argument(u"--s3-use-glacier-ir", action=u"store_true")

    # Whether to use S3 Glacier Deep Archive Storage
    parser.add_argument(u"--s3-use-deep-archive", action=u"store_true")

    # Whether to use S3 One Zone Infrequent Access Storage
    parser.add_argument(u"--s3-use-onezone-ia", action=u"store_true")

    # Whether to use "new-style" subdomain addressing for S3 buckets. Such
    # use is not backwards-compatible with upper-case buckets, or buckets
    # that are otherwise not expressable in a valid hostname.
    parser.add_argument(u"--s3-use-new-style", action=u"store_true")

    # Whether to use plain HTTP (without SSL) to send data to S3
    # See <https://bugs.launchpad.net/duplicity/+bug/433970>.
    parser.add_argument(u"--s3-unencrypted-connection", action=u"store_true")

    # Chunk size used for S3 multipart uploads.The number of parallel uploads to
    # S3 be given by chunk size / volume size. Use this to maximize the use of
    # your bandwidth. Defaults to 25MB
    parser.add_argument(u"--s3-multipart-chunk-size", type=set_megs, metavar=_(u"number"))

    # Number of processes to set the Processor Pool to when uploading multipart
    # uploads to S3. Use this to control the maximum simultaneous uploads to S3.
    parser.add_argument(u"--s3-multipart-max-procs", type=int, metavar=_(u"number"))

    # Number of seconds to wait for each part of a multipart upload to S3. Use this
    # to prevent hangups when doing a multipart upload to S3.
    parser.add_argument(u"--s3-multipart-max-timeout", type=int, metavar=_(u"number"))

    # Option to allow the s3/boto backend use the multiprocessing version.
    parser.add_argument(u"--s3-use-multiprocessing", action=u"store_true")

    # Option to allow use of server side encryption in s3
    parser.add_argument(u"--s3-use-server-side-encryption", action=u"store_true", dest=u"s3_use_sse")

    # Options to allow use of server side KMS encryption
    parser.add_argument(u"--s3-use-server-side-kms-encryption", action=u"store_true", dest=u"s3_use_sse_kms")

    parser.add_argument(u"--s3-kms-key-id", action=u"store", dest=u"s3_kms_key_id")

    parser.add_argument(u"--s3-kms-grant", action=u"store", dest=u"s3_kms_grant")

    # Options for specifying region and endpoint of s3
    parser.add_argument(u"--s3-region-name", dest=u"s3_region_name", action=u"store")

    parser.add_argument(u"--s3-endpoint-url", dest=u"s3_endpoint_url", action=u"store")

    # Option to specify a Swift container storage policy.
    parser.add_argument(u"--swift-storage-policy", metavar=_(u"policy"))

    # Number of the largest supported upload size where the Azure library makes only one put call.
    # This is used to upload a single block if the content length is known and is less than this value.
    # The default is 67108864 (64MiB)
    parser.add_argument(u"--azure-max-single-put-size", type=int, metavar=_(u"number"))

    # Number for the block size used by the Azure library to upload a blob if the length is unknown
    # or is larger than the value set by --azure-max-single-put-size".
    # The maximum block size the service supports is 100MiB.
    # The default is 4 * 1024 * 1024 (4MiB)
    parser.add_argument(u"--azure-max-block-size", type=int, metavar=_(u"number"))

    # The number for the maximum parallel connections to use when the blob size exceeds 64MB.
    # max_connections (int) - Maximum number of parallel connections to use when the blob size exceeds 64MB.
    parser.add_argument(u"--azure-max-connections", type=int, metavar=_(u"number"))

    # Standard storage tier used for storring backup files (Hot|Cool|Archive).
    parser.add_argument(u"--azure-blob-tier", metavar=_(u"Hot|Cool|Archive"))

    # scp command to use (ssh pexpect backend)
    parser.add_argument(u"--scp-command", metavar=_(u"command"))

    # sftp command to use (ssh pexpect backend)
    parser.add_argument(u"--sftp-command", metavar=_(u"command"))

    # allow the user to switch cloudfiles backend
    parser.add_argument(u"--cf-backend", metavar=_(u"pyrax|cloudfiles"))

    # Option that causes the B2 backend to hide files instead of deleting them
    parser.add_argument(u"--b2-hide-files", action=u"store_true")

    # TRANSL: Used in usage help to represent an ID for a GnuPG key. Example:
    # --encrypt-key <gpg_key_id>
    parser.add_argument(u"--sign-key", type=set_sign_key, metavar=_(u"gpg-key-id"))

    # default to batch mode using public-key encryption
    parser.add_argument(u"--ssh-askpass", action=u"store_true")

    # user added ssh options
    parser.add_argument(u"--ssh-options", action=u"append", metavar=_(u"options"))

    # user added ssl options (used by webdav, lftp backend)
    parser.add_argument(u"--ssl-cacert-file", metavar=_(u"pem formatted bundle of certificate authorities"))

    parser.add_argument(u"--ssl-cacert-path", metavar=_(u"path to a folder with certificate authority files"))

    parser.add_argument(u"--ssl-no-check-certificate", action=u"store_true")

    # header options for Webdav
    parser.add_argument(u"--webdav-headers", metavar=_(u"extra headers for Webdav, like 'Cookie,name=value'"))

    # Working directory for the tempfile module. Defaults to /tmp on most systems.
    parser.add_argument(u"--tempdir", dest=u"temproot", type=check_file, metavar=_(u"path"))

    # network timeout value
    # TRANSL: Used in usage help. Example:
    # --timeout <seconds>
    parser.add_argument(u"--timeout", type=int, metavar=_(u"seconds"))

    # Character used like the ":" in time strings like
    # 2002-08-06T04:22:00-07:00.  The colon isn't good for filenames on
    # windows machines.
    # TRANSL: abbreviation for "character" (noun)
    parser.add_argument(u"--time-separator", metavar=_(u"char"))

    # Whether to specify --use-agent in GnuPG options
    parser.add_argument(u"--use-agent", action=u"store_true")

    parser.add_argument(u"--verbosity", u"-v", type=check_verbosity, metavar=u"[0-9]")

    parser.add_argument(u"--version", u"-V", action="version", version=u"%(prog) __version__")

    # option for mediafire to purge files on delete instead of sending to trash
    parser.add_argument(u"--mf-purge", action=u"store_true")

    parser.add_argument(u"--mp-segment-size", type=set_mpsize, metavar=_(u"number"))

    # volume size
    # TRANSL: Used in usage help to represent a desired number of
    # something. Example:
    # --num-retries <number>
    parser.add_argument(u"--volsize", type=set_volsize, metavar=_(u"number"))

    # If set, collect only the file status, not the whole root.
    parser.add_argument(u"--file-changed", type=check_file, metavar=_(u"path"))

    # If set, skip collecting the files_changed list in statistics, nullifies --file-changed
    parser.add_argument(u"--no-files-changed", action=u"store_true")

    # If set, show file changes (new, deleted, changed) in the specified backup
    #  set (0 specifies latest, 1 specifies next latest, etc.)
    parser.add_argument(u"--show-changes-in-set", type=int, metavar=_(u"number"))

    # delay time before next try after a failure of a backend operation
    # TRANSL: Used in usage help. Example:
    # --backend-retry-delay <seconds>
    parser.add_argument(u"--backend-retry-delay", type=int, metavar=_(u"seconds"))

    # TODO: Find a way to nuke these test options in production.

    # TESTING ONLY - trigger Pydev debugger
    parser.add_argument(u"--pydevd", action=u"store_true", help=argparse.SUPPRESS)

    # TESTING ONLY - skips upload for a given volume
    parser.add_argument(u"--skip-volume", type=int, help=argparse.SUPPRESS)

    # TESTING ONLY - raises exception after volume
    parser.add_argument(u"--fail-on-volume", type=int, help=argparse.SUPPRESS)

    # TESTING ONLY - set current time
    parser.add_argument(u"--current-time", type=int, help=argparse.SUPPRESS)

    # parse the options
    args = parser.parse_args(arglist)

    # Copy all arguments and their values to the config module.  Don't copy
    # attributes that are 'hidden' (start with an underscore) or whose name is
    # the empty string (used for arguments that don't directly store a value
    # by using dest="")
    for f in [x for x in dir(args) if x and not x.startswith(u"_")]:
        v = getattr(args, f)
        setattr(config, f, v)

    # process first arg as possible command
    args = config.positional
    if args:
        cmd = args.pop(0)
        # look for possible abbreviations
        possible = [c for c in commands.keys() if c.startswith(cmd)]
        # no unique match, that's an error
        if len(possible) > 1:
            command_line_error(f"command '{cmd}' not unique: could be {' or '.join(possible)}")
        # only one match, that's a keeper, maybe
        elif len(possible) == 1:
            cmd = possible[0]
            if cmd not in commands.keys():
                command_line_error(f"command '{cmd}' is not a duplicity command.")
        # no matches, assume implied cmd
        elif not possible:
            args.insert(0, cmd)
            cmd = u"implied"
            commands[cmd] = [u"defer", u"defer"]

    # commands just need standard checks
    setattr(config, cmd, args)
    num_expect = len(commands[cmd])
    if len(args) != num_expect:
        command_line_error(f"Expected {num_expect} args, got {len(args)}.")

    targets = commands[cmd]
    for n in range(len(targets)):
        if targets[n] != u"defer":
            name = f"check_{targets[n]}"
            func = getattr(commandline, name)
            setattr(config, targets[n], func(args[n]))

    # other commands need added processing
    if cmd == u"remove-older-than":
        config.remove_time = dup_time.genstrtotime(arg)

    elif cmd == u"remove-all-but-n-full":
        config.remove_all_but_n_full_mode = True
        arg = args[0]
        config.keep_chains = int(arg)
        if not config.keep_chains > 0:
            command_line_error(cmd + u" count must be > 0")

    elif cmd == u"remove-all-inc-of-but-n-full":
        config.remove_all_inc_of_but_n_full_mode = True
        arg = args[0]
        config.keep_chains = int(arg)
        if not config.keep_chains > 0:
            command_line_error(cmd + u" count must be > 0")

    backend_url = config.target_url or config.source_url
    if config.backup_name is None:
        config.backup_name = generate_default_backup_name(backend_url)

    # convert file_prefix* string
    if isinstance(config.file_prefix, str):
        config.file_prefix = bytes(config.file_prefix, u'utf-8')
    if isinstance(config.file_prefix_manifest, str):
        config.file_prefix_manifest = bytes(config.file_prefix_manifest, u'utf-8')
    if isinstance(config.file_prefix_archive, str):
        config.file_prefix_archive = bytes(config.file_prefix_archive, u'utf-8')
    if isinstance(config.file_prefix_signature, str):
        config.file_prefix_signature = bytes(config.file_prefix_signature, u'utf-8')

    # set and expand archive dir
    set_archive_dir(expand_archive_dir(config.archive_dir,
                                       config.backup_name))

    log.Info(_(u"Using archive dir: %s") % (config.archive_dir_path.uc_name,))
    log.Info(_(u"Using backup name: %s") % (config.backup_name,))

    return args


def command_line_error(message):
    u"""Indicate a command line error and exit"""
    raise CommandLineError(_(f"Command line error: {message}\n") +
                           _(u"Enter 'duplicity --help' for help screen."),
                           log.ErrorCode.command_line)


def set_archive_dir(dirstring):
    u"""Check archive dir and set global"""
    if not os.path.exists(dirstring):
        try:
            os.makedirs(dirstring)
        except Exception:
            pass
    archive_dir_path = path.Path(dirstring)
    if not archive_dir_path.isdir():
        log.FatalError(_(f"Specified archive directory '{archive_dir_path.uc_name}' does not exist, "
                         u"or is not a directory"),
                       log.ErrorCode.bad_archive_dir)
    config.archive_dir_path = archive_dir_path


def set_sign_key(sign_key):
    u"""Set config.sign_key assuming proper key given"""
    if not re.search(u"^(0x)?([0-9A-Fa-f]{8}|[0-9A-Fa-f]{16}|[0-9A-Fa-f]{40})$", sign_key):
        log.FatalError(_(u"Sign key should be an 8, 16, or 40 character hex string, like "
                         u"'AA0E73D2'.\nReceived '%s' instead.") % (sign_key,),
                       log.ErrorCode.bad_sign_key)
    config.gpg_profile.sign_key = sign_key


def set_selection():
    u"""Return selection iter starting at filename with arguments applied"""
    global select_opts, select_files
    sel = selection.Select(config.local_path)
    sel.ParseArgs(select_opts, select_files)
    config.select = sel.set_iter()


def process_local_dir(action, local_pathname):
    u"""Check local directory, set config.local_path"""
    local_path = path.Path(path.Path(local_pathname).get_canonical())
    if action == u"restore":
        if (local_path.exists() and not local_path.isemptydir()) and not config.force:
            log.FatalError(_(u"Restore destination directory %s already "
                             u"exists.\nWill not overwrite.") % (local_path.uc_name,),
                           log.ErrorCode.restore_dir_exists)
    elif action == u"verify":
        if not local_path.exists():
            log.FatalError(_(u"Verify directory %s does not exist") %
                           (local_path.uc_name,),
                           log.ErrorCode.verify_dir_doesnt_exist)
    else:
        assert action == u"full" or action == u"inc"
        if not local_path.exists():
            log.FatalError(_(u"Backup source directory %s does not exist.")
                           % (local_path.uc_name,),
                           log.ErrorCode.backup_dir_doesnt_exist)

    config.local_path = local_path


def check_consistency(action):
    u"""Final consistency check, see if something wrong with command line"""

    if config.ignore_errors:
        log.Warn(_(u"Running in 'ignore errors' mode due to --ignore-errors.\n"
                   u"Please reconsider if this was not intended"))

    if config.hidden_encrypt_key:
        config.gpg_profile.hidden_recipients.append(config.hidden_encrypt_key)

    def assert_only_one(arglist):
        u"""Raises error if two or more of the elements of arglist are true"""
        n = 0
        for m in arglist:
            if m:
                n += 1
        command_line_error(u"Invalid syntax, two conflicting modes specified")

    if action in [u"list-current", u"collection-status",
                  u"cleanup", u"remove-old", u"remove-all-but-n-full", u"remove-all-inc-of-but-n-full"]:
        assert_only_one([list_current, collection_status, cleanup,
                         config.remove_time is not None])
    elif action == u"restore" or action == u"verify":
        if full_backup:
            command_line_error(u"full option cannot be used when "
                               u"restoring or verifying")
        elif config.incremental:
            command_line_error(u"incremental option cannot be used when "
                               u"restoring or verifying")
        if select_opts and action == u"restore":
            log.Warn(_(u"Command line warning: %s") % _(u"Selection options --exclude/--include\n"
                                                        u"currently work only when backing up,"
                                                        u"not restoring."))
    else:
        assert action == u"inc" or action == u"full"
        if verify:
            command_line_error(u"verify option cannot be used "
                               u"when backing up")
        if config.restore_dir:
            command_line_error(u"restore option incompatible with %s backup"
                               % (action,))
        if sum([config.s3_use_rrs, config.s3_use_ia, config.s3_use_onezone_ia]) >= 2:
            command_line_error(u"only one of --s3-use-rrs, --s3-use-ia, and --s3-use-onezone-ia may be used")


def ProcessCommandLine(cmdline_list):
    u"""Process command line, set config, return action

    action will be "list-current", "collection-status", "cleanup",
    "remove-old", "restore", "verify", "full", or "inc".

    """
    # build initial gpg_profile
    config.gpg_profile = gpg.GPGProfile()

    # parse command line
    args = parse_cmdline_options(cmdline_list)

    # if we get a different gpg-binary from the commandline then redo gpg_profile
    if config.gpg_binary is not None:
        src = config.gpg_profile
        config.gpg_profile = gpg.GPGProfile(
            passphrase=src.passphrase,
            sign_key=src.sign_key,
            recipients=src.recipients,
            hidden_recipients=src.hidden_recipients)
    log.Debug(_(u"GPG binary is %s, version %s") %
              ((config.gpg_binary or u'gpg'), config.gpg_profile.gpg_version))

    # we can now try to import all the backends
    backend.import_backends()

    # parse_cmdline_options already verified that we got exactly 1 or 2
    # positional arguments.  Convert to action
    if len(args) == 1:
        if list_current:
            action = u"list-current"
        elif collection_status:
            action = u"collection-status"
        elif cleanup:
            action = u"cleanup"
        elif config.remove_time is not None:
            action = u"remove-old"
        elif config.remove_all_but_n_full_mode:
            action = u"remove-all-but-n-full"
        elif config.remove_all_inc_of_but_n_full_mode:
            action = u"remove-all-inc-of-but-n-full"
        else:
            command_line_error(u"Too few arguments")

        config.backend = backend.get_backend(args[0])
        if not config.backend:
            command_line_error(_(f"Bad URL '{args[0]})'.\n"
                                 "Examples of URL strings are 'scp://user@host.net:1234/path' and\n"
                                 "'file:///usr/local'.  See the man page for more information."""))
    elif len(args) == 2:
        # Figure out whether backup or restore
        backup, local_pathname = set_backend(args[0], args[1])
        if backup:
            if full_backup:
                action = u"full"
            else:
                action = u"inc"
        else:
            if verify:
                action = u"verify"
            else:
                action = u"restore"

        process_local_dir(action, local_pathname)
        if action in [u'full', u'inc', u'verify']:
            set_selection()

    check_consistency(action)

    log.Info(_(u"Main action: ") + action)
    return action


def usage():
    u"""Returns terse usage info. The code is broken down into pieces for ease of
    translation maintenance. Any comments that look extraneous or redundant should
    be assumed to be for the benefit of translators, since they can get each string
    (paired with its preceding comment, if any) independently of the others."""

    trans = {
        # TRANSL: Used in usage help to represent a Unix-style path name. Example:
        # rsync://user[:password]@other_host[:port]//absolute_path
        u'absolute_path':_(u"absolute_path"),

        # TRANSL: Used in usage help. Example:
        # tahoe://alias/some_dir
        u'alias':_(u"alias"),

        # TRANSL: Used in help to represent a "bucket name" for Amazon Web
        # Services' Simple Storage Service (S3). Example:
        # s3://other.host/bucket_name[/prefix]
        u'bucket_name':_(u"bucket_name"),

        # TRANSL: abbreviation for "character" (noun)
        u'char':_(u"char"),

        # TRANSL: noun
        u'command':_(u"command"),

        # TRANSL: Used in usage help to represent the name of a container in
        # Amazon Web Services' Cloudfront. Example:
        # cf+http://container_name
        u'container_name':_(u"container_name"),

        # TRANSL: noun
        u'count':_(u"count"),

        # TRANSL: Used in usage help to represent the name of a file directory
        u'directory':_(u"directory"),

        # TRANSL: Used in usage help to represent the name of a file. Example:
        # --log-file <filename>
        u'filename':_(u"filename"),

        # TRANSL: Used in usage help to represent an ID for a GnuPG key. Example:
        # --encrypt-key <gpg_key_id>
        u'gpg_key_id':_(u"gpg-key-id"),

        # TRANSL: Used in usage help, e.g. to represent the name of a code
        # module. Example:
        # rsync://user[:password]@other.host[:port]::/module/some_dir
        u'module':_(u"module"),

        # TRANSL: Used in usage help to represent a desired number of
        # something. Example:
        # --num-retries <number>
        u'number':_(u"number"),

        # TRANSL: Used in usage help. (Should be consistent with the "Options:"
        # header.) Example:
        # duplicity [full|incremental] [options] source_dir target_url
        u'options':_(u"options"),

        # TRANSL: Used in usage help to represent an internet hostname. Example:
        # ftp://user[:password]@other.host[:port]/some_dir
        u'other_host':_(u"other.host"),

        # TRANSL: Used in usage help. Example:
        # ftp://user[:password]@other.host[:port]/some_dir
        u'password':_(u"password"),

        # TRANSL: Used in usage help to represent a Unix-style path name. Example:
        # --archive-dir <path>
        u'path':_(u"path"),

        # TRANSL: Used in usage help to represent a TCP port number. Example:
        # ftp://user[:password]@other.host[:port]/some_dir
        u'port':_(u"port"),

        # TRANSL: Used in usage help. This represents a string to be used as a
        # prefix to names for backup files created by Duplicity. Example:
        # s3://other.host/bucket_name[/prefix]
        u'prefix':_(u"prefix"),

        # TRANSL: Used in usage help to represent a Unix-style path name. Example:
        # rsync://user[:password]@other.host[:port]/relative_path
        u'relative_path':_(u"relative_path"),

        # TRANSL: Used in usage help. Example:
        # --timeout <seconds>
        u'seconds':_(u"seconds"),

        # TRANSL: Used in usage help to represent a "glob" style pattern for
        # matching one or more files, as described in the documentation.
        # Example:
        # --exclude <shell_pattern>
        u'shell_pattern':_(u"shell_pattern"),

        # TRANSL: Used in usage help to represent the name of a single file
        # directory or a Unix-style path to a directory. Example:
        # file:///some_dir
        u'some_dir':_(u"some_dir"),

        # TRANSL: Used in usage help to represent the name of a single file
        # directory or a Unix-style path to a directory where files will be
        # coming FROM. Example:
        # duplicity [full|incremental] [options] source_dir target_url
        u'source_dir':_(u"source_dir"),

        # TRANSL: Used in usage help to represent a URL files will be coming
        # FROM. Example:
        # duplicity [restore] [options] source_url target_dir
        u'source_url':_(u"source_url"),

        # TRANSL: Used in usage help to represent the name of a single file
        # directory or a Unix-style path to a directory. where files will be
        # going TO. Example:
        # duplicity [restore] [options] source_url target_dir
        u'target_dir':_(u"target_dir"),

        # TRANSL: Used in usage help to represent a URL files will be going TO.
        # Example:
        # duplicity [full|incremental] [options] source_dir target_url
        u'target_url':_(u"target_url"),

        # TRANSL: Used in usage help to represent a time spec for a previous
        # point in time, as described in the documentation. Example:
        # duplicity remove-older-than time [options] target_url
        u'time':_(u"time"),

        # TRANSL: Used in usage help to represent a user name (i.e. login).
        # Example:
        # ftp://user[:password]@other.host[:port]/some_dir
        u'user':_(u"user"),

        # TRANSL: account id for b2. Example: b2://account_id@bucket/
        u'account_id':_(u"account_id"),

        # TRANSL: application_key for b2.
        # Example: b2://account_id:application_key@bucket/
        u'application_key':_(u"application_key"),

        # TRANSL: remote name for rclone.
        # Example: rclone://remote:/some_dir
        u'remote':_(u"remote"),
    }

    # TRANSL: Header in usage help
    msg = u"""
  duplicity [full|incremental] [%(options)s] %(source_dir)s %(target_url)s
  duplicity [restore] [%(options)s] %(source_url)s %(target_dir)s
  duplicity verify [%(options)s] %(source_url)s %(target_dir)s
  duplicity collection-status [%(options)s] %(target_url)s
  duplicity list-current-files [%(options)s] %(target_url)s
  duplicity cleanup [%(options)s] %(target_url)s
  duplicity remove-older-than %(time)s [%(options)s] %(target_url)s
  duplicity remove-all-but-n-full %(count)s [%(options)s] %(target_url)s
  duplicity remove-all-inc-of-but-n-full %(count)s [%(options)s] %(target_url)s

""" % trans

    # TRANSL: Header in usage help
    msg = msg + _(u"Backends and their URL formats:") + u"""
  azure://%(container_name)s
  b2://%(account_id)s[:%(application_key)s]@%(bucket_name)s/[%(some_dir)s/]
  boto3+s3://%(bucket_name)s[/%(prefix)s]
  cf+http://%(container_name)s
  dpbx:///%(some_dir)s
  file:///%(some_dir)s
  ftp://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  ftps://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  gdocs://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  for gdrive:// a <service-account-url> like the following is required
        <serviceaccount-name>@<serviceaccount-name>.iam.gserviceaccount.com
  gdrive://<service-account-url>/target-folder/?driveID=<SHARED DRIVE ID> (for GOOGLE Shared Drive)
  gdrive://<service-account-url>/target-folder/?myDriveFolderID=<google-myDrive-folder-id> (for GOOGLE MyDrive)
  hsi://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  imap://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  mega://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  megav2://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  mf://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  onedrive://%(some_dir)s
  pca://%(container_name)s
  pydrive://%(user)s@%(other_host)s/%(some_dir)s
  rclone://%(remote)s:/%(some_dir)s
  rsync://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(relative_path)s
  rsync://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]//%(absolute_path)s
  rsync://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]::/%(module)s/%(some_dir)s
  s3+http://%(bucket_name)s[/%(prefix)s]
  s3://%(other_host)s[:%(port)s]/%(bucket_name)s[/%(prefix)s]
  scp://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  ssh://%(user)s[:%(password)s]@%(other_host)s[:%(port)s]/%(some_dir)s
  swift://%(container_name)s
  tahoe://%(alias)s/%(directory)s
  webdav://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s
  webdavs://%(user)s[:%(password)s]@%(other_host)s/%(some_dir)s

""" % trans

    # TRANSL: Header in usage help
    msg = msg + _(u"Commands:") + u"""
  cleanup <%(target_url)s>
  collection-status <%(target_url)s>
  full <%(source_dir)s> <%(target_url)s>
  incr <%(source_dir)s> <%(target_url)s>
  list-current-files <%(target_url)s>
  remove-all-but-n-full <%(count)s> <%(target_url)s>
  remove-all-inc-of-but-n-full <%(count)s> <%(target_url)s>
  remove-older-than <%(time)s> <%(target_url)s>
  restore <%(source_url)s> <%(target_dir)s>
  verify <%(target_url)s> <%(source_dir)s>

""" % trans

    return msg


if __name__ == u"__main__":
    log.setup()
    args = ProcessCommandLine(sys.argv[1:])
    print(args, argparse.Namespace)
