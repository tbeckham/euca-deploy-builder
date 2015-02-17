#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#

import json
import os
import yaml

network_mode = "EDGE"
default_cluster_name = "one"
client_file = "user-topo.yml"
environment_file = "environment.yml"
user_dict = yaml.load(open(client_file).read())

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


# Setup networking
if 'EDGE' == network_mode:
    config_json = {"InstanceDnsServers": ["frontend"],
                   "Clusters": [{"Subnet": {"Subnet": "10.111.0.0",
                                            "Netmask": "255.255.0.0",
                                            "Name": "10.111.0.0",
                                            "Gateway": "10.111.0.1"},
                                 "PrivateIps": "edge_priv",
                                 "Name": default_cluster_name}],
                   "PublicIps": "edge_pubs"}
    eucalyptus['network']['nc-router'] = 'N'
    eucalyptus['network']['config-json'] = config_json

print "Generated Environmentv\n"
print yaml.dump(merge(user_dict, default), default_flow_style=False)
