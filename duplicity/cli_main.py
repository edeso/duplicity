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
from dataclasses import dataclass
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


@dataclass(init=False)
class DuplicityCommands:
    u"""duplicity_commands and type of positional args expected"""
    backup = [u"url_or_dir", u"url_or_dir"]
    cleanup = [u"target_url"]
    collection_status = [u"target_url"]
    full = [u"source_dir", u"target_url"]
    incremental = [u"source_dir", u"target_url"]
    list_current_files = [u"target_url"]
    remove_older_than = [u"remove_time", u"target_url"]
    remove_all_but_n_full = [u"count", u"target_url"]
    remove_all_inc_of_but_n_full = [u"count", u"target_url"]
    restore = [u"source_url", u"target_dir"]
    verify = [u"source_url", u"target_dir"]


all_options = {
    u"allow_source_mismatch", u"archive_dir", u"asynchronous_upload", u"azure_blob_tier",
    u"azure_max_connections", u"azure_max_block_size", u"azure_max_single_put_size", u"b2_hide_files",
    u"backend_retry_delay", u"cf_backend", u"compare_data", u"config_dir", u"copy_links", u"dry_run",
    u"encrypt_key", u"encrypt_secret_keyring", u"encrypt_sign_key", u"exclude", u"exclude_device_files",
    u"exclude_filelist", u"exclude_if_present", u"exclude_older_than", u"exclude_other_filesystems",
    u"exclude_regexp", u"file_changed", u"file_prefix", u"file_prefix_archive", u"file_prefix_manifest",
    u"file_prefix_signature", u"force", u"ftp_passive", u"ftp_regular", u"full_if_older_than",
    u"gpg_binary", u"gpg_options", u"hidden_encrypt_key", u"idr_fakeroot", u"ignore_errors",
    u"imap_full_address", u"imap_mailbox", u"include", u"include_filelist", u"include_regexp", u"log_fd",
    u"log_file", u"log_timestamp", u"max_blocksize", u"mf_purge", u"mp_segment_size", u"name",
    u"no_compression", u"no_encryption", u"no_files_changed", u"no_print_statistics", u"null_separator",
    u"num_retries", u"numeric_owner", u"do_not_restore_ownership", u"metadata_sync_mode", u"par2_options",
    u"par2_redundancy", u"par2_volumes", u"path_to_restore", u"progress", u"progress_rate", u"rename",
    u"restore_time", u"rsync_options", u"s3_endpoint_url", u"s3_european_buckets",
    u"s3_unencrypted_connection", u"s3_use_deep_archive", u"s3_use_glacier", u"s3_use_glacier_ir",
    u"s3_use_ia", u"s3_use_new_style", u"s3_use_onezone_ia", u"s3_use_rrs", u"s3_multipart_chunk_size",
    u"s3_multipart_max_procs", u"s3_multipart_max_timeout", u"s3_use_multiprocessing",
    u"s3_use_server_side_encryption", u"s3_use_server_side_kms_encryption", u"s3_kms_key_id",
    u"s3_kms_grant", u"s3_region_name", u"swift_storage_policy", u"scp_command", u"sftp_command",
    u"show_changes_in_set", u"sign_key", u"ssh_askpass", u"ssh_options", u"ssl_cacert_file",
    u"ssl_cacert_path", u"ssl_no_check_certificate", u"tempdir", u"timeout", u"time_separator",
    u"use_agent", u"verbosity", u"version", u"volsize", u"webdav_headers", u"current_time",
    u"fail_on_volume", u"pydevd", u"skip_volume",
}

selection_options = {
    u"exclude", u"exclude_device_files", u"exclude_filelist", u"exclude_if_present", u"exclude_older_than",
    u"exclude_other_filesystems", u"exclude_regexp", u"include", u"include_filelist", u"include_regexp",
}


