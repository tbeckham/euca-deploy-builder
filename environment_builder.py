#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#

import json
import os
import yaml
import topology_parser
import socket


'''
Jenkins ENV Vars
'''
job_id = os.getenv('JOB_ID')
print "DEPLOY JOB ID IS: " + job_id
install_type = os.getenv('SOURCE_OR_PACAKGE_BUILD')
public_ips = os.getenv('PUBLIC_IPS')
euca_source = os.getenv('EUCA_SOURCE')
private_ips = os.getenv('PRIVATE_IPS')
source_branch = os.getenv('SOURCE_BRANCH')
euca2ools_version = os.getenv('EUCA2OOLS_VERSION')
hypervisor = os.getenv('HYPERVISOR')
network_mode = os.getenv('NETWORK')
block_storage_mode = os.getenv('BLOCK_STORAGE')
object_storage_mode = os.getenv('OBJECT_STORAGE')

'''
global vars
'''
default_cluster_name = "one"
parsed_cluster_name = topology_parser.search("cluster-name", topology_parser.get_topology())
client_file = "client.yml"
environment_file = "environment.yml"
user_dict = yaml.load(open(client_file).read())
topo_d = user_dict['default_attributes']['eucalyptus']


def write_json_environment():
    environment_dict = yaml.load(open(environment_file).read())
    filename = 'environment.json'
    with open(filename, 'w') as env_json:
        env_json.write(json.dumps(environment_dict, indent=4,
                                  sort_keys=True, separators=(',', ': ')))
    return


def merge(user, default):
    if isinstance(user, dict) and isinstance(default, dict):
        for k, v in default.iteritems():
            if k not in user:
                user[k] = v
            else:
                user[k] = merge(user[k], v)
    return user


def is_ip(addr):
    # print "addr: ",addr
    """
    determine if value is an IP or not
    :param addr:
    :return: true if value is an IP
    """
    try:
        socket.inet_aton(addr)
        return True
    except socket.error:
        return False


def set_component_ip_info(some_dict):
    """
    Read a dict (in euca-deploy case the topo dict) and find cases where value is not an IP. In such cases, replace
    the string with the value of the environment variable of the same name.

    For euca-deploy, it is expected that topology parser provided a topology with "MACHINE_X" in place of IPs that were
     not known at the start of the job (where "X" is the machine in the reservation). This name corresponds to the
     environment variables specified in machine list reservation returned by make reservation job.

    ie. first host in need of IP will be MACHINE_1, any component specified on that machine will have its IP set to
    the MACHINE_1 environment variable that was provided by make reservation.

    :param some_dict:
    :return:
    """
    for k, v in some_dict.iteritems():
        if isinstance(v, dict):
            set_component_ip_info(v)
        else:
            if k == "nodes":
                node_list = v.split(" ")
                for i in node_list:
                    if not is_ip(i):
                        new_value = i.replace(i, os.getenv(i, "MACHINE"))
                        some_dict[k] = new_value
            elif isinstance(v, list):
                for i in v:
                    if not is_ip(i):
                        new_value = i.replace(i, os.getenv(i, "MACHINE"))
                        some_dict[k][v.index(i)] = new_value
            else:
                if not is_ip(v):
                    new_value = v.replace(v, os.getenv(v, "MACHINE"))
                    some_dict[k] = new_value
    return


def get_component_ip(component, some_dict):
    """
    search topology for CLC and return the IP. This is a HACK right now and is very fragile

    TODO: generify. do not care what dict is passed in just parse it for the key and return value if found. Will need
    to be able to traverse sub dicts too.

    :param component:
    :param some_dict:
    :return:
    """
    for key in some_dict['topology']:
        if key == component:
            return some_dict['topology'][key]


def write_environment_to_file(yaml_dump, outfile):
    f = open(outfile, 'w')
    f.write(yaml_dump)
    f.close()

default = {'description': 'Eucalyptus CI Testing',
           'thrift': {'version': '0.9.1'},
           'name': job_id,
           "default_attributes": {"eucalyptus": {}}}

