#!/usr/bin/python

import re
import uuid

class FilterModule(object):
    def filters(self):
        return {
            'tblsplit': self.tblsplit,
            'valid_mshostname': self.valid_mshostname,
            'slice': self.slice
        }

    def tblsplit(self, line_to_split, field_number):
        row_splitter = re.compile("  +")  # Finds a sequence of two or more spaces
        fields = row_splitter.split(str(line_to_split).encode('utf-8'))
        try:
            field = fields[field_number]
        except:
            field = ''
        return field

    def valid_mshostname(self, fqdn):
        if len(fqdn) > 253:
            return "host-{}".format(uuid.uuid4().hex[-7:])

        hostname = fqdn.split('.')[0]

        if hostname == "":
            return "host-{}".format(uuid.uuid4().hex[-7:])

        while hostname[0] == '-':
            hostname = hostname[1:]  # strip dashes on the left, if present

        while hostname[-1] == '-':
            hostname = hostname[:-1]  # strip dashes on the right, if present

        if len(hostname) > 15:
            return "host-{}".format(uuid.uuid4().hex[-7:])

        return ''.join(e for e in hostname if (e.isalnum() or e == '-'))

    #
    # Returns subdictionary that contains only those keys that start with a certain string
    # see: https://stackoverflow.com/questions/4558983/slicing-a-dictionary-by-keys-that-start-with-a-certain-string
    # Note: it will _only_ return k/v when `value` is _not_ empty
    #
    # Parameters:
    #
    # d     ~ incoming dictionary
    # s     ~ search string
    # strip ~ wether or not to strip string (s) from key name
    #
    # Returns: dictionary
    #
    def slice(self, d, s, strip=False):
        return {k[len(s):] if strip else k:v for k,v in d.iteritems() if k.startswith(s) and v}
