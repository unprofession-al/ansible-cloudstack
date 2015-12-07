#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: cs_template
short_description: Manages templates on Apache CloudStack based clouds.
description:
  - Register a template from URL, create a template from a ROOT volume of a stopped VM or its snapshot and delete templates.
version_added: '2.0'
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the template.
    required: true
  url:
    description:
      - URL of where the template is hosted.
      - Mutually exclusive with C(vm).
    required: false
    default: null
  vm:
    description:
      - VM name the template will be created from its volume or alternatively from a snapshot.
      - VM must be in stopped state if created from its volume.
      - Mutually exclusive with C(url).
    required: false
    default: null
  snapshot:
    description:
      - Name of the snapshot, created from the VM ROOT volume, the template will be created from.
      - C(vm) is required together with this argument.
    required: false
    default: null
  os_type:
    description:
      - OS type that best represents the OS of this template.
    required: false
    default: null
  checksum:
    description:
      - The MD5 checksum value of this template.
      - If set, we search by checksum instead of name.
    required: false
    default: false
  is_ready:
    description:
      - This flag is used for searching existing templates.
      - If set to C(true), it will only list template ready for deployment e.g. successfully downloaded and installed.
      - Recommended to set it to C(false).
    required: false
    default: false
  is_public:
    description:
      - Register the template to be publicly available to all users.
      - Only used if C(state) is present.
    required: false
    default: false
  is_featured:
    description:
      - Register the template to be featured.
      - Only used if C(state) is present.
    required: false
    default: false
  is_dynamically_scalable:
    description:
      - Register the template having XS/VMWare tools installed in order to support dynamic scaling of VM CPU/memory.
      - Only used if C(state) is present.
    required: false
    default: false
  cross_zones:
    description:
      - Whether the template should be syned across zones.
      - Only used if C(state) is present.
    required: false
    default: false
  project:
    description:
      - Name of the project the template to be registered in.
    required: false
    default: null
  zone:
    description:
      - Name of the zone you wish the template to be registered or deleted from.
      - If not specified, first found zone will be used.
    required: false
    default: null
  template_filter:
    description:
      - Name of the filter used to search for the template.
    required: false
    default: 'self'
    choices: [ 'featured', 'self', 'selfexecutable', 'sharedexecutable', 'executable', 'community' ]
  hypervisor:
    description:
      - Name the hypervisor to be used for creating the new template.
      - Relevant when using C(state=present).
    required: false
    default: none
    choices: [ 'KVM', 'VMware', 'BareMetal', 'XenServer', 'LXC', 'HyperV', 'UCS', 'OVM' ]
  requires_hvm:
    description:
      - true if this template requires HVM.
    required: false
    default: false
  password_enabled:
    description:
      - True if the template supports the password reset feature.
    required: false
    default: false
  template_tag:
    description:
      - the tag for this template.
    required: false
    default: null
  sshkey_enabled:
    description:
      - True if the template supports the sshkey upload feature.
    required: false
    default: false
  is_routing:
    description:
      - True if the template type is routing i.e., if template is used to deploy router.
      - Only considered if C(url) is used.
    required: false
    default: false
  format:
    description:
      - The format for the template.
      - Relevant when using C(state=present).
    required: false
    default: null
    choices: [ 'QCOW2', 'RAW', 'VHD', 'OVA' ]
  is_extractable:
    description:
      - True if the template or its derivatives are extractable.
    required: false
    default: false
  details:
    description:
      - Template details in key/value pairs.
    required: false
    default: null
  bits:
    description:
      - 32 or 64 bits support.
    required: false
    default: '64'
  display_text:
    description:
      - Display text of the template.
    required: true
    default: null
  state:
    description:
      - State of the template.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  poll_async:
    description:
      - Poll async jobs until job has finished.
    required: false
    default: true
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Register a systemvm template
- local_action:
    module: cs_template
    name: systemvm-vmware-4.5
    url: "http://packages.shapeblue.com/systemvmtemplate/4.5/systemvm64template-4.5-vmware.ova"
    hypervisor: VMware
    format: OVA
    cross_zones: yes
    os_type: Debian GNU/Linux 7(64-bit)

# Create a template from a stopped virtual machine's volume
- local_action:
    module: cs_template
    name: debian-base-template
    vm: debian-base-vm
    os_type: Debian GNU/Linux 7(64-bit)
    zone: tokio-ix
    password_enabled: yes
    is_public: yes

