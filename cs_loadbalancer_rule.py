#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, Darren Worrall <darren@iweb.co.uk>
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
module: cs_loadbalancer_rule
short_description: Manages load balancer rules on Apache CloudStack based clouds.
description:
    - Add, update and remove load balancer rules.
version_added: '2.0'
author:
    - "Darren Worrall @dazworrall"
    - "René Moser (@resmo)"
options:
  name:
    description:
      - The name of the load balancer rule.
    required: true
  algorithm:
    description:
      - Load balancer algorithm
      - Required when using C(state=present).
    required: false
    choices: [ 'source', 'roundrobin', 'leastconn' ]
    default: 'source'
  private_port:
    description:
      - The private port of the private ip address/virtual machine where the network traffic will be load balanced to.
      - Required when using C(state=present).
      - Can not be updated after creation due API limitation.
    required: false
    default: null
  public_port:
    description:
      - The public port from where the network traffic will be load balanced from.
      - Required when using C(state=present).
      - Can not be updated after creation due API limitation.
    required: true
    default: null
  public_ip:
    description:
      - Public IP address from where the network traffic will be load balanced from.
    required: true
    aliases: [ 'ip_address' ]
  open_firewall:
    description:
      - Whether the firewall rule for public port should be created, while creating the new rule.
      - Use M(cs_firewall) for managing firewall rules.
    required: false
    default: false
  cidr:
    description:
      - CIDR (full notation) to be used for firewall rule if required.
    required: false
    default: null
  project:
    description:
      - Name of the project the load balancer IP address is related to.
    required: false
    default: null
  state:
    description:
      - State of the rule.
    required: true
    default: 'present'
    choices: [ 'present', 'absent' ]
  domain:
    description:
      - Domain the rule is related to.
    required: false
    default: null
  account:
    description:
      - Account the rule is related to.
    required: false
    default: null
  zone:
    description:
      - Name of the zone in which the rule shoud be created.
      - If not set, default zone is used.
    required: false
    default: null
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
# Create a load balancer rule
- local_action:
    module: cs_loadbalancer
    name: balance_http
    public_ip: 1.2.3.4
    algorithm: leastconn
    public_port: 80
    private_port: 8080

# Create a load balancer rule with members
- local_action:
    module: cs_loadbalancer
    name: balance_http
    public_ip: 1.2.3.4
    algorithm: roundrobin
    public_port: 80
    private_port: 80
    members:
    - web01
    - web02

# Delete a load balancer rule
- local_action:
    module: cs_loadbalancer
    name: balance_http
    public_ip: 1.2.3.4
    state: absent
'''

RETURN = '''
---
id:
  description: UUID of the rule.
  returned: success
  type: string
  sample: a6f7a5fc-43f8-11e5-a151-feff819cdc9f
zone:
  description: Name of zone the rule is related to.
  returned: success
  type: string
  sample: ch-gva-2
project:
  description: Name of project the rule is related to.
  returned: success
  type: string
  sample: Production
account:
  description: Account the rule is related to.
  returned: success
  type: string
  sample: example account
domain:
  description: Domain the rule is related to.
  returned: success
  type: string
  sample: example domain
algorithm:
  description: Load balancer algorithm used.
  returned: success
  type: string
  sample: "source"
cidr:
  description: CIDR to forward traffic from.
  returned: success
  type: string
  sample: ""
name:
  description: Name of the rule.
  returned: success
  type: string
  sample: "http-lb"
description:
  description: Description of the rule.
  returned: success
  type: string
  sample: "http load balancer rule"
public_port:
  description: Public port.
  returned: success
  type: string
  sample: 80
private_port:
  description: Private IP address.
  returned: success
  type: string
  sample: 80
public_ip:
  description: Public IP address.
  returned: success
  type: string
  sample: "1.2.3.4"
members:
  description: List of member names of the rule.
  returned: success
  type: list
  sample: [ "web01", "web02", "web03" ]
tags:
  description: List of resource tags associated with the rule.
  returned: success
  type: dict
  sample: '[ { "key": "foo", "value": "bar" } ]'
state:
  description: State of the rule.
  returned: success
  type: string
  sample: "Add"
