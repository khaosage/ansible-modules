#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# This file is based on nagios module
#

DOCUMENTATION = '''
---
module: sensu_api
author: RealVNC (andrew.baldwin@realvnc.com)
version: 1.0
description:
    This is a simple ansible interface to sensu-api, it can be used to stash
    and un-stash host from alerting.
options:
    action:
        silence_sensu: stash a host in sensu.
        unsilence_sensu: un-stash a host in sensu.
        remove_sensu_client: delete a client record in sensu.
    minutes:
        time to stash in miinutes.
    host:
        define the host/hosts you wish to stash / un-stash.
    port:
        not required - defaults to 4567
    user:
        user name for sensu-api server.
    password:
        password for sensu-api server.
    comment:
        The message that wiil be populated as Reason field on Sensu Dashboard.
note:
    This module requires the use of delegate_to to specify a server
    running the sensu-api.
'''

EXAMPLES = '''
# silence / stash hosts in sensu
    sensu_api:
      action: silence_sensu
      minutes: 8
      host: "{{ ansible_hostname }}"
      comment: "Stashed for updates"
    delegate_to: 'sensu-api.server.domain'

# unsilence / unstash sensu
    sensu_api:
      action: unsilence_sensu
      host: "{{ ansible_hostname }}"
    delegate_to: 'sensu-api.server.domain'

# remove sensu client
    sensu_api:
      action: remove_sensu_client
      host: "{{ ansible_hostname }}"
    delegate_to: 'sensu-api.server.domain'
'''

import requests
import json
import time


def main():
    ACTION_CHOICES = [
        'silence_sensu',
        'unsilence_sensu',
        'remove_sensu_client',
        ]

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, default=None, choices=ACTION_CHOICES),
            author=dict(default='Ansible'),
            host=dict(required=False, default=None),
            port=dict(default=4567),
            minutes=dict(default=30),
            comment=dict(default=None),
            user=dict(default=None),
            password=dict(default=None),
            )
        )

    action = module.params['action']
    host = module.params['host']
    port = module.params['port']
    user = module.params['user']
    password = module.params['password']
    minutes = module.params['minutes']
    comment = module.params['comment']

    ansible_sensu_api = SensuApi(module, **module.params)
    if module.check_mode:
        module.exit_json(changed=True)
    else:
        ansible_sensu_api.act()


class SensuApi(object):

    def __init__(self, module, **kwargs):
        self.module = module
        self.action = kwargs['action']
        self.author = kwargs['author']
        self.comment = kwargs['comment']
        self.host = kwargs['host']
        self.port = kwargs['port']
        self.user = kwargs['user']
        self.password = kwargs['password']
        self.minutes = int(kwargs['minutes'])

    def _now(self):
        return int(time.time())

    def _secs(self):
        return(self.minutes * 60)

    def silence_sensu(self):
        user = self.user
        password = self.password
        port = self.port
        path = "silence/" + self.host
        comment = self.comment
        expires = self._secs()
        payload = {
            "path": path,
            "content": {
                "reason": comment,
                "source": self.author,
                "username": self.author,
                "timestamp": self._now()},
            "expire": expires,
            }
        url = 'http://localhost:{port}/stashes'.format(port=port)
        info = requests.post(url, data=json.dumps(payload),
                             auth=(user, password))
        return(info.status_code)

    def unsilence_sensu(self):
        user = self.user
        password = self.password
        port = self.port
        path = "silence/" + self.host
        url = 'http://localhost:{port}/stashes/'.format(port=port)
        info = requests.delete(url + path, auth=(user, password))
        return(info.status_code)

    def remove_sensu_client(self):
        user = self.user
        password = self.password
        port = self.port
        host = self.host
        url = 'http://localhost:{port}/clients/'.format(port=port)
        info = requests.delete(url + host, auth=(user, password))
        return(info.status_code)

    def act(self):
        if self.action == 'silence_sensu':
            info = self.silence_sensu()
            if info == 201:
                self.module.exit_json(changed=True)

        elif self.action == 'unsilence_sensu':
            info = self.unsilence_sensu()
            if info == 204:
                self.module.exit_json(changed=True)

        elif self.action == 'remove_sensu_client':
            info = self.remove_sensu_client()
            if info == 202:
                self.module.exit_json(changed=True)

        else:
            self.module.fail_json(msg="unknown action specified: {}".format(
                self.action))


#########################################
# import module
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
