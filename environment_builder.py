#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#

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
                        node_list[node_list.index(i)] = os.getenv(i, "MACHINE")
                        some_dict[k] = ' '.join(node_list)
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
           'name': job_id,
           "default_attributes": {"eucalyptus": {}}}

# Initialize eucalyptus config hash with defaults
eucalyptus = {
    'install-type': install_type,
    'source-branch': source_branch,
    "default-img-url":
        "http://images.walrus.cloud.qa1.eucalyptus-systems.com:8773/precise-server-cloudimg-amd64-disk1.img",
    'install-load-balancer': 'true',
    'install-imaging-worker': 'true',
    'network': {'mode': "EDGE",
                'bridge-interface': 'br0',
                'public-interface': 'br0',
                'private-interface': 'br0',
                'bridged-nic': 'em1'},
    'nc': {"max-cores": 32},
    "source-repo": "ssh://repo-euca@git.eucalyptus-systems.com/internal",
    "init-script-url":
        "http://git.qa1.eucalyptus-systems.com/qa-repos/eucalele/raw/master/scripts/network-interfaces.sh",
    "log-level": "DEBUG",
    "yum-options": "--nogpg",
    "system-properties": {'cloudformation.url_domain_whitelist': '*s3.amazonaws.com,*qa1.eucalyptus-systems.com'}
}
default["default_attributes"] = {"eucalyptus": eucalyptus}

# set all the IP info
set_component_ip_info(topo_d)