# Create a template from a virtual machine's root volume snapshot
- local_action:
    module: cs_template
    name: debian-base-template
    vm: debian-base-vm
    snapshot: ROOT-233_2015061509114
    os_type: Debian GNU/Linux 7(64-bit)
    zone: tokio-ix
    password_enabled: yes
    is_public: yes

# Remove a template
- local_action:
    module: cs_template
    name: systemvm-4.2
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the template.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
name:
  description: Name of the template.
  returned: success
  type: string
  sample: Debian 7 64-bit
display_text:
  description: Display text of the template.
  returned: success
  type: string
  sample: Debian 7.7 64-bit minimal 2015-03-19
checksum:
  description: MD5 checksum of the template.
  returned: success
  type: string
  sample: 0b31bccccb048d20b551f70830bb7ad0
status:
  description: Status of the template.
  returned: success
  type: string
  sample: Download Complete
is_ready:
  description: True if the template is ready to be deployed from.
  returned: success
  type: boolean
  sample: true
is_public:
  description: True if the template is public.
  returned: success
  type: boolean
  sample: true
is_featured:
  description: True if the template is featured.
  returned: success
  type: boolean
  sample: true
is_extractable:
  description: True if the template is extractable.
  returned: success
  type: boolean
  sample: true
format:
  description: Format of the template.
  returned: success
  type: string
  sample: OVA
os_type:
  description: Typo of the OS.
  returned: success
  type: string
  sample: CentOS 6.5 (64-bit)
password_enabled:
  description: True if the reset password feature is enabled, false otherwise.
  returned: success
  type: boolean
  sample: false
sshkey_enabled:
  description: true if template is sshkey enabled, false otherwise.
  returned: success
  type: boolean
  sample: false
cross_zones:
  description: true if the template is managed across all zones, false otherwise.
  returned: success
  type: boolean
  sample: false
template_type:
  description: Type of the template.
  returned: success
  type: string
  sample: USER
created:
  description: Date of registering.
  returned: success
  type: string
  sample: 2015-03-29T14:57:06+0200
template_tag:
  description: Template tag related to this template.
  returned: success
  type: string
  sample: special
hypervisor:
  description: Hypervisor related to this template.
  returned: success
  type: string
  sample: VMware
tags:
  description: List of resource tags associated with the template.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
zone:
  description: Name of zone the template is registered in.
  returned: success
  type: string
  sample: zuerich
domain:
  description: Domain the template is related to.
  returned: success
  type: string
  sample: example domain
account:
  description: Account the template is related to.
  returned: success
  type: string
  sample: example account
project:
  description: Name of project the template is related to.
  returned: success
  type: string
  sample: Production
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
def cs_argument_spec():
    return dict(
        api_key = dict(default=None),
        api_secret = dict(default=None, no_log=True),
        api_url = dict(default=None),
        api_http_method = dict(choices=['get', 'post'], default='get'),
        api_timeout = dict(type='int', default=10),
        api_region = dict(default='cloudstack'),
    )

def cs_required_together():
    return [['api_key', 'api_secret', 'api_url']]

