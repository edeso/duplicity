# Copyright 2021 Syeam Bin Abdullah <syeamtechdemon@gmail.com>
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

from builtins import str
import os
import requests
import json
import urllib.request


import duplicity.backend
from duplicity import config
from duplicity import log
from duplicity.errors import BackendException

# TODO: ADD VERIFY PARAMETER FOR SSL


class SlateBackend(duplicity.backend.Backend):
    u"""
    Backend for Slate
    """
    def __init__(self, slatename):
        duplicity.backend.Backend.__init__(self, slatename)

        self.key = key
        data = json.dumps({ 'data': {'private': 'true'}})
        headers = {
          'Content-Type': 'application/json', 
          'Authorization': 'Basic ' + self.key
          }

        response = requests.post('https://slate.host/api/v1/get', data=data, headers=headers, verify=False) 
        if not response.ok:
          raise BackendException(u"Slate backend requires a valid API key")
        
        r = response.json()
        if len(r['slates']) < 1: 
          raise BackendException(u"No valid slates found, please create a slate to upload files")
        
        slates = [slate['data']['name']:slate for slate in r['slates']]
        slatenames = slates.keys()
        
        if slatename not in slatenames:
          raise BackendException(u"The chosen slate does not exist")

        self.slate = slate[slatename]
        self.id = slate['id']

        log.Info('Loaded slate\nname: %s\uuid: %s\nas: %s'%(slatename, self.slate['id'], r['user']['username']))
        

      def _put(self, file_path):
        url = 'https://uploads.slate.host/api/public/' + '8f835cb3-9a39-429b-87ac-f23205d5280d'

        files = {open(file_path, 'rb').name: open(file_path, 'rb')}
        headers = {
          'Authorization': 'Basic ' + self.key
          }

        response = requests.post(url=url, files=files, headers=headers, verify=False)

        if not response.ok:
          raise BackendException(u"An error occured whilst attempting to upload a file: %s"(response))
        else:
          log.Info("File successfully uploaded to Slate.")
      
      def _list(self):
        # Checks if a specific slate has been selectred, otherwise lists all slates
        data = json.dumps({ 'data': {'private': 'true'}})
        headers = {
        'Content-Type': 'application/json', 
        'Authorization': 'Basic ' + self.key
        }
        response = requests.post('https://slate.host/api/v1/get', data=data, headers=headers, verify=False) 

        if not response.ok:
          raise BackendException(u"Slate backend requires a valid API key")
        
        slates = response.json()['slates']
        file_list = []
        for slate in slates:
          files = ['data']['objects']
          for files in slate:
            file_list += file['name']
        
        return file_list
        

      
      def _get(self, filename, local_path):
        data = json.dumps({ 'data': {'private': 'true'}})
        headers = {
        'Content-Type': 'application/json', 
        'Authorization': 'Basic ' + self.key
        }

        response = requests.post('https://slate.host/api/v1/get', data=data, headers=headers, verify=False) 

        if not response.ok:
          raise BackendException(u"Slate backend requires a valid API key")
        
        slates = response.json()['slates']
        file_list = self._list()

        if filename not in file_list:
          raise BackendException(u"The chosen file does not exist in any of your slates")

        for slate in slates:
          for obj in slate['data']['objects']:
            if obj['name'] == filename:
              cid = obj['url'].split("/")[-1]
              break
        
        #TODO - index slates and index filenames to check for duplicates, and 
        try:
          urllib.request('ipfs.io/ipfs/%s'%(cid), local_path)
          log.Info(u'Download slate with cid: %s'%(cid))
        except NameError as e:
          return BackendException(u"Couldn't download slate")


duplicity.backend.register_backend(u'slate', SlateBackend)