for cluster_name in topology_parser.get_cluster_names():
    storage_property_prefix = cluster_name + '.storage.'
    if block_storage_mode == 'emc-vnx':
        topo_d['topology']['clusters'][cluster_name]['storage-backend'] = 'emc-vnx'
        eucalyptus['system-properties'][storage_property_prefix + 'chapuser'] = 'euca-one'
        eucalyptus['system-properties'][storage_property_prefix + 'ncpaths'] = '10.107.5.1'
        eucalyptus['system-properties'][storage_property_prefix + 'sanhost'] = '10.109.5.1'
        eucalyptus['system-properties'][storage_property_prefix + 'sanpassword'] = 'rdc4msl'
        eucalyptus['system-properties'][storage_property_prefix + 'sanuser'] = 'gadmin'
        eucalyptus['system-properties'][storage_property_prefix + 'scpaths'] = '10.107.5.1'
        eucalyptus['system-properties'][storage_property_prefix + 'storagepool'] = '0'
        eucalyptus['system-properties'][storage_property_prefix + 'clipath'] = '/opt/Navisphere/bin/naviseccli'
    elif block_storage_mode == 'netapp':
        topo_d['topology']['clusters'][cluster_name]['storage-backend'] = 'netapp'
        eucalyptus['system-properties'][storage_property_prefix + 'chapuser'] = 'euca-one'
        eucalyptus['system-properties'][storage_property_prefix + 'ncpaths'] = '10.107.2.1'
        eucalyptus['system-properties'][storage_property_prefix + 'sanhost'] = '10.109.2.1'
        eucalyptus['system-properties'][storage_property_prefix + 'sanpassword'] = 'zoomzoom'
        eucalyptus['system-properties'][storage_property_prefix + 'sanuser'] = 'root'
        eucalyptus['system-properties'][storage_property_prefix + 'scpaths'] = '10.107.2.1'
    elif block_storage_mode == 'netapp-cmode':
        topo_d['topology']['clusters'][cluster_name]['storage-backend'] = 'netapp'
        eucalyptus['system-properties'][storage_property_prefix + 'vservername'] = 'euca-vserver'
        eucalyptus['system-properties'][storage_property_prefix + 'chapuser'] = 'euca-one'
        eucalyptus['system-properties'][storage_property_prefix + 'ncpaths'] = '10.107.1.1'
        eucalyptus['system-properties'][storage_property_prefix + 'sanhost'] = '10.109.1.26'
        eucalyptus['system-properties'][storage_property_prefix + 'sanpassword'] = 'netapp123'
        eucalyptus['system-properties'][storage_property_prefix + 'sanuser'] = 'vsadmin'
        eucalyptus['system-properties'][storage_property_prefix + 'scpaths'] = '10.107.1.1'
    elif block_storage_mode == 'equallogic':
        topo_d['topology']['clusters'][cluster_name]['storage-backend'] = 'equallogic'
        eucalyptus['system-properties'][storage_property_prefix + 'chapuser'] = 'euca-one'
        eucalyptus['system-properties'][storage_property_prefix + 'ncpaths'] = '10.107.6.1'
        eucalyptus['system-properties'][storage_property_prefix + 'sanhost'] = '10.109.6.1'
        eucalyptus['system-properties'][storage_property_prefix + 'sanpassword'] = 'zoomzoom'
        eucalyptus['system-properties'][storage_property_prefix + 'sanuser'] = 'grpadmin'
        eucalyptus['system-properties'][storage_property_prefix + 'scpaths'] = '10.107.6.1'
    elif block_storage_mode == 'ceph-rbd':
        topo_d['topology']['clusters'][cluster_name]['storage-backend'] = 'ceph-rbd'
        eucalyptus['system-properties'][
            storage_property_prefix + 'cephkeyringfile'] = '/etc/ceph/ceph.client.qauser.keyring'
        eucalyptus['system-properties'][storage_property_prefix + 'cephuser'] = 'qauser'
        eucalyptus['system-properties'][storage_property_prefix + 'cephconfigfile'] = '/etc/ceph/ceph.conf'
        eucalyptus['system-properties'][storage_property_prefix + 'cephsnapshotpools'] = 'rbd'
        eucalyptus['system-properties'][storage_property_prefix + 'cephvolumepools'] = 'rbd'
        topo_d['topology']['clusters'][cluster_name]['ceph_cluster'] = {"ceph_user": "qauser",
                                                                        "keyring": {
                                                                            "key": "AQAkAP1TYLICHRAAWON3vIDgMgf6VrsawQmTvQ=="},
                                                                        "global": {
                                                                            "osd_pool_default_pgp_num": "128",
                                                                            "auth_service_required": "cephx",
                                                                            "osd_pool_default_size": 3,
                                                                            "filestore_xattr_use_omap": True,
                                                                            "auth_client_required": "cephx",
                                                                            "osd_pool_default_pg_num": 128,
                                                                            "auth_cluster_required": "cephx",
                                                                            "mon_host": "10.111.5.185",
                                                                            "mon_initial_members": "g-19-05",
                                                                            "fsid": "ea4b07ca-ebf9-45a9-be9a-47428b810d84"
                                                                        },
                                                                        "mon": {
                                                                            "mon host": "g-19-05,d-04,d-05",
                                                                            "mon addr": "10.111.5.185:6789,10.111.5.188:6789,"
                                                                                        "10.111.5.189:6789"
                                                                        }}
    else:
        topo_d['topology']['clusters'][cluster_name]['storage-backend'] = 'das'
        topo_d['topology']['clusters'][cluster_name]['das-device'] = 'vg01'

if object_storage_mode == "riakcs":
    topo_d['topology']['riakcs'] = {
                              "admin-name": job_id,
                              "admin-email": job_id + "@euca-qa.com",
                              "endpoint": "10.111.5.79",
                              "port": 80,
                              "access-key": "",
                              "secret-key": ""
                          }
    eucalyptus['system-properties']['objectstorage.dogetputoncopyfail'] = 'true'

