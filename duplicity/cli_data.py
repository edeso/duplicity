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

from dataclasses import dataclass

from duplicity.cli_util import *


@dataclass
class DuplicityCommands:
    u"""duplicity_commands and positional args expected"""
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

@dataclass
class CommandAliases:
    u"""commands and aliases"""
    backup = [u"back"]
    cleanup = [u"clean"]
    collection_status = [u"status"]
    full = []
    incremental = [u"inc"]
    list_current_files = [u"list"]
    remove_older_than = [u"remolder"]
    remove_all_but_n_full = [u"remfull"]
    remove_all_inc_of_but_n_full = [u"reminc"]
    restore = [u"rest"]
    verify = [u"ver"]

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

parent_options = {
    u"version",
}

backup_options = {
    u"allow_source_mismatch", u"asynchronous_upload", u"dry_run", u"time_separator", u"volsize",
}

selection_options = {
    u"exclude", u"exclude_device_files", u"exclude_filelist", u"exclude_if_present", u"exclude_older_than",
    u"exclude_other_filesystems", u"exclude_regexp", u"include", u"include_filelist", u"include_regexp",
}


@dataclass
class CommandOptions:
    u"""legal options by command"""
    backup = list(all_options - parent_options)
    cleanup = list(all_options - parent_options - backup_options - selection_options)
    collection_status = list(all_options - parent_options - backup_options - selection_options)
    full = list(all_options - parent_options)
    incremental = list(all_options - parent_options)
    list_current_files = list(all_options - parent_options - backup_options - selection_options)
    remove_older_than = list(all_options - parent_options - backup_options - selection_options)
    remove_all_but_n_full = list(all_options - parent_options - backup_options - selection_options)
    remove_all_inc_of_but_n_full = list(all_options - parent_options - backup_options - selection_options)
    restore = list(all_options - parent_options - backup_options - selection_options)
    verify = list(all_options - parent_options - backup_options - selection_options)


@dataclass
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
    u"restore_time": [u"t", u"time"],
    u"verbosity": [u"v"],
    u"version": [u"V"],
}


trans = {
    # TRANSL: Used in usage help to represent a Unix-style path name. Example:
    # rsync://user[:password]@other_host[:port]//absolute_path
    u'absolute_path': _(u"absolute_path"),

    # TRANSL: Used in usage help. Example:
    # tahoe://alias/some_dir
    u'alias': _(u"alias"),

    # TRANSL: Used in help to represent a "bucket name" for Amazon Web
    # Services' Simple Storage Service (S3). Example:
    # s3://other.host/bucket_name[/prefix]
    u'bucket_name': _(u"bucket_name"),

    # TRANSL: abbreviation for "character" (noun)
    u'char': _(u"char"),

    # TRANSL: noun
    u'command': _(u"command"),

    # TRANSL: Used in usage help to represent the name of a container in
    # Amazon Web Services' Cloudfront. Example:
    # cf+http://container_name
    u'container_name': _(u"container_name"),

    # TRANSL: noun
    u'count': _(u"count"),

    # TRANSL: Used in usage help to represent the name of a file directory
    u'directory': _(u"directory"),

    # TRANSL: Used in usage help to represent the name of a file. Example:
    # --log-file <filename>
    u'filename': _(u"filename"),

    # TRANSL: Used in usage help to represent an ID for a GnuPG key. Example:
    # --encrypt-key <gpg_key_id>
    u'gpg_key_id': _(u"gpg-key-id"),

    # TRANSL: Used in usage help, e.g. to represent the name of a code
    # module. Example:
    # rsync://user[:password]@other.host[:port]::/module/some_dir
    u'module': _(u"module"),

    # TRANSL: Used in usage help to represent a desired number of
    # something. Example:
    # --num-retries <number>
    u'number': _(u"number"),

    # TRANSL: Used in usage help. (Should be consistent with the "Options:"
    # header.) Example:
    # duplicity [full|incremental] [options] source_dir target_url
    u'options': _(u"options"),

    # TRANSL: Used in usage help to represent an internet hostname. Example:
    # ftp://user[:password]@other.host[:port]/some_dir
    u'other_host': _(u"other.host"),

    # TRANSL: Used in usage help. Example:
    # ftp://user[:password]@other.host[:port]/some_dir
    u'password': _(u"password"),

    # TRANSL: Used in usage help to represent a Unix-style path name. Example:
    # --archive-dir <path>
    u'path': _(u"path"),

    # TRANSL: Used in usage help to represent a TCP port number. Example:
    # ftp://user[:password]@other.host[:port]/some_dir
    u'port': _(u"port"),

    # TRANSL: Used in usage help. This represents a string to be used as a
    # prefix to names for backup files created by Duplicity. Example:
    # s3://other.host/bucket_name[/prefix]
    u'prefix': _(u"prefix"),

    # TRANSL: Used in usage help to represent a Unix-style path name. Example:
    # rsync://user[:password]@other.host[:port]/relative_path
    u'relative_path': _(u"relative_path"),

    # TRANSL: Used in usage help. Example:
    # --timeout <seconds>
    u'seconds': _(u"seconds"),

    # TRANSL: Used in usage help to represent a "glob" style pattern for
    # matching one or more files, as described in the documentation.
    # Example:
    # --exclude <shell_pattern>
    u'shell_pattern': _(u"shell_pattern"),

    # TRANSL: Used in usage help to represent the name of a single file
    # directory or a Unix-style path to a directory. Example:
    # file:///some_dir
    u'some_dir': _(u"some_dir"),

    # TRANSL: Used in usage help to represent the name of a single file
    # directory or a Unix-style path to a directory where files will be
    # coming FROM. Example:
    # duplicity [full|incremental] [options] source_dir target_url
    u'source_dir': _(u"source_dir"),

    # TRANSL: Used in usage help to represent a URL files will be coming
    # FROM. Example:
    # duplicity [restore] [options] source_url target_dir
    u'source_url': _(u"source_url"),

    # TRANSL: Used in usage help to represent the name of a single file
    # directory or a Unix-style path to a directory. where files will be
    # going TO. Example:
    # duplicity [restore] [options] source_url target_dir
    u'target_dir': _(u"target_dir"),

    # TRANSL: Used in usage help to represent a URL files will be going TO.
    # Example:
    # duplicity [full|incremental] [options] source_dir target_url
    u'target_url': _(u"target_url"),

    # TRANSL: Used in usage help to represent a time spec for a previous
    # point in time, as described in the documentation. Example:
    # duplicity remove-older-than time [options] target_url
    u'time': _(u"time"),

    # TRANSL: Used in usage help to represent a user name (i.e. login).
    # Example:
    # ftp://user[:password]@other.host[:port]/some_dir
    u'user': _(u"user"),

    # TRANSL: account id for b2. Example: b2://account_id@bucket/
    u'account_id': _(u"account_id"),

    # TRANSL: application_key for b2.
    # Example: b2://account_id:application_key@bucket/
    u'application_key': _(u"application_key"),

    # TRANSL: remote name for rclone.
    # Example: rclone://remote:/some_dir
    u'remote': _(u"remote"),
}
help_url_formats = _(u"Backends and their URL formats:") + u"""
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