@dataclass(init=False)
class CommandOptions:
    u"""legal options by command"""
    backup = list(all_options)
    cleanup = list(all_options - selection_options)
    collection_status = list(all_options - selection_options)
    full = list(all_options)
    incremental = list(all_options)
    list_current_files = list(all_options - selection_options)
    remove_older_than = list(all_options - selection_options)
    remove_all_but_n_full = list(all_options - selection_options)
    remove_all_inc_of_but_n_full = list(all_options - selection_options)
    restore = list(all_options - selection_options)
    verify = list(all_options - selection_options)


@dataclass(init=False)
class OptionKwargs:
    u"""Option kwargs for add_argument"""
    allow_source_mismatch = {
        u"action": u"store_true",
        u"help": u"Allow different source directories",
        u"default": d(config.allow_source_mismatch)
    }
    archive_dir = {
        u"type": check_file,
        u"metavar": _(u"path"),
        u"help": u"Path to store metadata archives",
        u"default": d(config.archive_dir)
    }
    asynchronous_upload = {
        u"action": u"store_const",
        u"const": 1,
        u"dest": u"async_concurrency",
        u"help": u"Number of async upload tasks, max of 1",
        u"default": d(config.async_concurrency)
    }
    azure_blob_tier = {
        u"metavar": _(u"Hot|Cool|Archive"),
        u"help": u"Standard storage tier used for storing backup files (Hot|Cool|Archive)",
        u"default": d(config.azure_blob_tier)
    }
    azure_max_connections = {
        u"type": int,
        u"metavar": _(u"number"),
        u"help": u"Number of maximum parallel connections to use when the blob size exceeds 64MB",
        u"default": d(config.azure_max_connections)
    }
    azure_max_block_size = {
        u"metavar": _(u"number"),
        u"type": int,
        u"help": u"Number for the block size to upload a blob if the length is unknown\n"
                 u"or is larger than the value set by --azure-max-single-put-size\n"
                 u"The maximum block size the service supports is 100MiB.",
        u"default": d(config.azure_max_block_size)
    }
    azure_max_single_put_size = {
        u"metavar": _(u"number"),
        u"type": int,
        u"help": u"Largest supported upload size where the Azure library makes only one put call.\n"
                 u"Used to upload a single block if the content length is known and is less than this",
        u"default": d(config.azure_max_single_put_size)
    }
    b2_hide_files = {
        u"action": u"store_true",
        u"help": u"Whether the B2 backend hides files instead of deleting them",
        u"default": d(config.b2_hide_files)
    }
    backend_retry_delay = {
        u"metavar": _(u"seconds"),
        u"type": int,
        u"help": u"Delay time before next try after a failure of a backend operation",
        u"default": d(config.backend_retry_delay)
    }
    cf_backend = {
        u"metavar": u"pyrax|cloudfiles",
        u"help": u"Allow the user to switch cloudfiles backend",
        u"default": d(config.cf_backend)
    }
    compare_data = {
        u"action": u"store_true",
        u"help": u"Compare data on verify not only signatures",
        u"default": d(config.compare_data)
    }
    config_dir = {
        u"metavar": _(u"path"),
        u"type": check_file,
        u"help": u"Path to store configuration files",
        u"default": d(config.archive_dir)
    }
    copy_links = {
        u"action": u"store_true",
        u"help": u"Copy contents of symlinks instead of linking",
        u"default": d(config.copy_links)
    }
    dry_run = {
        u"action": u"store_true",
        u"help": u"Perform dry-run with no writes",
        u"default": d(config.dry_run)
    }
    encrypt_key = {
        u"metavar": _(u"gpg-key-id"),
        u"action": u"append",
        u"help": u"GNUpg key for encryption/decryption",
        u"default": d(None)
    }
    encrypt_secret_keyring = {
        u"metavar": _(u"path"),
        u"help": u"Path to secret GNUpg keyring",
        u"default": d(None)
    }
    encrypt_sign_key = {
        u"metavar": _(u"gpg-key-id"),
        u"action": u"append",
        u"help": u"GNUpg key for signing",
        u"default": d(None)
    }
    exclude = {
        u"metavar": _(u"shell_pattern"),
        u"action": AddSelectionAction,
        u"help": u"Exclude globbing pattern",
        u"default": d(None)
    }
    exclude_device_files = {
        u"action": u"store_true",
        u"help": u"Exclude device files",
        u"default": d(False)
    }
    exclude_filelist = {
        u"metavar": _(u"filename"),
        u"action": AddFilelistAction,
        u"help": u"File with list of file patters to exclude",
        u"default": d(None)
    }
    exclude_if_present = {
        u"metavar": _(u"filename"),
        u"action": AddSelectionAction,
        u"help": u"Exclude directory if this file is present",
        u"default": d(None)
    }
    exclude_older_than = {
        u"metavar": _(u"time"),
        u"action": AddSelectionAction,
        u"help": u"Exclude files older than time",
        u"default": d(None)
    }
    exclude_other_filesystems = {
        u"action": u"store_true",
        u"help": u"Exclude other filesystems from backup",
        u"default": d(False)
    }
    exclude_regexp = {
        u"metavar": _(u"regex"),
        u"action": AddSelectionAction,
        u"help": u"Exclude based on regex pattern",
        u"default": d(None)
    }
    file_changed = {
        u"type": check_file,
        u"metavar": _(u"path"),
        u"help": u"Whether to collect only the file status, not the whole root",
        u"default": d(None)
    }
    file_prefix = {
        u"metavar": "string",
        u"help": u"String prefix for all duplicity files",
        u"default": d(config.file_prefix)
    }
    file_prefix_archive = {
        u"metavar": "string",
        u"help": u"String prefix for duplicity difftar files",
        u"default": d(config.file_prefix_archive)
    }
    file_prefix_manifest = {
        u"metavar": "string",
        u"help": u"String prefix for duplicity manifest files",
        u"default": d(config.file_prefix_manifest)
    }
    file_prefix_signature = {
        u"metavar": "string",
        u"help": u"String prefix for duplicity signature files",
        u"default": d(config.file_prefix_signature)
    }
    force = {
        u"action": u"store_true",
        u"help": u"Force duplicity to actually delete during cleanup",
        u"default": d(config.force)
    }
    ftp_passive = {
        u"action": u"store_const",
        u"const": u"passive",
        u"dest": u"ftp_connection",
        u"help": u"Tell FTP to use passive mode",
        u"default": d(config.ftp_connection)
    }
    ftp_regular = {
        u"action": u"store_const",
        u"const": u"regular",
        u"dest": u"ftp_connection",
        u"help": u"Tell FTP to use regular mode",
        u"default": d(config.ftp_connection)
    }
    full_if_older_than = {
        u"metavar": _(u"time"),
        u"type": check_time,
        u"dest": u"restore_time",
        u"help": u"Perform full backup if last full is older than 'time'",
        u"default": d(config.restore_time)
    }
    gpg_binary = {
        u"metavar": _(u"path"), u"type": check_file,
        u"help": u"Path to GNUpg executable file",
        u"default": d(config.gpg_binary)
    }
    gpg_options = {
        u"metavar": _(u"options"), u"action": u"append",
        u"help": u"Options to append to GNUpg invocation",
        u"default": d(None)
    }
    hidden_encrypt_key = {
        u"metavar": _(u"gpg-key-id"),
        u"help": u"Hidden GNUpg encryption key",
        u"default": d(None)
    }
    idr_fakeroot = {
        u"metavar": _(u"path"), u"type": check_file,
        u"help": u"Fake root for idrive backend",
        u"default": d(config.idr_fakeroot)
    }
    ignore_errors = {
        u"action": u"store_true",
        u"help": u"Ignore most errors during restore",
        u"default": d(False)
    }
    imap_full_address = {
        u"action": u"store_true",
        u"help": u"Whether to use the full email address as the user name",
        u"default": d(config.imap_full_address)
    }
    imap_mailbox = {
        u"metavar": _(u"imap_mailbox"),
        u"help": u"Name of the imap folder to store backups",
        u"default": d(config.imap_mailbox)
    }
    include = {
        u"metavar": _(u"shell_pattern"), u"action": AddSelectionAction,
        u"help": u"Exclude globbing pattern",
        u"default": d(None)
    }
    include_filelist = {
        u"metavar": _(u"filename"), u"action": AddFilelistAction,
        u"help": u"File with list of file patters to include",
        u"default": d(None)
    }
    include_regexp = {
        u"metavar": _(u"regex"),
        u"action": AddSelectionAction,
        u"help": u"Exclude based on regex pattern",
        u"default": d(None)
    }
    log_fd = {
        u"metavar": _(u"file_descriptor"),
        u"type": set_log_fd,
        u"help": u"Logging file descripto to use",
        u"default": d(None)
    }
    log_file = {
        u"metavar": _(u"log_filename"),
        u"type": set_log_file,
        u"help": u"Logging filename to use",
        u"default": d(None)
    }
    log_timestamp = {
        u"action": u"store_true",
        u"help": u"Whether to include timestamp and level in log",
        u"default": d(False)
    }
    max_blocksize = {
        u"metavar": _(u"number"), u"type": int,
        u"help": u"Maximum block size for large files in MB",
        u"default": d(None)
    }
    mf_purge = {
        u"action": u"store_true",
        u"help": u"Option for mediafire to purge files on delete instead of sending to trash",
        u"default": d(False)
    }
    mp_segment_size = {
        u"metavar": _(u"number"),
        u"type": set_mpsize,
        u"help": u"Swift backend segment size",
        u"default": d(config.mp_segment_size)
    }
    name = {
        u"metavar": _(u"backup name"),
        u"help": u"Custom backup name instead of hash",
        u"default": d(config.backup_name)
    }
    no_compression = {
        u"action": u"store_true",
        u"help": u"If supplied do not perform compression",
        u"default": d(False)
    }
    no_encryption = {
        u"action": u"store_true",
        u"help": u"If supplied do not perform encryption",
        u"default": d(False)
    }
    no_files_changed = {
        u"action": u"store_true",
        u"help": u"Whether to skip collecting the files_changed list in statistics",
        u"default": d(False)
    }
    no_print_statistics = {
        u"action": u"store_true",
        u"help": u"If supplied do not print statistics",
        u"default": d(False)
    }
    null_separator = {
        u"action": u"store_true",
        u"help": u"Whether to split on null instead of newline",
        u"default": d(False)
    }
    num_retries = {
        u"metavar": _(u"number"), u"type": int,
        u"help": u"Number of retries on network operations",
        u"default": d(config.num_retries)
    }
    numeric_owner = {
        u"action": u"store_true",
        u"help": u"Keeps number from tar file. Like same option in GNU tar.",
        u"default": d(False)
    }
    do_not_restore_ownership = {
        u"action": u"store_true",
        u"help": u"Do no restore the uid/gid when finished, useful if you're restoring\n"
                 U"data without having root privileges or Unix users support",
        u"default": d(False)
    }
    metadata_sync_mode = {
        u"choices": (u"full", u"partial"),
        u"help": u"Only sync required metadata not all",
        u"default": d(config.metadata_sync_mode)
    }
    par2_options = {
        u"metavar": _(u"options"), u"action": u"append",
        u"help": u"Verbatim par2 options.  May be supplied multiple times.",
        u"default": d(None)
    }
    par2_redundancy = {
        u"metavar": _(u"number"),
        u"type": int,
        u"help": u"Level of Redundancy in percent for Par2 files",
        u"default": d(config.par2_redundancy)
    }
    par2_volumes = {
        u"metavar": _(u"number"), u"type": int,
        u"help": u"Number of par2 volumes",
        u"default": d(config.par2_volumes)
    }
    path_to_restore = {
        u"metavar": _(u"path"),
        u"type": check_file,
        u"dest": u"restore_path",
        u"help": u"File or directory path to restore",
        u"default": d(config.restore_path)
    }
    progress = {
        u"action": u"store_true",
        u"help": u"Display progress for the full and incremental backup operations",
        u"default": d(config.progress)
    }
    progress_rate = {
        u"metavar": _(u"number"), u"type": int,
        u"help": u"Used to control the progress option update rate in seconds",
        u"default": d(config.progress_rate)
    }
    rename = {
        u"metavar": u"from to",
        u"type": AddRenameAction,
        u"nargs": 2,
        u"help": u"Rename files during restore",
        u"default": d(config.rename)
    }
    restore_time = {
        u"metavar": _(u"time"),
        u"type": check_time,
        u"help": u"Restores will try to bring back the state as of the following time",
        u"default": d(config.restore_time)
    }
    rsync_options = {
        u"metavar": _(u"options"), u"action": u"append",
        u"help": u"User added rsync options",
        u"default": d(config.rsync_options)
    }
    s3_endpoint_url = {
        u"metavar": _(u"s3_endpoint_url"), u"action": u"store",
        u"help": u"Specity S3 endpoint",
        u"default": d(config.s3_endpoint_url)
    }
    s3_european_buckets = {
        u"action": u"store_true",
        u"help": u"Whether to create European buckets",
        u"default": d(config.s3_european_buckets)
    }
    s3_unencrypted_connection = {
        u"action": u"store_true",
        u"help": u"Whether to use plain HTTP (without SSL) to send data to S3",
        u"default": d(config.s3_unencrypted_connection)
    }
    s3_use_deep_archive = {
        u"action": u"store_true",
        u"help": u"Whether to use S3 Glacier Deep Archive Storage",
        u"default": d(config.s3_use_deep_archive)
    }
    s3_use_glacier = {
        u"action": u"store_true",
        u"help": u"Whether to use S3 Glacier Storage",
        u"default": d(config.s3_use_glacier)
    }
    s3_use_glacier_ir = {
        u"action": u"store_true",
        u"help": "Whether to use S3 Glacier IR Storage",
        u"default": d(config.s3_use_glacier_ir)
    }
    s3_use_ia = {
        u"action": u"store_true",
        u"help": u"Whether to use S3 Infrequent Access Storage",
        u"default": d(config.s3_use_ia)
    }
    s3_use_new_style = {
        u"action": u"store_true",
        u"help": u"Whether to use new-style subdomain addressing for S3 buckets. Such\n"
                 u"use is not backwards-compatible with upper-case buckets, or buckets\n"
                 u"that are otherwise not expressable in a valid hostname",
        u"default": d(config.s3_use_new_style)
    }
    s3_use_onezone_ia = {
        u"action": u"store_true",
        u"help": u"Whether to use S3 One Zone Infrequent Access Storage",
        u"default": d(config.s3_use_onezone_ia)
    }
    s3_use_rrs = {
        u"action": u"store_true",
        u"help": u"Whether to use S3 Reduced Redundancy Storage",
        u"default": d(config.s3_use_rrs)
    }
    s3_multipart_chunk_size = {
        u"metavar": _(u"number"), u"type": set_megs,
        u"help": u"Chunk size used for S3 multipart uploads.The number of parallel uploads to\n"
                 u"S3 be given by chunk size / volume size. Use this to maximize the use of\n"
                 u"your bandwidth",
        u"default": d(int(config.s3_multipart_chunk_size / (1024 * 1024)))
    }
    s3_multipart_max_procs = {
        u"type": int,
        u"metavar": _(u"number"),
        u"help": u"Number of processes to set the Processor Pool to when uploading multipart\n"
                 u"uploads to S3. Use this to control the maximum simultaneous uploads to S3",
        u"default": d(config.s3_multipart_max_procs)
    }
    s3_multipart_max_timeout = {
        u"metavar": _(u"number"),
        u"type": int,
        u"help": u"Number of seconds to wait for each part of a multipart upload to S3. Use this\n"
                 u"to prevent hangups when doing a multipart upload to S3",
        u"default": d(config.s3_multipart_max_timeout)
    }
    s3_use_multiprocessing = {
        u"action": u"store_true",
        u"help": u"Option to allow the s3/boto backend use the multiprocessing version",
        u"default": d(config.s3_use_multiprocessing)
    }
    s3_use_server_side_encryption = {
        u"action": u"store_true",
        u"dest": u"s3_use_sse",
        u"help": u"Option to allow use of server side encryption in s3",
        u"default": d(config.s3_use_sse)
    }
    s3_use_server_side_kms_encryption = {
        u"action": u"store_true",
        u"dest": u"s3_use_sse_kms",
        u"help": u"Allow use of server side KMS encryption",
        u"default": d(config.s3_use_sse_kms)
    }
    s3_kms_key_id = {
        u"metavar": _(u"s3_kms_key_id"), u"action": u"store",
        u"help": u"S3 KMS encryption key id",
        u"default": d(config.s3_kms_key_id)
    }
    s3_kms_grant = {
        u"metavar": _(u"s3_kms_grant"), u"action": u"store",
        u"help": u"S3 KMS grant value",
        u"default": d(config.s3_kms_grant)
    }
    s3_region_name = {
        u"metavar": _(u"s3_region_name"), u"action": u"store",
        u"help": u"Specity S3 region name",
        u"default": d(config.s3_region_name)
    }
    swift_storage_policy = {
        u"metavar": _(u"policy"),
        u"help": u"Option to specify a Swift container storage policy.",
        u"default": d(config.swift_storage_policy)
    }
    scp_command = {
        u"metavar": _(u"command"),
        u"help": u"SCP command to use (ssh pexpect backend)",
        u"default": d(config.scp_command)
    }
    sftp_command = {
        u"metavar": _(u"command"),
        u"help": u"SFTP command to use (ssh pexpect backend)",
        u"default": d(config.sftp_command)
    }
    show_changes_in_set = {
        u"metavar": _(u"number"),
        u"type": int,
        u"help": u"Show file changes (new, deleted, changed) in the specified backup\n"
                 u"set (0 specifies latest, 1 specifies next latest, etc.)",
        u"default": d(config.show_changes_in_set)
    }
    sign_key = {
        u"metavar": _(u"gpg-key-id"),
        u"type": set_sign_key,
        u"help": u"Sign key for encryption/decryption",
        u"default": d(None)
    }
    ssh_askpass = {
        u"action": u"store_true",
        u"help": u"Ask the user for the SSH password. Not for batch usage",
        u"default": d(config.ssh_askpass)
    }
    ssh_options = {
        u"metavar": _(u"options"),
        u"action": u"append",
        u"help": u"SSH options to add",
        u"default": d(config.ssh_options)
    }
    ssl_cacert_file = {
        u"metavar": "file",
        u"help": _(u"pem formatted bundle of certificate authorities"),
        u"default": d(config.ssl_cacert_file)
    }
    ssl_cacert_path = {
        u"metavar": "path",
        u"help": _(u"path to a folder with certificate authority files"),
        u"default": d(config.ssl_cacert_path)
    }
    ssl_no_check_certificate = {
        u"action": u"store_true",
        u"help": u"Set to not validate SSL certificates",
        u"default": d(config.ssl_no_check_certificate)
    }
    tempdir = {
        u"metavar": _(u"path"),
        u"type": check_file,
        u"dest": u"temproot",
        u"help": u"Working directory for temp files",
        u"default": d(config.temproot)
    }
    timeout = {
        u"metavar": _(u"seconds"),
        u"type": int,
        u"help": u"Network timeout in seconds",
        u"default": d(config.timeout)
    }
    time_separator = {
        u"metavar": _(u"char"),
        u"help": u"Character used like the ':' in time strings like\n"
                 u"2002-08-06T04:22:00-07:00",
        u"default": d(config.time_separator)
    }
    use_agent = {
        u"action": u"store_true",
        u"help": u"Whether to specify --use-agent in GnuPG options",
        u"default": d(config.use_agent)
    }
    verbosity = {
        u"metavar": _(u"[0-9]"), u"type": check_verbosity,
        u"help": u"Logging verbosity",
        u"default": d(log.NOTICE)
    }
    version = {
        u"action": "version",
        u"version": u"%(prog) __version__",
        u"help": u"Display version and exit",
    }
    volsize = {
        u"metavar": _(u"number"),
        u"type": set_volsize,
        u"help": u"Volume size to use in MiB",
        u"default": d(int(config.volsize / (1024 * 1024)))
    }
    webdav_headers = {
        u"metavar": "string",
        u"help": _(u"extra headers for Webdav, like 'Cookie,name: value'"),
        u"default": d(config.webdav_headers)
    }

    # TODO: Find a way to nuke these test options in production.
    # TESTING ONLY - set current time
    current_time = {
        u"type": int,
        u"help": argparse.SUPPRESS
    }
    # TESTING ONLY - raises exception after volume
    fail_on_volume = {
        u"type": int,
        u"help": argparse.SUPPRESS
    }
    # TESTING ONLY - trigger Pydev debugger
    pydevd = {
        u"action": u"store_true",
        u"help": argparse.SUPPRESS
    }
    # TESTING ONLY - skips upload for a given volume
    skip_volume = {
        u"type": int,
        u"help": argparse.SUPPRESS
    }


