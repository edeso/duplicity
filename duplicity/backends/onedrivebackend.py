# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
# vim:tabstop=4:shiftwidth=4:expandtab
#
# Copyright 2014 Google Inc.
# Contact Michael Stapelberg <stapelberg+duplicity@google.com>
# This is NOT a Google product.
# Revised for Microsoft Graph API 2019 by David Martin
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


import json
import os
import sys
import time

import duplicity.backend
from duplicity import config
from duplicity import log
from duplicity.errors import BackendException


# For documentation on the API, see
# The previous Live SDK API required the use of opaque folder IDs to navigate paths, but the Microsoft Graph
# API allows the use of parent/child/grandchild pathnames.
# Old Live SDK API: https://docs.microsoft.com/en-us/previous-versions/office/developer/onedrive-live-sdk/dn659731(v%3doffice.15)  # noqa
# Files API: https://docs.microsoft.com/en-us/graph/api/resources/onedrive?view=graph-rest-1.0
# Large file upload API: https://docs.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_createuploadsession?view=odsp-graph-online  # noqa


class OneDriveBackend(duplicity.backend.Backend):
    """Uses Microsoft OneDrive (formerly SkyDrive) for backups."""

    API_URI = 'https://graph.microsoft.com/v1.0/'
    # The large file upload API says that uploaded chunks (except the last) must be multiples of 327680 bytes.
    REQUIRED_FRAGMENT_SIZE_MULTIPLE = 327680

    def __init__(self, parsed_url):
        duplicity.backend.Backend.__init__(self, parsed_url)

        self.directory = parsed_url.path.lstrip('/')
        onedrive_root = os.environ.get('ONEDRIVE_ROOT', 'me/drive/root')
        self.directory_onedrive_path = '%s:/%s/' % (onedrive_root, self.directory)
        if self.directory == "":
            raise BackendException((
                'You did not specify a path. '
                'Please specify a path, e.g. onedrive://duplicity_backups'))

        if config.volsize > (10 * 1024 * 1024 * 1024):
            raise BackendException((
                'Your --volsize is bigger than 10 GiB, which is the maximum '
                'file size on OneDrive.'))

        self.initialize_oauth2_session()

    def initialize_oauth2_session(self):
        client_id = os.environ.get('OAUTH2_CLIENT_ID')
        refresh_token = os.environ.get('OAUTH2_REFRESH_TOKEN')
        if client_id and refresh_token:
            self.http_client = ExternalOAuth2Session(client_id, refresh_token)
        else:
            self.http_client = DefaultOAuth2Session(self.API_URI)

    def _list(self):
        accum = []
        # Strip last slash, because graph can give a 404 in some cases with it
        next_url = self.API_URI + self.directory_onedrive_path.rstrip('/') + ':/children'
        while True:
            response = self.http_client.get(next_url)
            if response.status_code == 404:
                # No further files here
                break
            response.raise_for_status()
            responseJson = response.json()
            if 'value' not in responseJson:
                raise BackendException((
                    'Malformed JSON: expected "value" member in %s' % (
                        responseJson)))
            accum += responseJson['value']
            if '@odata.nextLink' in responseJson:
                next_url = responseJson['@odata.nextLink']
            else:
                break

        return [x['name'] for x in accum]

    def _get(self, remote_filename, local_path):
        remote_filename = remote_filename.decode("UTF-8")
        with local_path.open('wb') as f:
            response = self.http_client.get(
                self.API_URI + self.directory_onedrive_path + remote_filename + ':/content', stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    f.write(chunk)
            f.flush()

    def _put(self, source_path, remote_filename):
        # Happily, the OneDrive API will lazily create the folder hierarchy required to contain a pathname

        # Check if the user has enough space available on OneDrive before even
        # attempting to upload the file.
        remote_filename = remote_filename.decode("UTF-8")
        source_size = os.path.getsize(source_path.name)
        start = time.time()
        response = self.http_client.get(self.API_URI + 'me/drive?$select=quota')
        response.raise_for_status()
        if ('quota' in response.json()):
            available = response.json()['quota'].get('remaining', None)
            if available:
                log.Debug('Bytes available: %d' % available)
                if source_size > available:
                    raise BackendException((
                        'Out of space: trying to store "%s" (%d bytes), but only '
                        '%d bytes available on OneDrive.' % (
                            source_path.name, source_size,
                            available)))
        log.Debug("Checked quota in %fs" % (time.time() - start))

        with source_path.open() as source_file:
            start = time.time()
            url = self.API_URI + self.directory_onedrive_path + remote_filename + ':/createUploadSession'

            response = self.http_client.post(url)
            response.raise_for_status()
            response_json = json.loads(response.content.decode("UTF-8"))
            if 'uploadUrl' not in response_json:
                raise BackendException((
                    'File "%s" cannot be uploaded: could not create upload session: %s' % (
                        remote_filename, response.content)))
            uploadUrl = response_json['uploadUrl']

            # https://docs.microsoft.com/en-us/onedrive/developer/rest-api/api/driveitem_createuploadsession?
            # indicates 10 MiB is optimal for stable high speed connections.
            offset = 0
            desired_num_fragments = 10 * 1024 * 1024 // self.REQUIRED_FRAGMENT_SIZE_MULTIPLE
            while True:
                chunk = source_file.read(desired_num_fragments * self.REQUIRED_FRAGMENT_SIZE_MULTIPLE)
                if len(chunk) == 0:
                    break
                headers = {
                    'Content-Length': '%d' % (len(chunk)),
                    'Content-Range': 'bytes %d-%d/%d' % (offset, offset + len(chunk) - 1, source_size),
                }
                log.Debug('PUT %s %s' % (remote_filename, headers['Content-Range']))
                response = self.http_client.put(
                    uploadUrl,
                    headers=headers,
                    data=chunk)
                response.raise_for_status()
                offset += len(chunk)

            log.Debug("PUT file in %fs" % (time.time() - start))

    def _delete(self, remote_filename):
        remote_filename = remote_filename.decode("UTF-8")
        response = self.http_client.delete(self.API_URI + self.directory_onedrive_path + remote_filename)
        if response.status_code == 404:
            raise BackendException((
                'File "%s" cannot be deleted: it does not exist' % (
                    remote_filename)))
        response.raise_for_status()

    def _query(self, remote_filename):
        remote_filename = remote_filename.decode("UTF-8")
        response = self.http_client.get(self.API_URI + self.directory_onedrive_path + remote_filename)
        if response.status_code != 200:
            return {'size': -1}
        if 'size' not in response.json():
            raise BackendException((
                'Malformed JSON: expected "size" member in %s' % (
                    response.json())))
        return {'size': response.json()['size']}

    def _retry_cleanup(self):
        self.initialize_oauth2_session()


class OneDriveOAuth2Session(object):
    """A tiny wrapper for OAuth2Session that handles some OneDrive details."""

    OAUTH_TOKEN_URI = 'https://login.live.com/oauth20_token.srf'

    def __init__(self):
        # OAUTHLIB_RELAX_TOKEN_SCOPE prevents the oauthlib from complaining
        # about a mismatch between the requested scope and the delivered scope.
        # We need this because we don't get a refresh token without asking for
        # offline_access, but Microsoft Graph doesn't include offline_access
        # in its response (even though it does send a refresh_token).
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = 'TRUE'

        # Import requests-oauthlib
        try:
            # On debian (and derivatives), get these dependencies using:
            # apt-get install python-requests-oauthlib
            # On fedora (and derivatives), get these dependencies using:
            # yum install python-requests-oauthlib
            from requests_oauthlib import OAuth2Session
            self.session_class = OAuth2Session
        except ImportError as e:
            raise BackendException((
                'OneDrive backend requires python-requests-oauthlib to be '
                'installed. Please install it and try again.\n' + str(e)))

        # Should be filled by a subclass
        self.session = None

    def get(self, *args, **kwargs):
        return self.session.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.session.put(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.session.post(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.session.delete(*args, **kwargs)


class DefaultOAuth2Session(OneDriveOAuth2Session):
    """A possibly-interactive console session using a built-in API key"""

    OAUTH_TOKEN_PATH = os.path.expanduser(
        '~/.duplicity_onedrive_oauthtoken.json')
    CLIENT_ID = '000000004C12E85D'
    OAUTH_AUTHORIZE_URI = 'https://login.live.com/oauth20_authorize.srf'
    OAUTH_REDIRECT_URI = 'https://login.live.com/oauth20_desktop.srf'
    # Files.Read is for reading files,
    # Files.ReadWrite  is for creating/writing files,
    # User.Read is needed for the /me request to see if the token works.
    # offline_access is necessary for duplicity to access onedrive without
    # the user being logged in right now.
    OAUTH_SCOPE = ['Files.Read', 'Files.ReadWrite', 'User.Read', 'offline_access']

    def __init__(self, api_uri):
        super(DefaultOAuth2Session, self).__init__()

        token = None
        try:
            with open(self.OAUTH_TOKEN_PATH) as f:
                token = json.load(f)
        except IOError as e:
            log.Error(('Could not load OAuth2 token. '
                       'Trying to create a new one. (original error: %s)' % e))

        self.session = self.session_class(
            self.CLIENT_ID,
            scope=self.OAUTH_SCOPE,
            redirect_uri=self.OAUTH_REDIRECT_URI,
            token=token,
            auto_refresh_kwargs={
                'client_id': self.CLIENT_ID,
            },
            auto_refresh_url=self.OAUTH_TOKEN_URI,
            token_updater=self.token_updater)

        # We have to refresh token manually because it's not working "under the covers"
        if token is not None:
            self.session.refresh_token(self.OAUTH_TOKEN_URI)

        # Send a request to make sure the token is valid (or could at least be
        # refreshed successfully, which will happen under the covers). In case
        # this request fails, the provided token was too old (i.e. expired),
        # and we need to get a new token.
        user_info_response = self.session.get(api_uri + 'me')
        if user_info_response.status_code != 200:
            token = None

        if token is None:
            if not sys.stdout.isatty() or not sys.stdin.isatty():
                log.FatalError(('The OAuth2 token could not be loaded from %s '
                                'and you are not running duplicity '
                                'interactively, so duplicity cannot possibly '
                                'access OneDrive.' % self.OAUTH_TOKEN_PATH))
            authorization_url, state = self.session.authorization_url(
                self.OAUTH_AUTHORIZE_URI, display='touch')

            print()
            print('In order to authorize duplicity to access your OneDrive, '
                  'please open %s in a browser and copy the URL of the blank '
                  'page the dialog leads to.' % authorization_url)
            print()

            redirected_to = input('URL of the blank page: ').strip()

            token = self.session.fetch_token(
                self.OAUTH_TOKEN_URI,
                authorization_response=redirected_to)

            user_info_response = self.session.get(api_uri + 'me')
            user_info_response.raise_for_status()

            try:
                with open(self.OAUTH_TOKEN_PATH, 'w') as f:
                    json.dump(token, f)
            except Exception as e:
                log.Error(('Could not save the OAuth2 token to %s. '
                           'This means you need to do the OAuth2 authorization '
                           'process on every start of duplicity. '
                           'Original error: %s' % (
                               self.OAUTH_TOKEN_PATH, e)))

    def token_updater(self, token):
        try:
            with open(self.OAUTH_TOKEN_PATH, 'w') as f:
                json.dump(token, f)
        except Exception as e:
            log.Error(('Could not save the OAuth2 token to %s. '
                       'This means you may need to do the OAuth2 '
                       'authorization process again soon. '
                       'Original error: %s' % (
                           self.OAUTH_TOKEN_PATH, e)))


class ExternalOAuth2Session(OneDriveOAuth2Session):
    """Caller is managing tokens and provides an active refresh token."""
    def __init__(self, client_id, refresh_token):
        super(ExternalOAuth2Session, self).__init__()

        token = {
            'refresh_token': refresh_token,
        }

        self.session = self.session_class(
            client_id,
            token=token,
            auto_refresh_kwargs={
                'client_id': client_id,
            },
            auto_refresh_url=self.OAUTH_TOKEN_URI)

        # Get an initial refresh under our belts, since we don't have an access
        # token to start with.
        self.session.refresh_token(self.OAUTH_TOKEN_URI)


duplicity.backend.register_backend('onedrive', OneDriveBackend)
