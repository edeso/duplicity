# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
# Copyright 2019 Carl A. Adams <carlalex@overlords.com>
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

import duplicity.backend
from duplicity import (
    config,
    file_naming,
    log,
    log_util,
    progress,
)
from duplicity.errors import (
    BackendException,
    FatalBackendException,
)


# Note: current gaps with the old boto backend include:
#       - Glacier restore to S3 not implemented. Should this
#         be done here? Or is that out of scope. My current opinion
#         is that it is out of scope, and the manpage reflects this.
#         It can take days, so waiting seems like it's not ideal.
#         "Thaw" isn't currently a generic concept that the core asks
#         of back-ends. Perhaps that is worth exploring.  The older
#         boto backend appeared  to attempt this restore in the code,
#         but the man page indicated that restores should be done out
#         of band. If implemented,  We should add the the following
#         new features:
#              - when restoring from glacier or deep archive, specify TTL.
#              - allow user to specify how fast to restore (impacts cost).


class S3Boto3Backend(duplicity.backend.Backend):
    """
    Backend for Amazon's Simple Storage System, (aka Amazon S3), though
    the use of the boto3 module. (See
    https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
    for information on boto3.)

    Pursuant to Amazon's announced deprecation of path style S3 access,
    this backend only supports virtual host style bucket URIs.
    See the man page for full details.

    To make use of this backend, you must provide AWS credentials.
    This may be done in several ways: through the environment variables
    AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY, by the
    ~/.aws/credentials file, by the ~/.aws/config file,
    or by using the boto2 style ~/.boto or /etc/boto.cfg files.
    """

    def __init__(self, parsed_url):
        duplicity.backend.Backend.__init__(self, parsed_url)

        # This folds the null prefix and all null parts, which means that:
        #  //MyBucket/ and //MyBucket are equivalent.
        #  //MyBucket//My///My/Prefix/ and //MyBucket/My/Prefix are equivalent.
        url_path_parts = [x for x in parsed_url.path.split("/") if x != ""]
        if url_path_parts:
            self.bucket_name = url_path_parts.pop(0)
        else:
            raise BackendException("S3 requires a bucket name.")

        if url_path_parts:
            self.key_prefix = f"{'/'.join(url_path_parts)}/"
        else:
            self.key_prefix = ""

        self.parsed_url = parsed_url
        self.straight_url = duplicity.backend.strip_auth_from_url(parsed_url)
        self.s3 = None
        self.bucket = None
        self.tracker = UploadProgressTracker()

    def reset_connection(self):
        import boto3
        import botocore
        from botocore.exceptions import ClientError

        self.bucket = None
        self.s3 = boto3.resource(
            "s3",
            region_name=config.s3_region_name,
            use_ssl=(not config.s3_unencrypted_connection),
            endpoint_url=config.s3_endpoint_url,
        )

        try:
            self.s3.meta.client.head_bucket(Bucket=self.bucket_name)
        except botocore.exceptions.ClientError as bce:
            error_code = bce.response["Error"]["Code"]
            if error_code == "404":
                raise FatalBackendException(
                    f'S3 bucket "{self.bucket_name}" does not exist',
                    code=log.ErrorCode.backend_not_found,
                )
            else:
                raise

        self.bucket = self.s3.Bucket(self.bucket_name)  # only set if bucket is thought to exist.

    def _put(self, local_source_path, remote_filename):
        from boto3.s3.transfer import TransferConfig

        if not self.s3:
            self.reset_connection()

        # files that should not in glacier and deep_archive, to allow smooth operation
        glacier_exceptions = [
            file_naming.full_manifest_re,
            file_naming.inc_manifest_re,
            file_naming.full_sig_re,
            file_naming.new_sig_re,
        ]

        def is_glacier_exception(filename):
            return any([x.match(filename) for x in glacier_exceptions])

        if config.s3_use_rrs:
            storage_class = "REDUCED_REDUNDANCY"
        elif config.s3_use_ia:
            storage_class = "STANDARD_IA"
        elif config.s3_use_onezone_ia:
            storage_class = "ONEZONE_IA"
        elif config.s3_use_glacier and not is_glacier_exception(remote_filename):
            storage_class = "GLACIER"
        elif config.s3_use_glacier_ir and not is_glacier_exception(remote_filename):
            storage_class = "GLACIER_IR"
        elif config.s3_use_deep_archive and not is_glacier_exception(remote_filename):
            storage_class = "DEEP_ARCHIVE"
        else:
            storage_class = "STANDARD"
        extra_args = {"StorageClass": storage_class}

        if config.s3_use_sse:
            extra_args["ServerSideEncryption"] = "AES256"
        elif config.s3_use_sse_kms:
            if config.s3_kms_key_id is None:
                raise FatalBackendException(
                    "S3 USE SSE KMS was requested, but key id not provided " "require (--s3-kms-key-id)",
                    code=log.ErrorCode.s3_kms_no_id,
                )
            extra_args["ServerSideEncryption"] = "aws:kms"
            extra_args["SSEKMSKeyId"] = config.s3_kms_key_id
            if config.s3_kms_grant:
                extra_args["GrantFullControl"] = config.s3_kms_grant

        transfer_config = TransferConfig(
            multipart_chunksize=config.s3_multipart_chunk_size,
            multipart_threshold=config.s3_multipart_chunk_size,
            max_concurrency=config.s3_multipart_max_procs,
        )

        # Should the tracker be scoped to the put or the backend?
        # The put seems right to me, but the results look a little more correct
        # scoped to the backend.  This brings up questions about knowing when
        # it's proper for it to be reset.
        # tracker = UploadProgressTracker() # Scope the tracker to the put()
        tracker = self.tracker

        remote_filename = os.fsdecode(remote_filename)
        key = self.key_prefix + remote_filename

        log.Info(f"Uploading {self.straight_url}/{remote_filename} to {storage_class} Storage")
        self.s3.Object(self.bucket.name, key).upload_file(
            local_source_path.uc_name,
            Callback=tracker.progress_cb,
            Config=transfer_config,
            ExtraArgs=extra_args,
        )

    def _get(self, remote_filename, local_path):
        from botocore.exceptions import ClientError

        if not self.s3:
            self.reset_connection()

        remote_filename = os.fsdecode(remote_filename)
        key = self.key_prefix + remote_filename
        try:
            self.s3.Object(self.bucket.name, key).download_file(local_path.uc_name)
        except ClientError as ios:
            if ios.response["Error"]["Code"] == "InvalidObjectState":
                log_util.FatalError(
                    f"File {remote_filename} seems to be in a long term storage, "
                    f"please use AWS Console/API to initiate restore.\nAPI-Error: {ios}"
                )
            else:
                raise ios

    def _list(self):
        if not self.s3:
            self.reset_connection()

        filename_list = []
        for obj in self.bucket.objects.filter(Prefix=self.key_prefix):
            try:
                filename = obj.key.replace(self.key_prefix, "", 1)
                filename_list.append(os.fsencode(filename))
                log.Debug(f"Listed {self.straight_url}/{filename}")
            except AttributeError:
                pass
        return filename_list

    def _delete(self, remote_filename):
        if not self.s3:
            self.reset_connection()

        remote_filename = os.fsdecode(remote_filename)
        key = self.key_prefix + remote_filename
        self.s3.Object(self.bucket.name, key).delete()

    def _query(self, remote_filename):
        if not self.s3:
            self.reset_connection()

        import botocore

        remote_filename = os.fsdecode(remote_filename)
        key = self.key_prefix + remote_filename
        content_length = -1
        try:
            s3_obj = self.s3.Object(self.bucket.name, key)
            s3_obj.load()
            content_length = s3_obj.content_length
        except botocore.exceptions.ClientError as bce:
            if bce.response["Error"]["Code"] == "404":
                pass
            else:
                raise
        return {"size": content_length}


class UploadProgressTracker(object):
    def __init__(self):
        self.total_bytes = 0

    def progress_cb(self, fresh_byte_count):
        self.total_bytes += fresh_byte_count
        progress.report_transfer(self.total_bytes, 0)  # second arg appears to be unused
        # It would seem to me that summing progress should be the callers job,
        # and backends should just toss bytes written numbers over the fence.
        # But, the progress bar doesn't work in a reasonable way when we do
        # that. (This would also eliminate the need for this class to hold
        # the scoped rolling total.)
        # progress.report_transfer(fresh_byte_count, 0)


duplicity.backend.register_backend("boto3+s3", S3Boto3Backend)
# make boto3 the default s3 backend
duplicity.backend.register_backend("s3", S3Boto3Backend)
