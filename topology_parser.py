#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#
import os
import yaml


# environment_descriptor= os.getenv('TOPOLOGY')
# job_id= os.getenv('JOB_ID')
default_cluster_name = "one"

# simulate jenkins env vars
job_id = "tony-23"
environment_descriptor = '''
version: 4.1
machine-topology:
  - cloud-components:
    - clc
  - cloud-components:
    - cc
    cluster-name: one
    public-ip: 192.168.0.2
  - cloud-components:
    - sc
    cluster-name: two
    public-ip: 192.168.0.10
  - cloud-components:
    - nc
    public-ip: 192.168.0.4
    cluster-name: one
  - cloud-components:
    - nc
    public-ip: 192.168.0.3
    cluster-name: one
  - cloud-components:
    - walrus
  - cloud-components:
    - ufs
    public-ip: 192.168.0.1
'''

topo_dict = yaml.load(environment_descriptor)
client_dict = {'name': job_id, "default_attributes": {"eucalyptus": {}}}
topology = {}

def set_number_hosts_to_reserve():
    num_hosts = 0
    for machine in get_topology():
        if not is_attribute_declared(key="public-ip", some_dict=machine):
            num_hosts += 1
    f = open('build.properties', 'w')
    f.write("NUM_HOSTS=" + str(num_hosts) + "\n")
    f.close()
    print "\nReserving " + str(num_hosts) + " hosts\n"
    return


def get_topology():
    machine_details = []
    for i, v in enumerate(topo_dict['machine-topology']):
        machine_details.append(topo_dict['machine-topology'][i])
    return machine_details


def print_topology():
    print "\nThis is the determined topology"
    for i, v in enumerate(topo_dict['machine-topology']):
        print v['cloud-components']
    return


def is_attribute_declared(key, some_dict):
    if key in some_dict.keys():
        return True
    else:
        return False


def check_cluster_definition(machine, component):
    if not is_attribute_declared(key="clusters", some_dict=topology):
        topology['clusters'] = {machine.get('cluster-name'): {}}
        topology['clusters'][machine.get('cluster-name')][component] = machine.get('public-ip')
    else:
        if machine.get('cluster-name') in topology['clusters'].keys():
            print "DEBUG: cluster already exists, updating"
            topology['clusters'][machine.get('cluster-name')][component] = machine.get('public-ip')
        else:
            print "DEBUG: need a new cluster"
            topology['clusters'] = {machine.get('cluster-name'): {}}
            topology['clusters'][machine.get('cluster-name')][component] = machine.get('public-ip')
    return


def set_known_ips():
    nodes={default_cluster_name: []}
    for machine in get_topology():
        if is_attribute_declared(key="public-ip", some_dict=machine):
            for component in machine.get('cloud-components'):
                if component == 'clc':
                    topology['clc-1'] = str(machine.get('public-ip'))
                elif component == 'cc':
                    check_cluster_definition(machine=machine, component='cc-1')
                elif component == 'sc':
                    check_cluster_definition(machine=machine, component='sc-1')
                elif component == 'nc':
                    if not is_attribute_declared(key="clusters", some_dict=topology):
                        topology['clusters'] = {machine.get('cluster-name'): {}}
                        topology['clusters'][machine.get('cluster-name')]['nodes'] = machine.get('public-ip')
                    else:
                        if not is_attribute_declared(key=machine.get('cluster-name'), some_dict=nodes):
                            nodes[machine.get('cluster-name')].append(machine.get('public-ip'))
                            print "DEBUG: node dict = " + str(nodes)
                            topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
                elif component == 'walrus':
                    topology['walrus'] = str(machine.get('public-ip'))
                elif component == 'ufs':
                    topology['user-facing'] = [str(machine.get('public-ip'))]
    return


def create_client_yml():
    f = open('client.yml', 'w')
    f.write(yaml.dump(client_dict))
    f.close()


print"\n"
# for machine in get_topology():
# print machine
set_known_ips()
client_dict["default_attributes"] = {"eucalyptus": {"topology": topology}}

print "\n"
print yaml.dump(client_dict)

