#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#

import json
import os
import yaml
import topology_parser

'''
Jenkins ENV Vars
'''
# job_id = os.getenv('JOB_ID')
# print "DEPLOY JOB ID IS: " + job_id
# install_type = os.getenv('SOURCE_OR_PACAKGE_BUILD')
# frontend = os.getenv('MACHINE_1')
# public_ips = os.getenv('PUBLIC_IPS')
# euca_source = os.getenv('EUCA_SOURCE')
# private_ips = os.getenv('PRIVATE_IPS')
# source_branch = os.getenv('SOURCE_BRANCH')
# euca2ools_version = os.getenv('EUCA2OOLS_VERSION')
# hypervisor = os.getenv('HYPERVISOR')
# network_mode = os.getenv('NETWORK')
# block_storage_mode = os.getenv('BLOCK_STORAGE')
# object_storage_mode = os.getenv('OBJECT_STORAGE')

network_mode = "EDGE"
default_cluster_name = "one"
client_file = "client.yml"
environment_file = "environment.yml"
user_dict = yaml.load(open(client_file).read())

#simulate jenkins env vars
euca_source = "testing"

def write_json_environment():
    environment_dict = yaml.load(open(environment_file).read())
    filename = 'environment.json'
    with open(filename, 'w') as env_json:
        env_json.write(json.dumps(environment_dict, indent=4,
                                  sort_keys=True, separators=(',', ': ')))
    return

def merge(user, default):
    if isinstance(user,dict) and isinstance(default,dict):
        for k,v in default.iteritems():
            if k not in user:
                user[k] = v
            else:
                user[k] = merge(user[k],v)
    return user

default = {'description': 'Eucalyptus CI Testing',
           'thrift': {'version': '0.9.1'}}

# Initialize eucalyptus config hash with defaults
eucalyptus = {"default-img-url": "http://images.walrus.cloud.qa1.eucalyptus-systems.com:8773/precise-server-cloudimg-amd64-disk1.img",
              'install-load-balancer': 'true',
              'install-imaging-worker': 'true',
              'network': {'mode': "EDGE",
                          'bridge-interface': 'br0',
                          'public-interface': 'br0',
                          'private-interface': 'br0',
                          'bridged-nic': 'em1'},
              'nc': {"max-cores": 32},
              "source-repo": "ssh://repo-euca@git.eucalyptus-systems.com/internal",
              "init-script-url": "http://git.qa1.eucalyptus-systems.com/qa-repos/eucalele/raw/master/scripts/network-interfaces.sh",
              "log-level": "DEBUG",
              "yum-options": "--nogpg",
              "system-properties": {'cloudformation.url_domain_whitelist': '*s3.amazonaws.com,*qa1.eucalyptus-systems.com'}
}

default["default_attributes"] = {"eucalyptus": eucalyptus}

repository_mapping = {'testing': {
    'eucalyptus-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/eucalyptus-devel/centos/6/x86_64/',
    'enterprise-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/enterprise-devel/centos/6/x86_64/',
    'euca2ools-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/euca2ools-devel/centos/6/x86_64/'},
                       'maint/4.0/testing': {
                           'eucalyptus-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/eucalyptus-4.0/centos/6/x86_64/',
                           'enterprise-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/enterprise-4.0/centos/6/x86_64/',
                           'euca2ools-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/euca2ools-3.1/centos/6/x86_64/'},
                       'maint-4.1': {
                           'eucalyptus-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/eucalyptus-4.1/centos/6/x86_64/',
                           'enterprise-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/enterprise-4.1/centos/6/x86_64/',
                           'euca2ools-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/euca2ools-3.2/centos/6/x86_64/'}
}
default = dict(default.items() + repository_mapping[euca_source].items())

# Setup networking
if 'EDGE' == network_mode:
    config_json = {"InstanceDnsServers": ["CLC-IP"],
                   "Clusters": [{"Subnet": {"Subnet": "10.111.0.0",
                                            "Netmask": "255.255.0.0",
                                            "Name": "10.111.0.0",
                                            "Gateway": "10.111.0.1"},
                                 "PrivateIps": "edge_priv",
                                 "Name": default_cluster_name}],
                   "PublicIps": "edge_pubs"}
    eucalyptus['network']['nc-router'] = 'N'
    eucalyptus['network']['config-json'] = config_json

print "Generated Environment\n"
print yaml.dump(merge(user_dict, default), default_flow_style=False)

# topology_parser.get_topology()
# topology_parser.print_topology()
# topology_parser.set_number_hosts_to_reserve()