repository_mapping = {'master': {
    'eucalyptus-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/eucalyptus-devel/centos/6/x86_64/',
    'enterprise-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/enterprise-devel/centos/6/x86_64/',
    'euca2ools-repo': 'http://packages.release.eucalyptus-systems.com/yum/tags/euca2ools-devel/centos/6/x86_64/'},
                      'maint-4.0': {
                          'eucalyptus-repo':
                              'http://packages.release.eucalyptus-systems.com/yum/tags/eucalyptus-4.0/centos/6/x86_64/',
                          'enterprise-repo':
                              'http://packages.release.eucalyptus-systems.com/yum/tags/enterprise-4.0/centos/6/x86_64/',
                          'euca2ools-repo':
                              'http://packages.release.eucalyptus-systems.com/yum/tags/euca2ools-3.1/centos/6/x86_64/'},
                      'maint-4.1': {
                          'eucalyptus-repo':
                              'http://packages.release.eucalyptus-systems.com/yum/tags/eucalyptus-4.1/centos/6/x86_64/',
                          'enterprise-repo':
                              'http://packages.release.eucalyptus-systems.com/yum/tags/enterprise-4.1/centos/6/x86_64/',
                          'euca2ools-repo':
                              'http://packages.release.eucalyptus-systems.com/yum/tags/euca2ools-3.2/centos/6/x86_64/'}
}
eucalyptus.update(repository_mapping[euca_source])

# Setup networking
if 'EDGE' == network_mode:
    parsed_public_ips = public_ips.replace(" ", "").split(',')
    edge_pubs = parsed_public_ips[0:len(parsed_public_ips) / 2]
    edge_priv = parsed_public_ips[len(parsed_public_ips) / 2:len(parsed_public_ips)]
    config_json = {"InstanceDnsServers": [get_component_ip(component="clc-1", some_dict=topo_d)],
                   "Mode": "EDGE",
                   "Clusters": [],
                   "PublicIps": edge_pubs}
    for cluster in topology_parser.get_cluster_names():
        cluster_def = {"Subnet": {"Subnet": "10.111.0.0",
                                  "Netmask": "255.255.0.0",
                                  "Name": "10.111.0.0",
                                  "Gateway": "10.111.0.1"},
                       "PrivateIps": edge_priv,
                       "Name": cluster}
        config_json["Clusters"].append(cluster_def)
    eucalyptus['network']['nc-router'] = 'N'
    eucalyptus['network']['config-json'] = config_json
elif 'VPC' in network_mode:
    # Setup Midokura config
    frontend = get_component_ip(component="clc-1", some_dict=topo_d)
    eucalyptus['network']['mode'] = 'VPCMIDO'
    machine_1_hostname = socket.gethostbyaddr(frontend)[0]
    midolman_host_mapping = {machine_1_hostname: frontend}
    for cluster_name in topology_parser.get_cluster_names():
        for k, v in topo_d['topology']['clusters'][cluster_name].iteritems():
            if k == "nodes":
                node_list = v.split(" ")
                for node in node_list:
                    node_hostname = socket.gethostbyaddr(node)[0]
                    midolman_host_mapping[node_hostname] = node
    machine_1_octets = frontend.split('.')
    local_as = 64512 + 255 * int(machine_1_octets[2]) + int(machine_1_octets[3])
    mido_gw_ip = "10.116." + str(int(machine_1_octets[2]) + 128) + "." + machine_1_octets[3]
    midokura_config = {'repo-username': 'eucalyptus',
                       'repo-password': '8yU8Pj6h',
                       'yum-options': '--nogpg',
                       'zookeepers': ["{0}:2181".format(frontend)],
                       'cassandras': ["{0}".format(frontend)],
                       'initial-tenant': 'euca_tenant_1',
                       'midonet-api-url': "http://{0}:8080/midonet-api".format(frontend),
                       'midolman-host-mapping': midolman_host_mapping,
                       'bgp-peers': [{"router-name": "eucart",
                                      "port-ip": mido_gw_ip,
                                      "remote-as": 65000,
                                      "peer-address": "10.116.133.173",
                                      "local-as": local_as,
                                      "route": public_ips + "/24"}]
                       }
    default['default_attributes']['midokura'] = midokura_config
    pub_ip_octets = public_ips.split('.')
    last_pub_ip = pub_ip_octets[0] + '.' + pub_ip_octets[1] + '.' + pub_ip_octets[2] + '.' + '254'
    # Setup config JSON
    config_json = {'Mode': 'VPCMIDO',
                   'PublicIps': [public_ips + '-' + last_pub_ip],
                   'InstanceDnsServers': [frontend],
                   # This is the new way to configure MIDO
                   "Mido": {
                       "EucanetdHost": machine_1_hostname,
                       "GatewayHost": machine_1_hostname,
                       "GatewayIP": mido_gw_ip,
                       "GatewayInterface": "em1.116",
                       "PublicNetworkCidr": "10.116.128.0/17",
                       "PublicGatewayIP": "10.116.133.173"
                   }
                   }
    eucalyptus[
        "post-script-url"] = "http://git.qa1.eucalyptus-systems.com/qa-repos/eucalele/raw/master/scripts/midonet_post.sh"
    eucalyptus['network']['config-json'] = config_json
