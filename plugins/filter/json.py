#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

'''
This method does *not* use the AnsibleJSONEncoder.
As a result, there's no variable substitution.
'''
def to_plain_json(a, *args, **kw):
    return json.dumps(a, *args, **kw)

class FilterModule(object):

    def filters(self):
        return {
            'to_plain_json': to_plain_json
        }
