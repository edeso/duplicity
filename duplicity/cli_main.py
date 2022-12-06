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
from pathvalidate import is_valid_filepath
from pathvalidate import sanitize_filepath

from duplicity import cli_usage
from duplicity import config
from duplicity import dup_time
from duplicity import errors
from duplicity import gpg
from duplicity import log
from duplicity import path

select_opts = []  # Will hold all the selection options
select_files = []  # Will hold file objects when filelist given

# commands and type of positional args expected
commands = {
    u"backup": [u"url_or_dir", u"url_or_dir"],
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
        addarg = os.fsdecode(value) if isinstance(values, bytes) else values
        select_opts.append((os.fsdecode(option_string), addarg))


class AddFilistAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(AddFilistAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        select_opts.append((os.fsdecode(s), os.fsdecode(filename)))
        try:
            select_files.append(io.open(filename, u"rt", encoding=u"UTF-8"))
        except Exception as e:
            raise argparse.ArgumentError(str(e))


class AddRenameAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(AddRenameAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        key = os.fsencode(os.path.normcase(os.path.normpath(values[0])))
        config.rename[key] = os.fsencode(values[1])


def check_count(val):
    try:
        return int(val)
    except Exception as e:
        command_line_error(f"'{val}' is not an int.")


def check_remove_time(val):
    try:
        return dup_time.genstrtotime(val)
    except Exception as e:
        command_line_error(str(e))


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

    def make_wide(formatter, w=120, h=46 ):
        """Return a wider HelpFormatter, if possible."""
        try:
            # https://stackoverflow.com/a/5464440
            # beware: "Only the name of this class is considered a public API."
            kwargs = {'width': w, 'max_help_position': h}
            formatter(None, **kwargs)
            return lambda prog: formatter(prog, **kwargs)
        except TypeError:
            warnings.warn("argparse help formatter failed, falling back.")
            return formatter

    parser = argparse.ArgumentParser(
        prog=u'duplicity',
        argument_default=None,
        formatter_class=make_wide(argparse.ArgumentDefaultsHelpFormatter),
    )
    subparsers = parser.add_subparsers(required=False)

    subp_dict = dict()
    for subc, meta in commands.items():
        subp_dict[subc] = subparsers.add_parser(subc, help=u' '.join(meta))
        for arg in meta:
            subp_dict[subc].add_argument(arg, type=str)

    parser.add_argument(u"--allow-source-mismatch", action=u"store_true",
                        help=u"Allow different source directories",
                        default=False)

    parser.add_argument(u"--archive-dir", type=check_file, metavar=_(u"path"),
                        help=u"Path to store metadata archives",
                        default=config.archive_dir)

    # TODO: refactor dest=
    parser.add_argument(u"--asynchronous-upload", action=u"store_const", const=1, dest=u"async_concurrency",
                        help=u"Number of async upload tasks, max of 1 for now",
                        default=config.async_concurrency)

    parser.add_argument(u"--azure-blob-tier", metavar=_(u"Hot|Cool|Archive"),
                        help=u"Standard storage tier used for storring backup files (Hot|Cool|Archive)",
                        default=config.azure_blob_tier)

    parser.add_argument(u"--azure-max-connections", type=int, metavar=_(u"number"),
                        help=u"Number of maximum parallel connections to use when the blob size exceeds 64MB",
                        default=config.azure_max_connections)

    parser.add_argument(u"--azure-max-block-size", metavar=_(u"number"), type=int,
                        help=u"Number for the block size to upload a blob if the length is unknown\n"
                             u"or is larger than the value set by --azure-max-single-put-size\n"
                             u"The maximum block size the service supports is 100MiB.",
                        default=config.azure_max_block_size)

    parser.add_argument(u"--azure-max-single-put-size", metavar=_(u"number"), type=int,
                        help=u"Largest supported upload size where the Azure library makes only one put call.\n"
                             u"Used to upload a single block if the content length is known and is less than this",
                        default=config.azure_max_single_put_size)

    parser.add_argument(u"--b2-hide-files", action=u"store_true",
                        help=u"Whether the B2 backend hides files instead of deleting them")

    parser.add_argument(u"--backend-retry-delay", type=int, metavar=_(u"seconds"),
                        help=u"Delay time before next try after a failure of a backend operation",
                        default=config.backend_retry_delay)

    parser.add_argument(u"--cf-backend", metavar=_(u"pyrax|cloudfiles"),
                        help=u"Allow the user to switch cloudfiles backend")

    parser.add_argument(u"--compare-data", action=u"store_true",
                        help=u"Compare data on verify not only signatures",
                        default=False)

    parser.add_argument(u"--config-dir", type=check_file, metavar=_(u"path"),
                        help=u"Path to store configuration files",
                        default=config.archive_dir)

    # When symlinks are encountered, the item they point to is copied rather than
    # the symlink.
    parser.add_argument(u"--copy-links", action=u"store_true",
                        help=u"Copy contents of symlinks instead of linking",
                        default=False)

    # Don't actually do anything, but still report what would be done
    parser.add_argument(u"--dry-run", action=u"store_true",
                        help=u"Perform dry-run with no writes",
                        default=False)

    # TRANSL: Used in usage help to represent an ID for a GnuPG key. Example:
    # --encrypt-key <gpg_key_id>
    parser.add_argument(u"--encrypt-key", metavar=_(u"gpg-key-id"), action=u"append",
                        help=u"GNUpg key for encryption/decryption")

    # secret keyring in which the private encrypt key can be found
    parser.add_argument(u"--encrypt-secret-keyring", metavar=_(u"path"),
                        help=u"Path to secret GNUpg keyring")

    parser.add_argument(u"--encrypt-sign-key", metavar=_(u"gpg-key-id"), action=u"append",
                        help=u"GNUpg key for signing")

    parser.add_argument(u"--exclude", metavar=_(u"shell_pattern"), action=AddSelectionAction,
                        help=u"Exclude globbing pattern")

    parser.add_argument(u"--exclude-device-files", action=u"store_true",
                        help=u"Exclude device files",
                        default=False)

    parser.add_argument(u"--exclude-filelist", metavar=_(u"filename"), action=AddFilistAction,
                        help=u"File with list of file patters to exclude")

    parser.add_argument(u"--exclude-if-present", metavar=_(u"filename"), action=AddSelectionAction,
                        help=u"Exclude directory if this file is present")

    parser.add_argument(u"--exclude-older-than", metavar=_(u"time"), type=check_time, action=AddSelectionAction,
                        help=u"Exclude files older than time")

    parser.add_argument(u"--exclude-other-filesystems", action=u"store_true",
                        help=u"Exclude other filesystems from backup",
                        default=False)

    parser.add_argument(u"--exclude-regexp", metavar=_(u"regex"), action=AddSelectionAction,
                        help=u"Exclude based on regex pattern")

    parser.add_argument(u"--file-changed", type=check_file, metavar=_(u"path"),
                        help=u"Whether to collect only the file status, not the whole root")

    parser.add_argument(u"--file-prefix", metavar="string", action=u"store",
                        help=u"String prefix for all duplicity files")

    parser.add_argument(u"--file-prefix-archive", metavar="string", action=u"store",
                        help = u"String prefix for duplicity difftar files")

    parser.add_argument(u"--file-prefix-manifest", metavar="string", action=u"store",
                        help = u"String prefix for duplicity manifest files")

    parser.add_argument(u"--file-prefix-signature", metavar="string", action=u"store",
                        help = u"String prefix for duplicity signature files")

    parser.add_argument(u"--file-to-restore", u"-r", metavar=_(u"path"), type=check_file,
                        help=u"File or directory path to restore")

    parser.add_argument(u"--force", action=u"store_true",
                        help=u"Force duplicity to actually delete during cleanup",
                        default=False)

    # TODO: refactor dest=
    parser.add_argument(u"--ftp-passive", action=u"store_const", const=u"passive", dest=u"ftp_connection",
                        help=u"Tell FTP to use passive mode",
                        default='passive')

    # TODO: refactor dest=
    parser.add_argument(u"--ftp-regular", action=u"store_const", const=u"regular", dest=u"ftp_connection",
                        help=u"Tell FTP to use regular mode",
                        default='passive')

    parser.add_argument(u"--full-if-older-than", metavar=_(u"time"), type=check_time,
                        help=u"Perform full backup if last full is older than 'time'")

    parser.add_argument(u"--gpg-binary", metavar=_(u"path"), type=check_file,
                        help=u"Path to GNUpg executable file")

    parser.add_argument(u"--gpg-options", metavar=_(u"options"), action=u"append",
                        help=u"Options to append to GNUpg invocation")

    parser.add_argument(u"--hidden-encrypt-key", metavar=_(u"gpg-key-id"),
                        help=u"Hidden GNUpg encryption key")

    parser.add_argument(u"--idr-fakeroot", metavar=_(u"path"), type=check_file,
                        help=u"Fake root for idrive backend")

    parser.add_argument(u"--ignore-errors", action=u"store_true",
                        help=u"Ignore most errors during restore",
                        default=False)

    parser.add_argument(u"--imap-full-address", action=u"store_true",
                        help=u"Whether to use the full email address as the user name",
                        default=False)

    parser.add_argument(u"--imap-mailbox", metavar=_(u"imap_mailbox"),
                        help=u"Name of the imap folder to store backups")

    parser.add_argument(u"--include", metavar=_(u"shell_pattern"), action=AddSelectionAction,
                        help=u"Exclude globbing pattern")

    parser.add_argument(u"--include-filelist", metavar=_(u"filename"), action=AddFilistAction,
                        help=u"File with list of file patters to include")

    parser.add_argument(u"--include-regexp", metavar=_(u"regular_expression"), action=AddSelectionAction,
                        help=u"Exclude based on regex pattern")

    parser.add_argument(u"--log-fd", metavar=_(u"file_descriptor"), type=set_log_fd,
                        help=u"Logging file descripto to use")

    parser.add_argument(u"--log-file", metavar=_(u"log_filename"), type=set_log_file,
                        help=u"Logging filename to use")

    parser.add_argument(u"--log-timestamp", action=u"store_true",
                        help=u"Whether to include timestamp and level in log",
                        default=False)

    parser.add_argument(u"--max-blocksize", metavar=_(u"number"), type=int,
                        help=u"Maximum block size for large files in MB")

    parser.add_argument(u"--mf-purge", action=u"store_true",
                        help=u"Option for mediafire to purge files on delete instead of sending to trash")

    parser.add_argument(u"--mp-segment-size", metavar=_(u"number"), type=set_mpsize,
                        help=u"Swift backend segment size",
                        default=config.mp_segment_size)

    parser.add_argument(u"--name", metavar=_(u"backup name"),
                        help=u"Custom backup name instead of hash",
                        default=config.backup_name)

    parser.add_argument(u"--no-compression", action=u"store_true",
                        help=u"If supplied do not perform compression")

    parser.add_argument(u"--no-encryption", action=u"store_true",
                        help=u"If supplied do not perform encryption")

    parser.add_argument(u"--no-files-changed", action=u"store_true",
                        help=u"Whether to skip collecting the files_changed list in statistics")

    parser.add_argument(u"--no-print-statistics", action=u"store_true",
                        help=u"If supplied do not print statistics")

    parser.add_argument(u"--null-separator", action=u"store_true",
                        help=u"Whether to split on null instead of newline")

    parser.add_argument(u"--num-retries", metavar=_(u"number"), type=int,
                        help=u"Number of retries on network operations",
                        default=config.num_retries)

    parser.add_argument(u"--numeric-owner", action=u"store_true",
                        help=u"Keeps number from tar file. Like same option in GNU tar.",
                        default=False)

    parser.add_argument(u"--do-not-restore-ownership", action=u"store_true",
                        help=u"Do no restore the uid/gid when finished, useful if you're restoring\n" 
                             U"data without having root privileges or Unix users support",
                        default=False)

    parser.add_argument(u"--metadata-sync-mode", choices=(u"full", u"partial"),
                        help=u"Only sync required metadata not all",
                        default=u"partial")

    parser.add_argument(u"--par2-options", metavar=_(u"options"), action=u"append",
                        help=u"Verbatim par2 options.  May be supplied multiple times.")

    parser.add_argument(u"--par2-redundancy", metavar=_(u"number"), type=int, choices=range(5, 99),
                        help=u"Level of Redundancy in percent for Par2 files",
                        default=config.par2_redundancy)

    parser.add_argument(u"--par2-volumes", metavar=_(u"number"), type=int,
                        help=u"Number of par2 volumes",
                        default=config.par2_volumes)

    parser.add_argument(u"--progress", action=u"store_true",
                        help=u"Display progress for the full and incremental backup operations")

    parser.add_argument(u"--progress-rate", metavar=_(u"number"), type=int,
                        help=u"Used to control the progress option update rate in seconds",
                        default=config.progress_rate)

    parser.add_argument(u"--rename", type=check_file, nargs=2, metavar="from to", action=AddRenameAction,
                        help=u"Rename files during restore")

    parser.add_argument(u"--restore-time", u"--time", u"-t", metavar=_(u"time"), type=check_time,
                        help=u"Restores will try to bring back the state as of the following time")

    parser.add_argument(u"--rsync-options", metavar=_(u"options"), action=u"append",
                        help=u"User added rsync options")

    parser.add_argument(u"--s3-european-buckets", action=u"store_true",
                        help=u"Whether to create European buckets")

    parser.add_argument(u"--s3-unencrypted-connection", action=u"store_true",
                        help=u"Whether to use plain HTTP (without SSL) to send data to S3")

    parser.add_argument(u"--s3-use-deep-archive", action=u"store_true",
                        help=u"Whether to use S3 Glacier Deep Archive Storage")

    parser.add_argument(u"--s3-use-glacier", action=u"store_true",
                        help=u"Whether to use S3 Glacier Storage")

    parser.add_argument(u"--s3-use-glacier-ir", action=u"store_true",
                        help="Whether to use S3 Glacier IR Storage")

    parser.add_argument(u"--s3-use-ia", action=u"store_true",
                        help=u"Whether to use S3 Infrequent Access Storage")

    parser.add_argument(u"--s3-use-new-style", action=u"store_true",
                        help=u"Whether to use new-style subdomain addressing for S3 buckets. Such\n"
                             u"use is not backwards-compatible with upper-case buckets, or buckets\n"
                             u"that are otherwise not expressable in a valid hostname")

    parser.add_argument(u"--s3-use-onezone-ia", action=u"store_true",
                        help=u"Whether to use S3 One Zone Infrequent Access Storage")

    parser.add_argument(u"--s3-use-rrs", action=u"store_true",
                        help=u"Whether to use S3 Reduced Redundancy Storage")

    parser.add_argument(u"--s3-multipart-chunk-size", metavar=_(u"number"), type=set_megs,
                        help=u"Chunk size used for S3 multipart uploads.The number of parallel uploads to\n"
                             u"S3 be given by chunk size / volume size. Use this to maximize the use of\n"
                             u"your bandwidth",
                        default=config.s3_multipart_chunk_size)

    parser.add_argument(u"--s3-multipart-max-procs", type=int, metavar=_(u"number"),
                        help=u"Number of processes to set the Processor Pool to when uploading multipart\n"
                             u"uploads to S3. Use this to control the maximum simultaneous uploads to S3",
                        default=config.s3_multipart_max_procs)

    parser.add_argument(u"--s3-multipart-max-timeout", metavar=_(u"number"), type=int,
                        help=u"Number of seconds to wait for each part of a multipart upload to S3. Use this\n"
                             u"to prevent hangups when doing a multipart upload to S3",
                        default=config.s3_multipart_max_timeout)

    parser.add_argument(u"--s3-use-multiprocessing", action=u"store_true",
                        help=u"Option to allow the s3/boto backend use the multiprocessing version")

    # TODO: refactor dest=
    parser.add_argument(u"--s3-use-server-side-encryption", action=u"store_true", dest=u"s3_use_sse",
                        help=u"Option to allow use of server side encryption in s3")

    # TODO: refactor dest=
    parser.add_argument(u"--s3-use-server-side-kms-encryption", action=u"store_true", dest=u"s3_use_sse_kms",
                        help=u"Allow use of server side KMS encryption")

    parser.add_argument(u"--s3-kms-key-id", metavar=_(u"s3_kms_key_id"), action=u"store",
                        help=u"S3 KMS encryption key id")

    parser.add_argument(u"--s3-kms-grant", metavar=_(u"s3_kms_grant"), action=u"store",
                        help=u"S3 KMS grant value")

    parser.add_argument(u"--s3-region-name", metavar=_(u"s3_region_name"), action=u"store",
                        help=u"Specity S3 region name",
                        default=None)

    parser.add_argument(u"--s3-endpoint-url", metavar=_(u"s3_endpoint_url"), action=u"store",
                        help=u"Specity S3 endpoint",
                        default=None)

    parser.add_argument(u"--swift-storage-policy", metavar=_(u"policy"),
                        help=u"Option to specify a Swift container storage policy.",
                        default=None)

    parser.add_argument(u"--scp-command", metavar=_(u"command"),
                        help=u"SCP command to use (ssh pexpect backend)")

    parser.add_argument(u"--sftp-command", metavar=_(u"command"),
                        help=u"SFTP command to use (ssh pexpect backend)")

    parser.add_argument(u"--show-changes-in-set", type=int, metavar=_(u"number"),
                        help=u"Show file changes (new, deleted, changed) in the specified backup\n"
                             u"set (0 specifies latest, 1 specifies next latest, etc.)")

    parser.add_argument(u"--sign-key", type=set_sign_key, metavar=_(u"gpg-key-id"),
                        help=u"Sign key for encryption/decryption")

    parser.add_argument(u"--ssh-askpass", action=u"store_true",
                        help=u"Ask the user for the SSH password. Not for batch usage")

    parser.add_argument(u"--ssh-options", metavar=_(u"options"), action=u"append",
                        help=u"SSH options to add")

    parser.add_argument(u"--ssl-cacert-file", metavar="file",
                        help=_(u"pem formatted bundle of certificate authorities"))

    parser.add_argument(u"--ssl-cacert-path", metavar="path",
                        help=_(u"path to a folder with certificate authority files"))

    parser.add_argument(u"--ssl-no-check-certificate", action=u"store_true",
                        help=u"Set to not validate SSL certificates")

    # TODO: refactor dest=
    parser.add_argument(u"--tempdir", metavar=_(u"path"), type=check_file, dest=u"temproot",
                        help=u"Working directory for temp files",
                        default=config.temproot)

    parser.add_argument(u"--timeout", metavar=_(u"seconds"), type=int,
                        help=u"Network timeout in seconds",
                        default=config.timeout)

    parser.add_argument(u"--time-separator", metavar=_(u"char"),
                        help=u"Character used like the ':' in time strings like\n"
                             u"2002-08-06T04:22:00-07:00",
                        default=config.time_separator)

    parser.add_argument(u"--use-agent", action=u"store_true",
                        help=u"Whether to specify --use-agent in GnuPG options")

    parser.add_argument(u"--verbosity", u"-v", metavar=_(u"[0-9]"), type=check_verbosity,
                        help=u"Logging verbosity")

    parser.add_argument(u"--version", u"-V", action="version", version=u"%(prog) __version__",
                        help=u"Display version and exit")

    parser.add_argument(u"--volsize", metavar=_(u"number"), type=set_volsize,
                        help=u"Volume size to use in MiB",
                        default=int(config.volsize / (1024 * 1024)))

    parser.add_argument(u"--webdav-headers", metavar="string",
                        help=_(u"extra headers for Webdav, like 'Cookie,name=value'"))

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
    cmdvar = cmd.replace(u'-', u'_')
    setattr(config, cmdvar, args)
    num_expect = len(commands[cmd])
    if len(args) != num_expect:
        command_line_error(f"Expected {num_expect} args, got {len(args)}.")

    targets = commands[cmd]
    for n in range(len(targets)):
        if targets[n] != u"defer":
            name = f"check_{targets[n]}"
            func = getattr(cli_main, name)
            setattr(config, targets[n], func(args[n]))

    # other commands need added processing
    if cmd == u"remove-all-but-n-full":
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


if __name__ == u"__main__":
    log.setup()
    args = ProcessCommandLine(sys.argv[1:])
    print(args, argparse.Namespace)
