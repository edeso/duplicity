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
from duplicity import log
from duplicity import util
from duplicity.errors import BackendException

class SlateBackend(duplicity.backend.Backend):
    u"""
    Backend for Slate
    """
    def __init__(self, parsed_url):
        duplicity.backend.Backend.__init__(self, parsed_url)
        log.Info(u"loading slate backend...")
        if u'SLATE_API_KEY' not in os.environ.keys():
            raise BackendException(u"You must set an environment variable SLATE_API_KEY as the value of your slate API key")
        else:
            self.key = os.environ[u'SLATE_API_KEY']
    
        if u'SLATE_SSL_VERIFY' not in os.environ.keys():
            self.verify = True
        else:
            if u'SLATE_SSL_VERIFY' == u'0':
                self.verify = False
            else:
                self.verify = True
      
        data = json.dumps({ u'data': {u'private': u'true'}})
        headers = {
            u'Content-Type': u'application/json', 
            u'Authorization': u'Basic ' + self.key
            }

        response = requests.post(u'https://slate.host/api/v1/get', data=data, headers=headers, verify=self.verify) 
        if not response.ok:
            raise BackendException(u"Slate backend requires a valid API key")
    
        self.slate_id = parsed_url.geturl().split('/')[-1]
    
        # Maybe in the future if necessary :
        # r = response.json()
        # if len(r['slates']) < 1: 
        #   raise BackendException(u"No valid slates found, please create a slate to upload files")
    
        # self.slates = [slate['data']['name']:slate for slate in r['slates']]
        # slatenames = slates.keys()
    
        # if slatename not in slatenames:
        #   raise BackendException(u"The chosen slate does not exist")

        # self.slate = slate[slatename]
        # self.id = slate['id']

        # log.Info('Loaded slate\nname: %s\uuid: %s\nas: %s'%(slatename, self.slate['id'], r['user']['username']))
        # etc.....
    
  

    def _put(self, source_path, remote_filename=None):
        data = json.dumps({ u'data': {u'private': u'true'}})
        headers = {
            u'Content-Type': u'application/json', 
            u'Authorization': u'Basic ' + self.key
            }

        print("opening")
        if remote_filename is None:
            print("uploading(1)")    
            files = {open(util.fsdecode(source_path.name), u'rb').name: open(util.fsdecode(source_path.name), u'rb')}

        else:
            print("uploading(2)")    
            print("remote_filename: ", str(remote_filename))
            files = {util.fsdecode(remote_filename): open(util.fsdecode(source_path.name), u'rb')}

        headers = {
            u'Authorization': u'Basic ' + self.key
            }

        print("response")
        response = requests.post(url=u'https://uploads.slate.host/api/public/' + self.slate_id, files=files, headers=headers, verify=self.verify)
        print("response handled")

        if not response.ok:
            raise BackendException(u"An error occured whilst attempting to upload a file: %s"%(response))
        else:
            log.Info(u"File successfully uploaded to slate with id:" + self.slate_id)
  
    def _list(self):

        # Checks if a specific slate has been selected, otherwise lists all slates
        log.Info(u"Slate ID: %s"%(self.slate_id))
        data = json.dumps({ u'data': {u'private': u'true'}})
        headers = {
        u'Content-Type': u'application/json', 
        u'Authorization': u'Basic ' + self.key
        }
        response = requests.post(u'https://slate.host/api/v1/get', data=data, headers=headers, verify=self.verify) 

        if not response.ok:
            raise BackendException(u"Slate backend requires a valid API key")
    
        slates = response.json()[u'slates']
        log.Info("SLATES:\n%s"%(slates))
        file_list = []
        for slate in slates:
            if slate[u'id'] == self.slate_id:
                files = slate[u'data'][u'objects']
                for f in files:
                    file_list.append(f[u'name'])
            else:
                log.Info(u"Could not find slate with id: " + self.slate_id)

        return file_list
    

  
    def _get(self, remote_filename, local_path):
        # Downloads chosen file from IPFS by parsing its cid
        data = json.dumps({ u'data': {u'private': u'true'}})
        headers = {
            u'Content-Type': u'application/json', 
            u'Authorization': u'Basic ' + self.key
        }

        response = requests.post(u'https://slate.host/api/v1/get', data=data, headers=headers, verify=self.verify) 
    
        slates = response.json()[u'slates']
        # file_list = self._list()

        # if remote_filename not in file_list:
        #     raise BackendException(u"The chosen file does not exist in the chosen slate")

        for slate in slates:
            if slate[u'id'] == self.slate_id:
                for obj in slate[u'data'][u'objects']:
                    if obj[u'name'] == remote_filename:
                        cid = obj[u'url'].split(u"/")[-1]
                        break
                    else:
                        raise BackendException(u"The file '" + remote_filename +u"' could not be found in the specified slate")
            else:
                raise BackendException(u"A slate with id " + self.slate_id + u" does not exist")
    
        try:
            urllib.request(u'ipfs.io/ipfs/%s'%(cid), util.fsdecode(local_path.name))
            log.Info(u'Downloaded file with cid: %s'%(cid))
        except NameError as e:
            raise BackendException(u"Couldn't download file")


duplicity.backend.register_backend(u'slate', SlateBackend)