'''

try:
    from cs import CloudStack, CloudStackException, read_config
    has_lib_cs = True
except ImportError:
    has_lib_cs = False

# import cloudstack common
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


    def _get_by_key(self, key=None, my_dict={}):
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
        args = {}
        args['projectid'] = self.get_project(key='id')
        args['domainid'] = self.get_domain(key='id')
        args['resourceid'] = resource['id']

        response = self.cs.listTags(**args)

        existing_tags = []

        if response:
            for tag in response['tag']:
                existing_tags.append({'key': tag['key'], 'value': tag['value']})

        return existing_tags

    def _delete_tags(self, resource, resource_type, tags):
        if tags:
            self.result['changed'] = True
            if not self.module.check_mode:
                args = {}
                args['resourceids']  = resource['id']
                args['resourcetype'] = resource_type
                args['tags']         = tags
                self.cs.deleteTags(**args)


    def _create_tags(self, resource, resource_type, tags):
        if tags:
            self.result['changed'] = True
            if not self.module.check_mode:
                args = {}
                args['resourceids']  = resource['id']
                args['resourcetype'] = resource_type
                args['tags']         = tags
                self.cs.createTags(**args)

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
                self._delete_tags(resource, resource_type, self._tags_that_should_not_exist(resource, tags))
                self._create_tags(resource, resource_type, self._tags_that_should_exist_or_be_updated(resource, tags))
                resource['tags'] = self.get_tags(resource)
        return resource


    def get_disk_offering(self, key=None):
        disk_offering = self.module.params.get('disk_offering')

        if not disk_offering:
            return None

        disk_offerings = self.cs.listDiskOfferings()
        if disk_offerings:
            for d in disk_offerings['diskoffering']:
                if disk_offering in [d['displaytext'], d['name'], d['id']]:
                    return self._get_by_key(key, d)
        self.module.fail_json(msg="Disk offering '%s' not found" % disk_offering)


    def get_capabilities(self, key=None):
        if self.capabilities:
            return self._get_by_key(key, self.capabilities)
        capabilities = self.cs.listCapabilities()
        self.capabilities = capabilities['capability']
        return self._get_by_key(key, self.capabilities)


    # TODO: for backward compatibility only, remove it if not used anymore
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

            # Special handling for tags
            if 'tags' in resource:
                self.result['tags'] = []
                for tag in resource['tags']:
                    result_tag          = {}
                    result_tag['key']   = tag['key']
                    result_tag['value'] = tag['value']
                    self.result['tags'].append(result_tag)
        return self.result


class AnsibleCloudStackLBRule(AnsibleCloudStack):

    def __init__(self, module):
        super(AnsibleCloudStackLBRule, self).__init__(module)
        self.returns = {
            'publicip': 'public_ip',
            'algorithm': 'algorithm',
            'cidrlist': 'cidr',
            'members': 'members',
        }
        # these values will be casted to int
        self.returns_to_int = {
            'publicport': 'public_port',
            'privateport': 'private_port',
        }


    def get_ip_address(self, key=None, param_name='ip_address'):
        if self.ip_address:
            return self._get_by_key(key, self.ip_address)

        ip_address = self.module.params.get(param_name)
        if not ip_address:
            self.module.fail_json(msg="IP address param '%s' is required" % param_name)

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


    def get_rule(self, **kwargs):
        rules = self.cs.listLoadBalancerRules(**kwargs)
        if rules:
            return rules['loadbalancerrule'][0]


    def _get_common_args(self):
        return {
            'account': self.get_account(key='name'),
            'domainid': self.get_domain(key='id'),
            'projectid': self.get_project(key='id'),
            'zoneid': self.get_zone(key='id'),
            'publicipid': self.get_ip_address(key='id', param_name='public_ip'),
            'name': self.module.params.get('name'),
        }


    def get_wanted_members_ids(self, wanted_member_names):
        wanted_members_id_list = []
        args = {}
        args['account'] = self.get_account(key='name')
        args['domainid'] = self.get_domain(key='id')
        args['projectid'] = self.get_project(key='id')
        args['zoneid'] = self.get_zone(key='id')
        res = self.cs.listVirtualMachines(**args)
        for vm in res.get('virtualmachine', []):
            if vm['name'] in wanted_member_names:
                wanted_members_id_list.append(vm['id'])
        if len(wanted_member_names) != len(wanted_members_id_list):
            self.module.fail_json(msg="One or more members could not be found: %s" % ', '.join(wanted_member_names))
        return wanted_members_id_list


    def get_existing_member_ids(self, rule):
        existing_members_id_list = []
        args = {}
        args['id'] = rule['id']
        res = self.cs.listLoadBalancerRuleInstances(**args)
        for vm in res.get('loadbalancerruleinstance', []):
            existing_members_id_list.append(vm['id'])
        return existing_members_id_list


    def present_members(self, rule):
        wanted_members_names = self.module.params.get('members')
        if wanted_members_names is None:
            return rule

        wanted_members_ids   = self.get_wanted_members_ids(wanted_members_names)
        existing_members_ids = self.get_existing_member_ids(rule)
        member_ids_to_remove = list(set(existing_members_ids) - set(wanted_members_ids))
        member_ids_to_assign = list(set(wanted_members_ids) - set(existing_members_ids))

        args = {}
        args['id'] = rule['id']

        if member_ids_to_assign:
            self.result['changed'] = True
            args['virtualmachineids'] = ','.join(member_ids_to_assign)
            res = self.cs.assignToLoadBalancerRule(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                res = self.poll_job(res, 'loadbalancerrule')

        if member_ids_to_remove:
            self.result['changed'] = True
            args['virtualmachineids'] = ','.join(member_ids_to_remove)
            res = self.cs.removeFromLoadBalancerRule(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                res = self.poll_job(res, 'loadbalancerrule')
        rule['members'] = wanted_members_names
        return rule


    def present_lb_rule(self):
        missing_params = []
        for required_params in [
            'algorithm',
            'private_port',
            'public_port',
        ]:
            if not self.module.params.get(required_params):
                missing_params.append(required_params)
        if missing_params:
            self.module.fail_json(msg="missing required arguments: %s" % ','.join(missing_params))

        args = self._get_common_args()
        rule = self.get_rule(**args)
        if rule:
            rule = self._update_lb_rule(rule)
        else:
            rule = self._create_lb_rule(rule)

        if rule:
            rule = self.ensure_tags(resource=rule, resource_type='LoadBalancer')
            rule = self.present_members(rule)
        return rule


    def _create_lb_rule(self, rule):
        self.result['changed'] = True
        if not self.module.check_mode:
            args = self._get_common_args()
            args['algorithm']   = self.module.params.get('algorithm')
            args['privateport'] = self.module.params.get('private_port')
            args['publicport']  = self.module.params.get('public_port')
            args['cidrlist']    = self.module.params.get('cidr')
            args['description'] = self.module.params.get('description')
            res = self.cs.createLoadBalancerRule(**args)
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

            poll_async = self.module.params.get('poll_async')
            if poll_async:
                rule = self.poll_job(res, 'loadbalancer')
        return rule


    def _update_lb_rule(self, rule):
        args                = {}
        args['id']          = rule['id']
        args['algorithm']   = self.module.params.get('algorithm')
        args['description'] = self.module.params.get('description')
        if self.has_changed(args, rule):
            self.result['changed'] = True
            if not self.module.check_mode:
                res = self.cs.updateLoadBalancerRule(**args)
                if 'errortext' in res:
                    self.module.fail_json(msg="Failed: '%s'" % res['errortext'])

                poll_async = self.module.params.get('poll_async')
                if poll_async:
                    rule = self.poll_job(res, 'loadbalancer')
        return rule


    def absent_lb_rule(self):
        args = self._get_common_args()
        rule = self.get_rule(**args)
        if rule:
            self.result['changed'] = True
        if rule and not self.module.check_mode:
            res = self.cs.deleteLoadBalancerRule(id=rule['id'])
            if 'errortext' in res:
                self.module.fail_json(msg="Failed: '%s'" % res['errortext'])
            poll_async = self.module.params.get('poll_async')
            if poll_async:
                res = self._poll_job(res, 'loadbalancer')
        return rule


    def get_result(self, rule):
        super(AnsibleCloudStackLBRule, self).get_result(rule)
        if rule:
            # Bad bad API does not always return int when it should.
            for search_key, return_key in self.returns_to_int.iteritems():
                if search_key in rule:
                    self.result[return_key] = int(rule[search_key])
        return self.result


def main():
    module = AnsibleModule(
        argument_spec = dict(
            name = dict(required=True),
            description = dict(default=None),
            algorithm = dict(choices=['source', 'roundrobin', 'leastconn'], required=False, default='source'),
            private_port = dict(type='int', required=False),
            public_port = dict(type='int', required=False),
            state = dict(choices=['present', 'absent'], default='present'),
            public_ip = dict(required=True, aliases=['ip_address']),
            cidr = dict(required=False),
            project = dict(default=None, required=False),
            open_firewall = dict(choices=BOOLEANS, default=False),
            tags = dict(type='list', aliases=[ 'tag' ], default=None),
            zone = dict(default=None),
            domain = dict(default=None),
            account = dict(default=None),
            members = dict(type='list', aliases=[ 'member' ], default=None),
            poll_async = dict(choices=BOOLEANS, default=True),
            api_key = dict(default=None),
            api_secret = dict(default=None, no_log=True),
            api_url = dict(default=None),
            api_http_method = dict(choices=['get', 'post'], default='get'),
            api_timeout = dict(type='int', default=10),
            api_region = dict(default='cloudstack'),
        ),
        required_together = (
            ['api_key', 'api_secret', 'api_url'],
        ),
        supports_check_mode=True
    )

    if not has_lib_cs:
        module.fail_json(msg="python library cs required: pip install cs")

    try:
        acs_lb_rule = AnsibleCloudStackLBRule(module)

        state = module.params.get('state')
        if state in ['absent']:
            rule = acs_lb_rule.absent_lb_rule()
        else:
            rule = acs_lb_rule.present_lb_rule()

        result = acs_lb_rule.get_result(rule)

    except CloudStackException, e:
        module.fail_json(msg='CloudStackException: %s' % str(e))

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