elif ('MANAGED-NOVLAN' == network_mode) or ('MANAGED' == network_mode):
    eucalyptus['network']['mode'] = network_mode
    managed_network = {"ManagedSubnet": {"Subnet": "172.16.0.0",
                                         "Netmask": "255.255.0.0"}}
    if network_mode == 'MANAGED':
        managed_network['ManagedSubnet'].update({"MinVlan": "512", "MaxVlan": "639"})
    eucalyptus['network']['public-interface'] = 'em1'
    eucalyptus['network']['private-interface'] = 'em1'
    config_json = {"InstanceDnsServers": [get_component_ip(component="clc-1", some_dict=topo_d)],
                   "Mode": network_mode,
                   "Clusters": [],
                   "PublicIps": public_ips.replace(" ", "").split(',')}
    for cluster in topology_parser.get_cluster_names():
        cluster_def = {"Name": cluster, "MacPrefix": "d0:0d"}
        config_json["Clusters"].append(cluster_def)
        config_json.update(managed_network)
    eucalyptus['network']['nc-router'] = 'N'
    eucalyptus['network']['config-json'] = config_json

# output env to console
print "Generated Environment\n"
print yaml.dump(merge(user_dict, default), default_flow_style=False)

# write generated euca-deploy yaml to file
write_environment_to_file(yaml_dump=yaml.dump(merge(user_dict, default), default_flow_style=False),
                          outfile=environment_file)

# write Eutester Config to workspace
config_data = ''
config_data = config_data + 'NETWORK\t' + network_mode + '\n'
config_data = config_data + topo_d['topology']['clc-1'] + '\tCENTOS' + '\t6.5' + '\t64' + '\tREPO' + '\t[CLC]' + '\n'
if object_storage_mode == "walrus":
    config_data = config_data + topo_d['topology']['walrus'] + '\tCENTOS' + '\t6.5' + '\t64' + '\tREPO' + '\t[WS]' + '\n'

clusters = 0
for cluster_name in topo_d['topology']['clusters'].keys():
    config_data = config_data + topo_d['topology']['clusters'][cluster_name][
        'cc-1'] + '\tCENTOS' + '\t6.5' + '\t64' + '\tREPO' + '\t[CC0' + str(clusters) + ']' + '\n'
    config_data = config_data + topo_d['topology']['clusters'][cluster_name][
        'sc-1'] + '\tCENTOS' + '\t6.5' + '\t64' + '\tREPO' + '\t[SC0' + str(clusters) + ']' + '\n'
    for k, v in topo_d['topology']['clusters'][cluster_name].iteritems():
        if k == "nodes":
            node_list = v.split(" ")
            for node in node_list:
                config_data = config_data + node + '\tCENTOS' + '\t6.5' + '\t64' + '\tREPO' + '\t[NC0' + str(clusters) + ']' + '\n'
    clusters += 1

with open('config_data', 'w') as data:
    data.write(config_data)

print config_data
