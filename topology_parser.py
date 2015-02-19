#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#
import os
import yaml

environment_descriptor = os.getenv('TOPOLOGY')
job_id = os.getenv('JOB_ID')
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
    """
    Three scenarios can exist here:
     1) No cluster definition in topology
     - create cluster dict and dict for specific cluster name
     2) Cluster definition exists but not this cluster name
     - create dict for new cluster name
     3) Cluster exists in topology dict and the same name cluster exists
     - update dict
    :param machine: dict of machine description
    :param component: cc-1 or sc-1
    :return:
    """
    if not is_attribute_declared(key="clusters", some_dict=topology):
        topology['clusters'] = {machine.get('cluster-name'): {}}
        topology['clusters'][machine.get('cluster-name')][component] = machine.get('public-ip')
    elif machine.get('cluster-name') in topology['clusters'].keys():
        topology['clusters'][machine.get('cluster-name')][component] = machine.get('public-ip')
    else:
        topology['clusters'][machine.get('cluster-name')] = {}
        topology['clusters'][machine.get('cluster-name')][component] = machine.get('public-ip')
    return


def create_client_topology():
    """
    This will parse the client topology description and build out a euca-deploy compatible yaml for components with
     known IPs.

    :return:
    """
    nodes = {}
    node_ip = 0
    for machine in get_topology():
        for component in machine.get('cloud-components'):
            if component == 'clc':
                topology['clc-1'] = machine.get('public-ip')
            elif component == 'cc':
                check_cluster_definition(machine=machine, component='cc-1')
            elif component == 'sc':
                check_cluster_definition(machine=machine, component='sc-1')
            elif component == 'walrus':
                topology['walrus'] = machine.get('public-ip')
            elif component == 'ufs':
                topology['user-facing'] = [machine.get('public-ip')]
            elif component == 'nc':
                if is_attribute_declared(key="public-ip", some_dict=machine):
                    if not is_attribute_declared(key="clusters", some_dict=topology):
                        nodes[machine.get('cluster-name')] = [machine.get('public-ip')]
                        topology['clusters'] = {machine.get('cluster-name'): {}}
                        topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
                    elif machine.get('cluster-name') in topology['clusters'].keys():
                        if not is_attribute_declared(key=machine.get('cluster-name'), some_dict=nodes):
                            nodes[machine.get('cluster-name')] = [machine.get('public-ip')]
                        else:
                            nodes[machine.get('cluster-name')].append(machine.get('public-ip'))
                        topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
                    else:
                        if not is_attribute_declared(key=machine.get('cluster-name'), some_dict=nodes):
                            nodes[machine.get('cluster-name')] = [machine.get('public-ip')]
                        else:
                            nodes[machine.get('cluster-name')].append(machine.get('public-ip'))
                        topology['clusters'][machine.get('cluster-name')] = {}
                        topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
                else:
                    if not is_attribute_declared(key="clusters", some_dict=topology):
                        nodes[machine.get('cluster-name')] = ["a_node"]
                        topology['clusters'] = {machine.get('cluster-name'): {}}
                        topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
                    elif machine.get('cluster-name') in topology['clusters'].keys():
                        if not is_attribute_declared(key=machine.get('cluster-name'), some_dict=nodes):
                            nodes[machine.get('cluster-name')] = ["a_node"]
                        else:
                            nodes[machine.get('cluster-name')].append("a_node")
                        topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
                    else:
                        if not is_attribute_declared(key=machine.get('cluster-name'), some_dict=nodes):
                            nodes[machine.get('cluster-name')] = ["a_node"]
                        else:
                            nodes[machine.get('cluster-name')].append("a_node")
                        topology['clusters'][machine.get('cluster-name')] = {}
                        topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
    return


def create_client_yml(in_dict, out_file):
    f = open(out_file, 'w')
    f.write(yaml.dump(in_dict))
    f.close()

# populate known information and write to file to be consumed by environment builder
create_client_topology()
client_dict["default_attributes"] = {"eucalyptus": {"topology": topology}}
create_client_yml(in_dict=client_dict, out_file='client.yml')