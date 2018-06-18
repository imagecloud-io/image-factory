#!/usr/bin/python
#
# Copyright (c) 2017 Emma Laurijssens van Engelenhoven, <emma@talwyn-esp.nl>
#
#  GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


import base64
import random
from Crypto.Cipher import AES
from ansible.errors import AnsibleFilterError

class FilterModule(object):

    # The filters method ties the label we use in Ansible to the method/function that is actually being executed.
    # Usually we use the same name for both the label and the method.

    def filters(self):
        return {
            'aesencrypt': self.aesencrypt,
            'aesdecrypt': self.aesdecrypt
        }

    # The filter aesencrypt and aesdecrypt take two arguments. The first argument is the data that is 'piped' into the filter.
    # The second argument is the AES key (we'll use AES-256 so a 32 byte key is necessary).

    def aesencrypt(self, blob, key):

        # We need to make sure the key length is correct. Any guesswork or patchwork here weakens security, so
        # raise an error if it's not.

        if (len(key) != 16) and (len(key) != 24) and (len(key) != 32):
            raise AnsibleFilterError("Key length should be 16, 24 or 32 characters")

        # AES uses a block size of 16 bytes. So, the input must be a multiple of 16. The input data could be anything
        # though. So, we will be padding the missing bytes with a byte that indicates the number of characters
        # added. If the input data *is* exactly on a 16 byte boundary, then we'll add 16 bytes. That way, the function
        # that unpads the decrypted data does not have to know anything, it just looks at the last byte, that will
        # range in value from 1 to 16, and remove that much bytes from the data.

        block_size = 16

        def pad(s):
            return s + (block_size - len(s) % block_size) * chr(block_size - len(s) % block_size)

        # AES in CBC mode needs a random 16 byte initialization vector, so that encrypted data can not be related,
        # even when the source data was the same. In that regard, it serves the same purpose as a password salt.
        # The final encrypted data is prepended with the iv, so that the data can be successfully decrypted, and then
        # Base64 encoded to allow for embedding in text structures.

        iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
        _crypto = AES.new(key, AES.MODE_CBC, iv)
        encryptedblob = iv + _crypto.encrypt(pad(blob))

        return base64.b64encode(encryptedblob)

    def aesdecrypt(self, blob, key):

        if (len(key) != 16) and (len(key) != 24) and (len(key) != 32):
            raise AnsibleFilterError("Key length should be 16, 24 or 32 characters")

        def unpad(s):
            return s[0:-ord(s[-1])]

        # When decoding, we first need to isolate the initialization vector. We do that by taking the first 16 bytes
        # from the Base64 decoded data. Then, we use the remainder of the data and the iv, and decrypt the data. That
        # leaves us with the padded data, which only needs to be un-padded.

        iv = base64.b64decode(blob)[:16]
        _crypto = AES.new(key, AES.MODE_CBC, iv)
        decryptedblob = _crypto.decrypt(base64.b64decode(blob)[16:])

        return unpad(decryptedblob)