option_alternates = {
    u"path_to_restore": [u"r"],
    u"restore_time": [u"time", u"t"],
    u"verbosity": [u"v"],
    u"version": [u"V"],
}


class CommandLineError(errors.UserError):
    pass


def parse_cmdline_options(arglist):
    u"""
    Parse argument list
    """

    def make_wide(formatter, w=120, h=46):
        """
        Return a wider HelpFormatter, if possible.
        """
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
    subparsers = parser.add_subparsers(
        title=u"valid subcommands",
        required=False,
    )

    subparser_dict = dict()
    for subc, meta in DuplicityCommands.__dict__.items():
        if subc.startswith(u"__"):
            continue
        subc = var2cmd(subc)
        subparser_dict[subc] = subparsers.add_parser(subc, help=f"# duplicity {subc} {u' '.join(meta)}")
        subparser_dict[subc].add_argument(subc, action=u"store_true",
                                          default=d(getattr(config, cmd2var(subc))))
        for arg in meta:
            subparser_dict[subc].add_argument(arg, type=str)

    for option, kwargs in OptionKwargs.__dict__.items():
        if option.startswith(u"__"):
            continue
        names = [option] + (option_alternates.get(option, []))
        names = [var2opt(n) for n in names]
        parser.add_argument(*names, **kwargs)

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

    # # process first arg as possible command
    # if args:
    #     cmd = args.pop(0)
    #     # look for possible abbreviations
    #     possible = [c for c in duplicity_commands.keys() if c.startswith(cmd)]
    #     # no unique match, that's an error
    #     if len(possible) > 1:
    #         command_line_error(f"command '{cmd}' not unique: could be {' or '.join(possible)}")
    #     # only one match, that's a keeper, maybe
    #     elif len(possible) == 1:
    #         cmd = possible[0]
    #         if cmd not in duplicity_commands.keys():
    #             command_line_error(f"command '{cmd}' is not a duplicity command.")
    #     # no matches, assume implied cmd
    #     elif not possible:
    #         args.insert(0, cmd)
    #         cmd = u"implied"
    #         duplicity_commands[cmd] = [u"defer", u"defer"]
    #
    # # duplicity_commands just need standard checks
    # cmdvar = cmd.replace(u'-', u'_')
    # setattr(config, cmdvar, args)
    # num_expect = len(duplicity_commands[cmd])
    # if len(args) != num_expect:
    #     command_line_error(f"Expected {num_expect} args, got {len(args)}.")
    #
    # targets = duplicity_commands[cmd]
    # for n in range(len(targets)):
    #     if targets[n] != u"defer":
    #         name = f"check_{targets[n]}"
    #         func = getattr(cli_main, name)
    #         setattr(config, targets[n], func(args[n]))
    #
    # # other duplicity_commands need added processing
    # if cmd == u"remove-all-but-n-full":
    #     config.remove_all_but_n_full_mode = True
    #     arg = args[0]
    #     config.keep_chains = int(arg)
    #     if not config.keep_chains > 0:
    #         command_line_error(cmd + u" count must be > 0")
    #
    # elif cmd == u"remove-all-inc-of-but-n-full":
    #     config.remove_all_inc_of_but_n_full_mode = True
    #     arg = args[0]
    #     config.keep_chains = int(arg)
    #     if not config.keep_chains > 0:
    #         command_line_error(cmd + u" count must be > 0")
    #
    # backend_url = config.target_url or config.source_url
    # if config.backup_name is None:
    #     config.backup_name = generate_default_backup_name(backend_url)
    #
    # # convert file_prefix* string
    # if isinstance(config.file_prefix, str):
    #     config.file_prefix = bytes(config.file_prefix, u'utf-8')
    # if isinstance(config.file_prefix_manifest, str):
    #     config.file_prefix_manifest = bytes(config.file_prefix_manifest, u'utf-8')
    # if isinstance(config.file_prefix_archive, str):
    #     config.file_prefix_archive = bytes(config.file_prefix_archive, u'utf-8')
    # if isinstance(config.file_prefix_signature, str):
    #     config.file_prefix_signature = bytes(config.file_prefix_signature, u'utf-8')
    #
    # # set and expand archive dir
    # set_archive_dir(expand_archive_dir(config.archive_dir,
    #                                    config.backup_name))
    #
    # log.Info(_(u"Using archive dir: %s") % (config.archive_dir_path.uc_name,))
    # log.Info(_(u"Using backup name: %s") % (config.backup_name,))
    #
    # # if we get a different gpg-binary from the commandline then redo gpg_profile
    # if config.gpg_binary is not None:
    #     src = config.gpg_profile
    #     config.gpg_profile = gpg.GPGProfile(
    #         passphrase=src.passphrase,
    #         sign_key=src.sign_key,
    #         recipients=src.recipients,
    #         hidden_recipients=src.hidden_recipients)
    # log.Debug(_(u"GPG binary is %s, version %s") %
    #           ((config.gpg_binary or u'gpg'), config.gpg_profile.gpg_version))
    #
    # # we can now try to import all the backends
    # backend.import_backends()
    #
    # # parse_cmdline_options already verified that we got exactly 1 or 2
    # # positional arguments.  Convert to action
    # if len(args) == 1:
    #     if list_current:
    #         action = u"list-current"
    #     elif collection_status:
    #         action = u"collection-status"
    #     elif cleanup:
    #         action = u"cleanup"
    #     elif config.remove_time is not None:
    #         action = u"remove-old"
    #     elif config.remove_all_but_n_full_mode:
    #         action = u"remove-all-but-n-full"
    #     elif config.remove_all_inc_of_but_n_full_mode:
    #         action = u"remove-all-inc-of-but-n-full"
    #     else:
    #         command_line_error(u"Too few arguments")
    #
    #     config.backend = backend.get_backend(args[0])
    #     if not config.backend:
    #         command_line_error(_(f"Bad URL '{args[0]})'.\n"
    #                              "Examples of URL strings are 'scp://user@host.net:1234/path' and\n"
    #                              "'file:///usr/local'.  See the man page for more information."""))
    # elif len(args) == 2:
    #     # Figure out whether backup or restore
    #     backup, local_pathname = set_backend(args[0], args[1])
    #     if backup:
    #         if full_backup:
    #             action = u"full"
    #         else:
    #             action = u"inc"
    #     else:
    #         if verify:
    #             action = u"verify"
    #         else:
    #             action = u"restore"
    #
    #     process_local_dir(action, local_pathname)
    #     if action in [u'full', u'inc', u'verify']:
    #         set_selection()
    #
    # check_consistency(action)
    #
    # log.Info(_(u"Main action: ") + action)
    return action


if __name__ == u"__main__":
    log.setup()
    args = process_command_line(sys.argv[1:])
    print(args, argparse.Namespace)