class AnsibleCloudStack(object):

    def __init__(self, module):
        if not has_lib_cs:
            module.fail_json(msg="python library cs required: pip install cs")

        self.result = {
            'changed': False,
        }

        # Common returns, will be merged with self.returns
        # search_for_key: replace_with_key
        self.common_returns = {
            'id':           'id',
            'name':         'name',
            'created':      'created',
            'zonename':     'zone',
            'state':        'state',
            'project':      'project',
            'account':      'account',
            'domain':       'domain',
            'displaytext':  'display_text',
            'displayname':  'display_name',
            'description':  'description',
        }

        # Init returns dict for use in subclasses
        self.returns = {}
        # these values will be casted to int
        self.returns_to_int = {}

        self.module = module
        self._connect()

        self.domain = None
        self.account = None
        self.project = None
        self.ip_address = None
        self.zone = None
        self.vm = None
        self.os_type = None
        self.hypervisor = None
        self.capabilities = None
        self.tags = None


    def _connect(self):
        api_key = self.module.params.get('api_key')
        api_secret = self.module.params.get('secret_key')
        api_url = self.module.params.get('api_url')
        api_http_method = self.module.params.get('api_http_method')
        api_timeout = self.module.params.get('api_timeout')

        if api_key and api_secret and api_url:
            self.cs = CloudStack(
                endpoint=api_url,
                key=api_key,
                secret=api_secret,
                timeout=api_timeout,
                method=api_http_method
                )
        else:
            api_region = self.module.params.get('api_region', 'cloudstack')
            self.cs = CloudStack(**read_config(api_region))


    def get_or_fallback(self, key=None, fallback_key=None):
        value = self.module.params.get(key)
        if not value:
            value = self.module.params.get(fallback_key)
        return value


    # TODO: for backward compatibility only, remove if not used anymore
    def _has_changed(self, want_dict, current_dict, only_keys=None):
        return self.has_changed(want_dict=want_dict, current_dict=current_dict, only_keys=only_keys)


    def has_changed(self, want_dict, current_dict, only_keys=None):
        for key, value in want_dict.iteritems():

            # Optionally limit by a list of keys
            if only_keys and key not in only_keys:
                continue

            # Skip None values
            if value is None:
                continue

            if key in current_dict:

                # API returns string for int in some cases, just to make sure
                if isinstance(value, int):
                    current_dict[key] = int(current_dict[key])
                elif isinstance(value, str):
                    current_dict[key] = str(current_dict[key])

                # Only need to detect a singe change, not every item
                if value != current_dict[key]:
                    return True
        return False


    def _get_by_key(self, key=None, my_dict=None):
        if my_dict is None:
            my_dict = {}
        if key:
            if key in my_dict:
                return my_dict[key]
            self.module.fail_json(msg="Something went wrong: %s not found" % key)
        return my_dict


    def get_project(self, key=None):
        if self.project:
            return self._get_by_key(key, self.project)

        project = self.module.params.get('project')
        if not project:
            return None
        args = {}
        args['account'] = self.get_account(key='name')
        args['domainid'] = self.get_domain(key='id')
        projects = self.cs.listProjects(**args)
        if projects:
            for p in projects['project']:
                if project.lower() in [ p['name'].lower(), p['id'] ]:
                    self.project = p
                    return self._get_by_key(key, self.project)
        self.module.fail_json(msg="project '%s' not found" % project)


    def get_ip_address(self, key=None):
        if self.ip_address:
            return self._get_by_key(key, self.ip_address)

        ip_address = self.module.params.get('ip_address')
        if not ip_address:
            self.module.fail_json(msg="IP address param 'ip_address' is required")

        args = {}
        args['ipaddress'] = ip_address
        args['account'] = self.get_account(key='name')
        args['domainid'] = self.get_domain(key='id')
        args['projectid'] = self.get_project(key='id')
        ip_addresses = self.cs.listPublicIpAddresses(**args)

        if not ip_addresses:
            self.module.fail_json(msg="IP address '%s' not found" % args['ipaddress'])

        self.ip_address = ip_addresses['publicipaddress'][0]
        return self._get_by_key(key, self.ip_address)


    def get_vm(self, key=None):
        if self.vm:
            return self._get_by_key(key, self.vm)

        vm = self.module.params.get('vm')
        if not vm:
            self.module.fail_json(msg="Virtual machine param 'vm' is required")

        args = {}
        args['account'] = self.get_account(key='name')
        args['domainid'] = self.get_domain(key='id')
        args['projectid'] = self.get_project(key='id')
        args['zoneid'] = self.get_zone(key='id')
        vms = self.cs.listVirtualMachines(**args)
        if vms:
            for v in vms['virtualmachine']:
                if vm in [ v['name'], v['displayname'], v['id'] ]:
                    self.vm = v
                    return self._get_by_key(key, self.vm)
        self.module.fail_json(msg="Virtual machine '%s' not found" % vm)


    def get_zone(self, key=None):
        if self.zone:
            return self._get_by_key(key, self.zone)

        zone = self.module.params.get('zone')
        zones = self.cs.listZones()

        # use the first zone if no zone param given
        if not zone:
            self.zone = zones['zone'][0]
            return self._get_by_key(key, self.zone)

        if zones:
            for z in zones['zone']:
                if zone in [ z['name'], z['id'] ]:
                    self.zone = z
                    return self._get_by_key(key, self.zone)
        self.module.fail_json(msg="zone '%s' not found" % zone)


    def get_os_type(self, key=None):
        if self.os_type:
            return self._get_by_key(key, self.zone)

        os_type = self.module.params.get('os_type')
        if not os_type:
            return None

        os_types = self.cs.listOsTypes()
        if os_types:
            for o in os_types['ostype']:
                if os_type in [ o['description'], o['id'] ]:
                    self.os_type = o
                    return self._get_by_key(key, self.os_type)
        self.module.fail_json(msg="OS type '%s' not found" % os_type)


    def get_hypervisor(self):
        if self.hypervisor:
            return self.hypervisor

        hypervisor = self.module.params.get('hypervisor')
        hypervisors = self.cs.listHypervisors()

        # use the first hypervisor if no hypervisor param given
        if not hypervisor:
            self.hypervisor = hypervisors['hypervisor'][0]['name']
            return self.hypervisor

        for h in hypervisors['hypervisor']:
            if hypervisor.lower() == h['name'].lower():
                self.hypervisor = h['name']
                return self.hypervisor
        self.module.fail_json(msg="Hypervisor '%s' not found" % hypervisor)


    def get_account(self, key=None):
        if self.account:
            return self._get_by_key(key, self.account)

        account = self.module.params.get('account')
        if not account:
            return None

        domain = self.module.params.get('domain')
        if not domain:
            self.module.fail_json(msg="Account must be specified with Domain")

        args = {}
        args['name'] = account
        args['domainid'] = self.get_domain(key='id')
        args['listall'] = True
        accounts = self.cs.listAccounts(**args)
        if accounts:
            self.account = accounts['account'][0]
            return self._get_by_key(key, self.account)
        self.module.fail_json(msg="Account '%s' not found" % account)


    def get_domain(self, key=None):
        if self.domain:
            return self._get_by_key(key, self.domain)

        domain = self.module.params.get('domain')
        if not domain:
            return None

        args = {}
        args['listall'] = True
        domains = self.cs.listDomains(**args)
        if domains:
            for d in domains['domain']:
                if d['path'].lower() in [ domain.lower(), "root/" + domain.lower(), "root" + domain.lower() ]:
                    self.domain = d
                    return self._get_by_key(key, self.domain)
        self.module.fail_json(msg="Domain '%s' not found" % domain)


    def get_tags(self, resource=None):
        if not self.tags:
            args = {}
            args['projectid'] = self.get_project(key='id')
            args['account'] = self.get_account(key='name')
            args['domainid'] = self.get_domain(key='id')
            args['resourceid'] = resource['id']
            response = self.cs.listTags(**args)
            self.tags = response.get('tag', [])

        existing_tags = []
        if self.tags:
            for tag in self.tags:
                existing_tags.append({'key': tag['key'], 'value': tag['value']})
        return existing_tags


    def _process_tags(self, resource, resource_type, tags, operation="create"):
        if tags:
            self.result['changed'] = True
            if not self.module.check_mode:
                args = {}
                args['resourceids']  = resource['id']
                args['resourcetype'] = resource_type
                args['tags']         = tags
                if operation == "create":
                    response = self.cs.createTags(**args)
                else:
                    response = self.cs.deleteTags(**args)
                self.poll_job(response)


    def _tags_that_should_exist_or_be_updated(self, resource, tags):
        existing_tags = self.get_tags(resource)
        return [tag for tag in tags if tag not in existing_tags]


    def _tags_that_should_not_exist(self, resource, tags):
        existing_tags = self.get_tags(resource)
        return [tag for tag in existing_tags if tag not in tags]


    def ensure_tags(self, resource, resource_type=None):
        if not resource_type or not resource:
            self.module.fail_json(msg="Error: Missing resource or resource_type for tags.")

        if 'tags' in resource:
            tags = self.module.params.get('tags')
            if tags is not None:
                self._process_tags(resource, resource_type, self._tags_that_should_not_exist(resource, tags), operation="delete")
                self._process_tags(resource, resource_type, self._tags_that_should_exist_or_be_updated(resource, tags))
                self.tags = None
                resource['tags'] = self.get_tags(resource)
        return resource


    def get_capabilities(self, key=None):
        if self.capabilities:
            return self._get_by_key(key, self.capabilities)
        capabilities = self.cs.listCapabilities()
        self.capabilities = capabilities['capability']
        return self._get_by_key(key, self.capabilities)


    # TODO: for backward compatibility only, remove if not used anymore
    def _poll_job(self, job=None, key=None):
        return self.poll_job(job=job, key=key)


    def poll_job(self, job=None, key=None):
        if 'jobid' in job:
            while True:
                res = self.cs.queryAsyncJobResult(jobid=job['jobid'])
                if res['jobstatus'] != 0 and 'jobresult' in res:
                    if 'errortext' in res['jobresult']:
                        self.module.fail_json(msg="Failed: '%s'" % res['jobresult']['errortext'])
                    if key and key in res['jobresult']:
                        job = res['jobresult'][key]
                    break
                time.sleep(2)
        return job


    def get_result(self, resource):
        if resource:
            returns = self.common_returns.copy()
            returns.update(self.returns)
            for search_key, return_key in returns.iteritems():
                if search_key in resource:
                    self.result[return_key] = resource[search_key]

            # Bad bad API does not always return int when it should.
            for search_key, return_key in self.returns_to_int.iteritems():
                if search_key in resource:
                    self.result[return_key] = int(resource[search_key])

            # Special handling for tags
            if 'tags' in resource:
                self.result['tags'] = []
                for tag in resource['tags']:
                    result_tag          = {}
                    result_tag['key']   = tag['key']
                    result_tag['value'] = tag['value']
                    self.result['tags'].append(result_tag)
        return self.result