# Initialize eucalyptus config hash with defaults
eucalyptus = {
    "default-img-url": "http://images.walrus.cloud.qa1.eucalyptus-systems.com:8773/precise-server-cloudimg-amd64-disk1.img",
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

storage_property_prefix = parsed_cluster_name + '.storage.'
if block_storage_mode == 'emc-vnx':
    eucalyptus['system-properties'][storage_property_prefix + 'chapuser'] = 'euca-one'
    eucalyptus['system-properties'][storage_property_prefix + 'ncpaths'] = '10.107.5.1'
    eucalyptus['system-properties'][storage_property_prefix + 'sanhost'] = '10.109.5.1'
    eucalyptus['system-properties'][storage_property_prefix + 'sanpassword'] = 'rdc4msl'
    eucalyptus['system-properties'][storage_property_prefix + 'sanuser'] = 'gadmin'
    eucalyptus['system-properties'][storage_property_prefix + 'scpaths'] = '10.107.5.1'
    eucalyptus['system-properties'][storage_property_prefix + 'storagepool'] = '0'
    eucalyptus['system-properties'][storage_property_prefix + 'clipath'] = '/opt/Navisphere/bin/naviseccli'
elif block_storage_mode == 'netapp':
    eucalyptus['system-properties'][storage_property_prefix + 'chapuser'] = 'euca-one'
    eucalyptus['system-properties'][storage_property_prefix + 'ncpaths'] = '10.107.2.1'
    eucalyptus['system-properties'][storage_property_prefix + 'sanhost'] = '10.109.2.1'
    eucalyptus['system-properties'][storage_property_prefix + 'sanpassword'] = 'zoomzoom'
    eucalyptus['system-properties'][storage_property_prefix + 'sanuser'] = 'root'
    eucalyptus['system-properties'][storage_property_prefix + 'scpaths'] = '10.107.2.1'
elif block_storage_mode == 'netapp-cmode':
    # Cluster mode is the only mode that is differentiated in Jenkins but not in euca
    topo_d['topology']['clusters'][parsed_cluster_name]['storage-backend'] = 'netapp'
    eucalyptus['system-properties'][storage_property_prefix + 'vservername'] = 'euca-vserver'
    eucalyptus['system-properties'][storage_property_prefix + 'chapuser'] = 'euca-one'
    eucalyptus['system-properties'][storage_property_prefix + 'ncpaths'] = '10.107.1.1'
    eucalyptus['system-properties'][storage_property_prefix + 'sanhost'] = '10.109.1.26'
    eucalyptus['system-properties'][storage_property_prefix + 'sanpassword'] = 'netapp123'
    eucalyptus['system-properties'][storage_property_prefix + 'sanuser'] = 'vsadmin'
    eucalyptus['system-properties'][storage_property_prefix + 'scpaths'] = '10.107.1.1'
elif block_storage_mode == 'equallogic':
    eucalyptus['system-properties'][storage_property_prefix + 'chapuser'] = 'euca-one'
    eucalyptus['system-properties'][storage_property_prefix + 'ncpaths'] = '10.107.6.1'
    eucalyptus['system-properties'][storage_property_prefix + 'sanhost'] = '10.109.6.1'
    eucalyptus['system-properties'][storage_property_prefix + 'sanpassword'] = 'zoomzoom'
    eucalyptus['system-properties'][storage_property_prefix + 'sanuser'] = 'grpadmin'
    eucalyptus['system-properties'][storage_property_prefix + 'scpaths'] = '10.107.6.1'

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
eucalyptus.update(repository_mapping[euca_source])

### set all the IP info
set_component_ip_info(topo_d)

# Setup networking
if 'EDGE' == network_mode:
    config_json = {"InstanceDnsServers": [get_component_ip(component="clc-1", some_dict=topo_d)],
                   "Clusters": [{"Subnet": {"Subnet": "10.111.0.0",
                                            "Netmask": "255.255.0.0",
                                            "Name": "10.111.0.0",
                                            "Gateway": "10.111.0.1"},
                                 "PrivateIps": edge_priv,
                                 "Name": parsed_cluster_name}],
                   "PublicIps": edge_pubs}
    eucalyptus['network']['nc-router'] = 'N'
    eucalyptus['network']['config-json'] = config_json
else:
    ### Managed, Managed-No-VLAN
    eucalyptus['network']['public-interface'] = 'em1'
    eucalyptus['network']['private-interface'] = 'em1'
    eucalyptus['network']['public-ips'] = public_ips
    if network_mode == 'MANAGED':
        eucalyptus['system-properties']['cloud.network.global_min_network_tag'] = "512"
        eucalyptus['system-properties']['cloud.network.global_max_network_tag'] = "639"

### output env to console
print "Generated Environment\n"
print yaml.dump(merge(user_dict, default), default_flow_style=False)


### write generated euca-deploy yaml to file
write_environment_to_file(yaml_dump=yaml.dump(merge(user_dict, default), default_flow_style=False),
                          outfile=environment_file)
