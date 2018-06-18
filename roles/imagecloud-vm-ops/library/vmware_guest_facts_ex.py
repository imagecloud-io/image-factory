#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module is also sponsored by E.T.A.I. (www.etai.fr)
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: vmware_guest_facts
short_description: Gather facts about a single VM
description:
    - Gather facts about a single VM on a VMware ESX cluster
version_added: 2.3
author:
    - Loic Blot (@nerzhul) <loic.blot@unix-experience.fr>
notes:
    - Tested on vSphere 5.5
requirements:
    - "python >= 2.6"
    - PyVmomi
options:
   name:
        description:
            - Name of the VM to work with
        required: True
   name_match:
        description:
            - If multiple VMs matching the name, use the first or last found
        default: 'first'
        choices: ['first', 'last']
   uuid:
        description:
            - UUID of the instance to manage if known, this is VMware's unique identifier.
            - This is required if name is not supplied.
   folder:
        description:
            - Destination folder, absolute path to find an existing guest.
            - This is required if name is supplied.
   datacenter:
        description:
            - Destination datacenter for the deploy operation
        required: True
extends_documentation_fragment: vmware.documentation
'''

EXAMPLES = '''
- name: Gather VM facts
  vmware_guest_facts:
    hostname: 192.168.1.209
    username: administrator@vsphere.local
    password: vmware
    validate_certs: no
    uuid: 421e4592-c069-924d-ce20-7e7533fab926
  delegate_to: localhost
  register: facts
'''

RETURN = """
instance:
    description: metadata about the virtual machine
    returned: always
    type: dict
    sample: None
"""

import os
import time

# import module snippets
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.six import iteritems
from ansible.module_utils.vmware import connect_to_api, find_vm_by_id, list_snapshots

try:
    import json
except ImportError:
    import simplejson as json

HAS_PYVMOMI = False
try:
    import pyVmomi
    from pyVmomi import vim

    HAS_PYVMOMI = True
except ImportError:
    pass

def gather_vm_facts(content, vm):
    """ Gather facts from vim.VirtualMachine object. """
    facts = {
        'module_hw': True,
        'hw_name': vm.config.name,
        'hw_power_status': vm.summary.runtime.powerState,
        'hw_guest_full_name': vm.summary.guest.guestFullName,
        'hw_guest_id': vm.summary.guest.guestId,
        'hw_product_uuid': vm.config.uuid,
        'hw_processor_count': vm.config.hardware.numCPU,
        'hw_memtotal_mb': vm.config.hardware.memoryMB,
        'hw_interfaces': [],
        'guest_tools_status': vm.guest.toolsRunningStatus,
        'guest_tools_version': vm.guest.toolsVersion,
        'ipv4': None,
        'ipv6': None,
        'annotation': vm.config.annotation,
        'customvalues': {},
        'snapshots': [],
        'current_snapshot': None,
        'esx_host': vm.summary.runtime.host.name,
    }

    cfm = content.customFieldsManager
    # Resolve custom values
    for value_obj in vm.summary.customValue:
        kn = value_obj.key
        if cfm is not None and cfm.field:
            for f in cfm.field:
                if f.key == value_obj.key:
                    kn = f.name
                    # Exit the loop immediately, we found it
                    break

        facts['customvalues'][kn] = value_obj.value

    net_dict = {}
    for device in vm.guest.net:
        net_dict[device.macAddress] = list(device.ipAddress)

    for k, v in iteritems(net_dict):
        for ipaddress in v:
            if ipaddress:
                if '::' in ipaddress:
                    facts['ipv6'] = ipaddress
                else:
                    facts['ipv4'] = ipaddress

    ethernet_idx = 0
    for idx, entry in enumerate(vm.config.hardware.device):
        if not hasattr(entry, 'macAddress'):
            continue

        if entry.macAddress:
            mac_addr = entry.macAddress
            mac_addr_dash = mac_addr.replace(':', '-')
        else:
            mac_addr = mac_addr_dash = None

        factname = 'hw_eth' + str(ethernet_idx)
        facts[factname] = {
            'addresstype': entry.addressType,
            'label': entry.deviceInfo.label,
            'macaddress': mac_addr,
            'ipaddresses': net_dict.get(entry.macAddress, None),
            'macaddress_dash': mac_addr_dash,
            'summary': entry.deviceInfo.summary,
        }
        facts['hw_interfaces'].append('eth' + str(ethernet_idx))
        ethernet_idx += 1

    snapshot_facts = list_snapshots(vm)
    if 'snapshots' in snapshot_facts:
        facts['snapshots'] = snapshot_facts['snapshots']
        facts['current_snapshot'] = snapshot_facts['current_snapshot']
    return facts


class PyVmomiHelper(object):
    def __init__(self, module):
        if not HAS_PYVMOMI:
            module.fail_json(msg='pyvmomi module required')

        self.module = module
        self.params = module.params
        self.content = connect_to_api(self.module)

    def getvm(self, name=None, uuid=None, folder=None):
        vm = None

        if uuid:
            vm = find_vm_by_id(self.content, vm_id=uuid, vm_id_type="uuid")
        elif folder:
            # Build the absolute folder path to pass into the search method
            if not self.params['folder'].startswith('/'):
                self.module.fail_json(msg="Folder %(folder)s needs to be an absolute path, starting with '/'." % self.params)
            searchpath = '%(datacenter)s%(folder)s' % self.params

            # get all objects for this path ...
            f_obj = self.content.searchIndex.FindByInventoryPath(searchpath)
            if f_obj:
                if isinstance(f_obj, vim.Datacenter):
                    f_obj = f_obj.vmFolder
                for c_obj in f_obj.childEntity:
                    if not isinstance(c_obj, vim.VirtualMachine):
                        continue
                    if c_obj.name == name:
                        vm = c_obj
                        if self.params['name_match'] == 'first':
                            break

        return vm

    def gather_facts(self, vm):
        return gather_vm_facts(self.content, vm)


def get_obj(content, vimtype, name):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True)
    for c in container.view:
        if name:
            if c.name == name:
                obj = c
                break
        else:
            obj = c
            break

    container.Destroy()
    return obj


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hostname=dict(
                type='str',
                default=os.environ.get('VMWARE_HOST')
            ),
            username=dict(
                type='str',
                default=os.environ.get('VMWARE_USER')
            ),
            password=dict(
                type='str', no_log=True,
                default=os.environ.get('VMWARE_PASSWORD')
            ),
            validate_certs=dict(required=False, type='bool', default=True),
            name=dict(required=True, type='str'),
            name_match=dict(required=False, type='str', default='first'),
            uuid=dict(required=False, type='str'),
            folder=dict(required=False, type='str', default='/vm'),
            datacenter=dict(required=True, type='str'),
        ),
    )

    # Prepend /vm if it was missing from the folder path, also strip trailing slashes
    if not module.params['folder'].startswith('/vm') and module.params['folder'].startswith('/'):
        module.params['folder'] = '/vm%(folder)s' % module.params
    module.params['folder'] = module.params['folder'].rstrip('/')

    pyv = PyVmomiHelper(module)
    # Check if the VM exists before continuing
    vm = pyv.getvm(name=module.params['name'],
                   folder=module.params['folder'],
                   uuid=module.params['uuid'])

    # VM already exists
    if vm:
        try:
            module.exit_json(instance=pyv.gather_facts(vm))
        except Exception:
            e = get_exception()
            module.fail_json(msg="Fact gather failed with exception %s" % e)
    else:
        module.fail_json(msg="Unable to gather facts for non-existing VM %(name)s" % module.params)

if __name__ == '__main__':
    main()