class AnsibleCloudStackTemplate(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackTemplate, self).__init__(module)
        self.returns = {
            'checksum':         'checksum',
            'status':           'status',
            'isready':          'is_ready',
            'templatetag':      'template_tag',
            'sshkeyenabled':    'sshkey_enabled',
            'passwordenabled':  'password_enabled',
            'tempaltetype':     'template_type',
            'ostypename':       'os_type',
            'crossZones':       'cross_zones',
            'isextractable':    'is_extractable',
            'isfeatured':       'is_featured',
            'ispublic':         'is_public',
            'format':           'format',
            'hypervisor':       'hypervisor',
        }


    def _get_args(self):
        args                            = {}
        args['name']                    = self.module.params.get('name')
        args['displaytext']             = self.get_or_fallback('display_text', 'name')
        args['bits']                    = self.module.params.get('bits')
        args['isdynamicallyscalable']   = self.module.params.get('is_dynamically_scalable')
        args['isextractable']           = self.module.params.get('is_extractable')
        args['isfeatured']              = self.module.params.get('is_featured')
        args['ispublic']                = self.module.params.get('is_public')
        args['passwordenabled']         = self.module.params.get('password_enabled')
        args['requireshvm']             = self.module.params.get('requires_hvm')
        args['templatetag']             = self.module.params.get('template_tag')
        args['ostypeid']                = self.get_os_type(key='id')

        if not args['ostypeid']:
            self.module.fail_json(msg="Missing required arguments: os_type")

        return args


    def get_root_volume(self, key=None):
        args                        = {}
        args['account']             = self.get_account(key='name')
        args['domainid']            = self.get_domain(key='id')
        args['projectid']           = self.get_project(key='id')
        args['virtualmachineid']    = self.get_vm(key='id')
        args['type']                = "ROOT"

        volumes = self.cs.listVolumes(**args)
        if volumes:
            return self._get_by_key(key, volumes['volume'][0])
        self.module.fail_json(msg="Root volume for '%s' not found" % self.get_vm('name'))


    def get_snapshot(self, key=None):
        snapshot = self.module.params.get('snapshot')
        if not snapshot:
            return None

        args                = {}
        args['account']     = self.get_account(key='name')
        args['domainid']    = self.get_domain(key='id')
        args['projectid']   = self.get_project(key='id')
        args['volumeid']    = self.get_root_volume('id')
        snapshots = self.cs.listSnapshots(**args)
        if snapshots:
            for s in snapshots['snapshot']:
                if snapshot in [ s['name'], s['id'] ]:
                    return self._get_by_key(key, s)
        self.module.fail_json(msg="Snapshot '%s' not found" % snapshot)


    def create_template(self):
        template = self.get_template()
        if not template:
            self.result['changed'] = True

            args = self._get_args()
            snapshot_id = self.get_snapshot(key='id')
            if snapshot_id:
                args['snapshotid'] = snapshot_id
            else:
                args['volumeid']  = self.get_root_volume('id')

            if not self.module.check_mode:
                template = self.cs.createTemplate(**args)

                if 'errortext' in template:
                    self.module.fail_json(msg="Failed: '%s'" % template['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    template = self._poll_job(template, 'template')
        return template


    def register_template(self):
        template = self.get_template()
        if not template:
            self.result['changed'] = True
            args                    = self._get_args()
            args['url']             = self.module.params.get('url')
            args['format']          = self.module.params.get('format')
            args['checksum']        = self.module.params.get('checksum')
            args['isextractable']   = self.module.params.get('is_extractable')
            args['isrouting']       = self.module.params.get('is_routing')
            args['sshkeyenabled']   = self.module.params.get('sshkey_enabled')
            args['hypervisor']      = self.get_hypervisor()
            args['domainid']        = self.get_domain(key='id')
            args['account']         = self.get_account(key='name')
            args['projectid']       = self.get_project(key='id')

            if not self.module.params.get('cross_zones'):
                args['zoneid'] = self.get_zone(key='id')
            else:
                args['zoneid'] = -1

            if not self.module.check_mode:
                res = self.cs.registerTemplate(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
                template = res['template']
        return template


    def get_template(self):
        args                    = {}
        args['isready']         = self.module.params.get('is_ready')
        args['templatefilter']  = self.module.params.get('template_filter')
        args['domainid']        = self.get_domain(key='id')
        args['account']         = self.get_account(key='name')
        args['projectid']       = self.get_project(key='id')

        if not self.module.params.get('cross_zones'):
            args['zoneid'] = self.get_zone(key='id')

        # if checksum is set, we only look on that.
        checksum = self.module.params.get('checksum')
        if not checksum:
            args['name'] = self.module.params.get('name')

        templates = self.cs.listTemplates(**args)
        if templates:
            # if checksum is set, we only look on that.
            if not checksum:
                return templates['template'][0]
            else:
                for i in templates['template']:
                    if 'checksum' in i and i['checksum'] == checksum:
                        return i
        return None


    def remove_template(self):
        template = self.get_template()
        if template:
            self.result['changed'] = True

            args            = {}
            args['id']      = template['id']
            args['zoneid']  = self.get_zone(key='id')

            if not self.module.check_mode:
                res = self.cs.deleteTemplate(**args)

                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    res = self._poll_job(res, 'template')
        return template



def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name = dict(required=True),
        display_text = dict(default=None),
        url = dict(default=None),
        vm = dict(default=None),
        snapshot = dict(default=None),
        os_type = dict(default=None),
        is_ready = dict(type='bool', choices=BOOLEANS, default=False),
        is_public = dict(type='bool', choices=BOOLEANS, default=True),
        is_featured = dict(type='bool', choices=BOOLEANS, default=False),
        is_dynamically_scalable = dict(type='bool', choices=BOOLEANS, default=False),
        is_extractable = dict(type='bool', choices=BOOLEANS, default=False),
        is_routing = dict(type='bool', choices=BOOLEANS, default=False),
        checksum = dict(default=None),
        template_filter = dict(default='self', choices=['featured', 'self', 'selfexecutable', 'sharedexecutable', 'executable', 'community']),
        hypervisor = dict(choices=['KVM', 'VMware', 'BareMetal', 'XenServer', 'LXC', 'HyperV', 'UCS', 'OVM', 'Simulator'], default=None),
        requires_hvm = dict(type='bool', choices=BOOLEANS, default=False),
        password_enabled = dict(type='bool', choices=BOOLEANS, default=False),
        template_tag = dict(default=None),
        sshkey_enabled = dict(type='bool', choices=BOOLEANS, default=False),
        format = dict(choices=['QCOW2', 'RAW', 'VHD', 'OVA'], default=None),
        details = dict(default=None),
        bits = dict(type='int', choices=[ 32, 64 ], default=64),
        state = dict(choices=['present', 'absent'], default='present'),
        cross_zones = dict(type='bool', choices=BOOLEANS, default=False),
        zone = dict(default=None),
        domain = dict(default=None),
        account = dict(default=None),
        project = dict(default=None),
        poll_async = dict(type='bool', choices=BOOLEANS, default=True),
    ))

    required_together = cs_required_together()
    required_together.extend([
        ['format', 'url', 'hypervisor'],
    ])

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=required_together,
        mutually_exclusive = (
            ['url', 'vm'],
        ),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_tpl = AnsibleCloudStackTemplate(module)

        state = module.params.get('state')
        if state in ['absent']:
            tpl = acs_tpl.remove_template()
        else:
            if module.params.get('url'):
                tpl = acs_tpl.register_template()
            elif module.params.get('vm'):
                tpl = acs_tpl.create_template()
            else:
                module.fail_json(msg="one of the following is required on state=present: url,vm")

        result = acs_tpl.get_result(tpl)

    except CloudStackException as e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
