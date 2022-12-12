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

from duplicity import config
from duplicity import dup_time
from duplicity import errors
from duplicity import gpg
from duplicity import log
from duplicity import path
from duplicity.cli_util import *


# TODO: move to config
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


def parse_cmdline_options(arglist):
    u"""Parse argument list"""

    def make_wide(formatter, w=120, h=46):
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

    def d(val):
        if isinstance(val, (str, bytes)):
            if val:
                return val
            else:
                return None
        else:
            return None

    parser = argparse.ArgumentParser(
        prog=u'duplicity',
        argument_default=None,
        formatter_class=make_wide(argparse.ArgumentDefaultsHelpFormatter),
    )
    subparsers = parser.add_subparsers(
        title=u"valid subcommands",
        required=False,
    )

    subp_dict = dict()
    for subc, meta in commands.items():
        subp_dict[subc] = subparsers.add_parser(subc, help=f"# duplicity {subc} {u' '.join(meta)}")
        for arg in meta:
            subp_dict[subc].add_argument(arg, type=str)

    parser.add_argument(u"--allow-source-mismatch", action=u"store_true",
                        help=u"Allow different source directories",
                        default=d(config.allow_source_mismatch))

    parser.add_argument(u"--archive-dir", type=check_file, metavar=_(u"path"),
                        help=u"Path to store metadata archives",
                        default=d(config.archive_dir))

    parser.add_argument(u"--asynchronous-upload", action=u"store_const", const=1, dest=u"async_concurrency",
                        help=u"Number of async upload tasks, max of 1 for now",
                        default=d(config.async_concurrency))

    parser.add_argument(u"--azure-blob-tier", metavar=_(u"Hot|Cool|Archive"),
                        help=u"Standard storage tier used for storring backup files (Hot|Cool|Archive)",
                        default=d(config.azure_blob_tier))

    parser.add_argument(u"--azure-max-connections", type=int, metavar=_(u"number"),
                        help=u"Number of maximum parallel connections to use when the blob size exceeds 64MB",
                        default=d(config.azure_max_connections))

    parser.add_argument(u"--azure-max-block-size", metavar=_(u"number"), type=int,
                        help=u"Number for the block size to upload a blob if the length is unknown\n"
                             u"or is larger than the value set by --azure-max-single-put-size\n"
                             u"The maximum block size the service supports is 100MiB.",
                        default=d(config.azure_max_block_size))

    parser.add_argument(u"--azure-max-single-put-size", metavar=_(u"number"), type=int,
                        help=u"Largest supported upload size where the Azure library makes only one put call.\n"
                             u"Used to upload a single block if the content length is known and is less than this",
                        default=d(config.azure_max_single_put_size))

    parser.add_argument(u"--b2-hide-files", action=u"store_true",
                        help=u"Whether the B2 backend hides files instead of deleting them")

    parser.add_argument(u"--backend-retry-delay", type=int, metavar=_(u"seconds"),
                        help=u"Delay time before next try after a failure of a backend operation",
                        default=d(config.backend_retry_delay))

    parser.add_argument(u"--cf-backend", metavar=_(u"pyrax|cloudfiles"),
                        help=u"Allow the user to switch cloudfiles backend")

    parser.add_argument(u"--compare-data", action=u"store_true",
                        help=u"Compare data on verify not only signatures",
                        default=d(config.compare_data))

    parser.add_argument(u"--config-dir", type=check_file, metavar=_(u"path"),
                        help=u"Path to store configuration files",
                        default=d(config.archive_dir))

    parser.add_argument(u"--copy-links", action=u"store_true",
                        help=u"Copy contents of symlinks instead of linking",
                        default=d(config.copy_links))

    parser.add_argument(u"--dry-run", action=u"store_true",
                        help=u"Perform dry-run with no writes",
                        default=d(config.dry_run))

    parser.add_argument(u"--encrypt-key", metavar=_(u"gpg-key-id"), action=u"append",
                        help=u"GNUpg key for encryption/decryption",
                        default=d(None))

    # secret keyring in which the private encrypt key can be found
    parser.add_argument(u"--encrypt-secret-keyring", metavar=_(u"path"),
                        help=u"Path to secret GNUpg keyring",
                        default=d(None))

    parser.add_argument(u"--encrypt-sign-key", metavar=_(u"gpg-key-id"), action=u"append",
                        help=u"GNUpg key for signing",
                        default=d(None))

    parser.add_argument(u"--exclude", metavar=_(u"shell_pattern"), type=AddSelectionAction,
                        help=u"Exclude globbing pattern",
                        default=d(None))

    parser.add_argument(u"--exclude-device-files", action=u"store_true",
                        help=u"Exclude device files",
                        default=d(False))

    parser.add_argument(u"--exclude-filelist", metavar=_(u"filename"), type=AddFilelistAction,
                        help=u"File with list of file patters to exclude",
                        default=d(None))

    parser.add_argument(u"--exclude-if-present", metavar=_(u"filename"), type=AddSelectionAction,
                        help=u"Exclude directory if this file is present",
                        default=d(None))

    parser.add_argument(u"--exclude-older-than", metavar=_(u"time"), type=AddSelectionAction,
                        help=u"Exclude files older than time",
                        default=d(None))

    parser.add_argument(u"--exclude-other-filesystems", action=u"store_true",
                        help=u"Exclude other filesystems from backup",
                        default=d(False))

    parser.add_argument(u"--exclude-regexp", metavar=_(u"regex"), type=AddSelectionAction,
                        help=u"Exclude based on regex pattern",
                        default=d(None))

    parser.add_argument(u"--file-changed", type=check_file, metavar=_(u"path"),
                        help=u"Whether to collect only the file status, not the whole root",
                        default=d(None))

    parser.add_argument(u"--file-prefix", metavar="string", action=u"store",
                        help=u"String prefix for all duplicity files",
                        default=d(config.file_prefix))

    parser.add_argument(u"--file-prefix-archive", metavar="string", action=u"store",
                        help=u"String prefix for duplicity difftar files",
                        default=d(config.file_prefix_archive))

    parser.add_argument(u"--file-prefix-manifest", metavar="string", action=u"store",
                        help=u"String prefix for duplicity manifest files",
                        default=d(config.file_prefix_manifest))

    parser.add_argument(u"--file-prefix-signature", metavar="string", action=u"store",
                        help=u"String prefix for duplicity signature files",
                        default=d(config.file_prefix_signature))

    parser.add_argument(u"--force", action=u"store_true",
                        help=u"Force duplicity to actually delete during cleanup",
                        default=d(config.force))

    parser.add_argument(u"--ftp-passive", action=u"store_const", const=u"passive", dest=u"ftp_connection",
                        help=u"Tell FTP to use passive mode",
                        default=d(config.ftp_connection))

    parser.add_argument(u"--ftp-regular", action=u"store_const", const=u"regular", dest=u"ftp_connection",
                        help=u"Tell FTP to use regular mode",
                        default=d(config.ftp_connection))

    parser.add_argument(u"--full-if-older-than", metavar=_(u"time"), type=check_time, dest=u"restore_time",
                        help=u"Perform full backup if last full is older than 'time'",
                        default=d(config.restore_time))

    parser.add_argument(u"--gpg-binary", metavar=_(u"path"), type=check_file,
                        help=u"Path to GNUpg executable file",
                        default=d(config.gpg_binary))

    parser.add_argument(u"--gpg-options", metavar=_(u"options"), action=u"append",
                        help=u"Options to append to GNUpg invocation",
                        default=d(None))

    parser.add_argument(u"--hidden-encrypt-key", metavar=_(u"gpg-key-id"),
                        help=u"Hidden GNUpg encryption key",
                        default=d(None))

    parser.add_argument(u"--idr-fakeroot", metavar=_(u"path"), type=check_file,
                        help=u"Fake root for idrive backend",
                        default=d(config.idr_fakeroot))

    parser.add_argument(u"--ignore-errors", action=u"store_true",
                        help=u"Ignore most errors during restore",
                        default=d(False))

    parser.add_argument(u"--imap-full-address", action=u"store_true",
                        help=u"Whether to use the full email address as the user name",
                        default=d(config.imap_full_address))

    parser.add_argument(u"--imap-mailbox", metavar=_(u"imap_mailbox"),
                        help=u"Name of the imap folder to store backups",
                        default=d(config.imap_mailbox))

    parser.add_argument(u"--include", metavar=_(u"shell_pattern"), type=AddSelectionAction,
                        help=u"Exclude globbing pattern",
                        default=d(None))

    parser.add_argument(u"--include-filelist", metavar=_(u"filename"), type=AddFilelistAction,
                        help=u"File with list of file patters to include",
                        default=d(None))

    parser.add_argument(u"--include-regexp", metavar=_(u"regular_expression"), type=AddSelectionAction,
                        help=u"Exclude based on regex pattern",
                        default=d(None))

    parser.add_argument(u"--log-fd", metavar=_(u"file_descriptor"), type=set_log_fd,
                        help=u"Logging file descripto to use",
                        default=d(None))

    parser.add_argument(u"--log-file", metavar=_(u"log_filename"), type=set_log_file,
                        help=u"Logging filename to use",
                        default=d(None))

    parser.add_argument(u"--log-timestamp", action=u"store_true",
                        help=u"Whether to include timestamp and level in log",
                        default=d(False))

    parser.add_argument(u"--max-blocksize", metavar=_(u"number"), type=int,
                        help=u"Maximum block size for large files in MB",
                        default=d(None))

    parser.add_argument(u"--mf-purge", action=u"store_true",
                        help=u"Option for mediafire to purge files on delete instead of sending to trash",
                        default=d(False))

    parser.add_argument(u"--mp-segment-size", metavar=_(u"number"), type=set_mpsize,
                        help=u"Swift backend segment size",
                        default=d(config.mp_segment_size))

    parser.add_argument(u"--name", metavar=_(u"backup name"),
                        help=u"Custom backup name instead of hash",
                        default=d(config.backup_name))

    parser.add_argument(u"--no-compression", action=u"store_true",
                        help=u"If supplied do not perform compression")

    parser.add_argument(u"--no-encryption", action=u"store_true",
                        help=u"If supplied do not perform encryption",
                        default=d(False))

    parser.add_argument(u"--no-files-changed", action=u"store_true",
                        help=u"Whether to skip collecting the files_changed list in statistics",
                        default=d(False))

    parser.add_argument(u"--no-print-statistics", action=u"store_true",
                        help=u"If supplied do not print statistics",
                        default=d(False))

    parser.add_argument(u"--null-separator", action=u"store_true",
                        help=u"Whether to split on null instead of newline",
                        default=d(False))

    parser.add_argument(u"--num-retries", metavar=_(u"number"), type=int,
                        help=u"Number of retries on network operations",
                        default=d(config.num_retries))

    parser.add_argument(u"--numeric-owner", action=u"store_true",
                        help=u"Keeps number from tar file. Like same option in GNU tar.",
                        default=d(False))

    parser.add_argument(u"--do-not-restore-ownership", action=u"store_true",
                        help=u"Do no restore the uid/gid when finished, useful if you're restoring\n" 
                             U"data without having root privileges or Unix users support",
                        default=d(False))

    parser.add_argument(u"--metadata-sync-mode", choices=(u"full", u"partial"),
                        help=u"Only sync required metadata not all",
                        default=d(config.metadata_sync_mode))

    parser.add_argument(u"--par2-options", metavar=_(u"options"), action=u"append",
                        help=u"Verbatim par2 options.  May be supplied multiple times.",
                        default=d(None))

    parser.add_argument(u"--par2-redundancy", metavar=_(u"number"), type=int, choices=range(5, 99),
                        help=u"Level of Redundancy in percent for Par2 files",
                        default=d(config.par2_redundancy))

    parser.add_argument(u"--par2-volumes", metavar=_(u"number"), type=int,
                        help=u"Number of par2 volumes",
                        default=d(config.par2_volumes))

    parser.add_argument(u"--path-to-restore", u"-r", metavar=_(u"path"), type=check_file, dest=u"restore_path",
                        help=u"File or directory path to restore",
                        default=d(config.restore_path))

    parser.add_argument(u"--progress", action=u"store_true",
                        help=u"Display progress for the full and incremental backup operations")

    parser.add_argument(u"--progress-rate", metavar=_(u"number"), type=int,
                        help=u"Used to control the progress option update rate in seconds",
                        default=d(config.progress_rate))

    parser.add_argument(u"--rename", nargs=2, metavar="from to", type=AddRenameAction,
                        help=u"Rename files during restore",
                        default=d(config.rename))

    parser.add_argument(u"--restore-time", u"--time", u"-t", metavar=_(u"time"), type=check_time,
                        help=u"Restores will try to bring back the state as of the following time")

    parser.add_argument(u"--rsync-options", metavar=_(u"options"), action=u"append",
                        help=u"User added rsync options",
                        default=d(config.rsync_options))

    parser.add_argument(u"--s3-endpoint-url", metavar=_(u"s3_endpoint_url"), action=u"store",
                        help=u"Specity S3 endpoint",
                        default=d(config.s3_endpoint_url))

    parser.add_argument(u"--s3-european-buckets", action=u"store_true",
                        help=u"Whether to create European buckets",
                        default=d(config.s3_european_buckets))

    parser.add_argument(u"--s3-unencrypted-connection", action=u"store_true",
                        help=u"Whether to use plain HTTP (without SSL) to send data to S3",
                        default=d(config.s3_unencrypted_connection))

    parser.add_argument(u"--s3-use-deep-archive", action=u"store_true",
                        help=u"Whether to use S3 Glacier Deep Archive Storage",
                        default=d(config.s3_use_deep_archive))

    parser.add_argument(u"--s3-use-glacier", action=u"store_true",
                        help=u"Whether to use S3 Glacier Storage",
                        default=d(config.s3_use_glacier))

    parser.add_argument(u"--s3-use-glacier-ir", action=u"store_true",
                        help="Whether to use S3 Glacier IR Storage",
                        default=d(config.s3_use_glacier_ir))

    parser.add_argument(u"--s3-use-ia", action=u"store_true",
                        help=u"Whether to use S3 Infrequent Access Storage",
                        default=d(config.s3_use_ia))

    parser.add_argument(u"--s3-use-new-style", action=u"store_true",
                        help=u"Whether to use new-style subdomain addressing for S3 buckets. Such\n"
                             u"use is not backwards-compatible with upper-case buckets, or buckets\n"
                             u"that are otherwise not expressable in a valid hostname",
                        default=d(config.s3_use_new_style))

    parser.add_argument(u"--s3-use-onezone-ia", action=u"store_true",
                        help=u"Whether to use S3 One Zone Infrequent Access Storage",
                        default=d(config.s3_use_onezone_ia))

    parser.add_argument(u"--s3-use-rrs", action=u"store_true",
                        help=u"Whether to use S3 Reduced Redundancy Storage",
                        default=d(config.s3_use_rrs))

    parser.add_argument(u"--s3-multipart-chunk-size", metavar=_(u"number"), type=set_megs,
                        help=u"Chunk size used for S3 multipart uploads.The number of parallel uploads to\n"
                             u"S3 be given by chunk size / volume size. Use this to maximize the use of\n"
                             u"your bandwidth",
                        default=d(int(config.s3_multipart_chunk_size / (1024 * 1024))))

    parser.add_argument(u"--s3-multipart-max-procs", type=int, metavar=_(u"number"),
                        help=u"Number of processes to set the Processor Pool to when uploading multipart\n"
                             u"uploads to S3. Use this to control the maximum simultaneous uploads to S3",
                        default=d(config.s3_multipart_max_procs))

    parser.add_argument(u"--s3-multipart-max-timeout", metavar=_(u"number"), type=int,
                        help=u"Number of seconds to wait for each part of a multipart upload to S3. Use this\n"
                             u"to prevent hangups when doing a multipart upload to S3",
                        default=d(config.s3_multipart_max_timeout))

    parser.add_argument(u"--s3-use-multiprocessing", action=u"store_true",
                        help=u"Option to allow the s3/boto backend use the multiprocessing version",
                        default=d(config.s3_use_multiprocessing))

    parser.add_argument(u"--s3-use-server-side-encryption", action=u"store_true", dest=u"s3_use_sse",
                        help=u"Option to allow use of server side encryption in s3",
                        default=d(config.s3_use_sse))

    parser.add_argument(u"--s3-use-server-side-kms-encryption", action=u"store_true", dest=u"s3_use_sse_kms",
                        help=u"Allow use of server side KMS encryption",
                        default=d(config.s3_use_sse_kms))

    parser.add_argument(u"--s3-kms-key-id", metavar=_(u"s3_kms_key_id"), action=u"store",
                        help=u"S3 KMS encryption key id",
                        default=d(config.s3_kms_key_id))

    parser.add_argument(u"--s3-kms-grant", metavar=_(u"s3_kms_grant"), action=u"store",
                        help=u"S3 KMS grant value",
                        default=d(config.s3_kms_grant))

    parser.add_argument(u"--s3-region-name", metavar=_(u"s3_region_name"), action=u"store",
                        help=u"Specity S3 region name",
                        default=d(config.s3_region_name))

    parser.add_argument(u"--swift-storage-policy", metavar=_(u"policy"),
                        help=u"Option to specify a Swift container storage policy.",
                        default=d(config.swift_storage_policy))

    parser.add_argument(u"--scp-command", metavar=_(u"command"),
                        help=u"SCP command to use (ssh pexpect backend)",
                        default=d(config.scp_command))

    parser.add_argument(u"--sftp-command", metavar=_(u"command"),
                        help=u"SFTP command to use (ssh pexpect backend)",
                        default=d(config.sftp_command))

    parser.add_argument(u"--show-changes-in-set", type=int, metavar=_(u"number"),
                        help=u"Show file changes (new, deleted, changed) in the specified backup\n"
                             u"set (0 specifies latest, 1 specifies next latest, etc.)",
                        default=d(config.show_changes_in_set))

    parser.add_argument(u"--sign-key", type=set_sign_key, metavar=_(u"gpg-key-id"),
                        help=u"Sign key for encryption/decryption",
                        default=d(None))

    parser.add_argument(u"--ssh-askpass", action=u"store_true",
                        help=u"Ask the user for the SSH password. Not for batch usage",
                        default=d(config.ssh_askpass))

    parser.add_argument(u"--ssh-options", metavar=_(u"options"), action=u"append",
                        help=u"SSH options to add",
                        default=d(config.ssh_options))

    parser.add_argument(u"--ssl-cacert-file", metavar="file",
                        help=_(u"pem formatted bundle of certificate authorities"),
                        default=d(config.ssl_cacert_file))

    parser.add_argument(u"--ssl-cacert-path", metavar="path",
                        help=_(u"path to a folder with certificate authority files"),
                        default=d(config.ssl_cacert_path))

    parser.add_argument(u"--ssl-no-check-certificate", action=u"store_true",
                        help=u"Set to not validate SSL certificates",
                        default=d(config.ssl_no_check_certificate))

    parser.add_argument(u"--tempdir", metavar=_(u"path"), type=check_file, dest=u"temproot",
                        help=u"Working directory for temp files",
                        default=d(config.temproot))

    parser.add_argument(u"--timeout", metavar=_(u"seconds"), type=int,
                        help=u"Network timeout in seconds",
                        default=d(config.timeout))

    parser.add_argument(u"--time-separator", metavar=_(u"char"),
                        help=u"Character used like the ':' in time strings like\n"
                             u"2002-08-06T04:22:00-07:00",
                        default=d(config.time_separator))

    parser.add_argument(u"--use-agent", action=u"store_true",
                        help=u"Whether to specify --use-agent in GnuPG options")

    parser.add_argument(u"--verbosity", u"-v", metavar=_(u"[0-9]"), type=check_verbosity,
                        help=u"Logging verbosity",
                        default=d(log.NOTICE))

    parser.add_argument(u"--version", u"-V", action="version", version=u"%(prog) __version__",
                        help=u"Display version and exit")

    parser.add_argument(u"--volsize", metavar=_(u"number"), type=set_volsize,
                        help=u"Volume size to use in MiB",
                        default=d(int(config.volsize / (1024 * 1024))))

    parser.add_argument(u"--webdav-headers", metavar="string",
                        help=_(u"extra headers for Webdav, like 'Cookie,name=value'"),
                        default=d(config.webdav_headers))

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
    return args


def command_line_error(message):
    u"""Indicate a command line error and exit"""
    raise CommandLineError(_(f"Command line error: {message}\n") +
                           _(u"Enter 'duplicity --help' for help screen."),
                           log.ErrorCode.command_line)


def process_command_line(cmdline_list):
    u"""Process command line, set config, return action

    action will be "list-current", "collection-status", "cleanup",
    "remove-old", "restore", "verify", "full", or "inc".

    """
    # build initial gpg_profile
    config.gpg_profile = gpg.GPGProfile()

    # parse command line
    args = parse_cmdline_options(cmdline_list)

    # process first arg as possible command
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
    args = process_command_line(sys.argv[1:])
    print(args, argparse.Namespace)
