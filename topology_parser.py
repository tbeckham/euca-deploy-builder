#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#
import os
import yaml

environment_descriptor = os.getenv('TOPOLOGY')
topo_dict = yaml.load(environment_descriptor)
client_dict = {"default_attributes": {"eucalyptus": {}}}
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


def check_cluster_definition(machine, component, count):
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
    :param count: machine number
    :return:
    """
    if not is_attribute_declared(key="clusters", some_dict=topology):
        topology['clusters'] = {machine.get('cluster-name'): {}}
        topology['clusters'][machine.get('cluster-name')][component] = get_component_ip(machine, count)
    elif machine.get('cluster-name') in topology['clusters'].keys():
        topology['clusters'][machine.get('cluster-name')][component] = get_component_ip(machine, count)
    else:
        topology['clusters'][machine.get('cluster-name')] = {}
        topology['clusters'][machine.get('cluster-name')][component] = get_component_ip(machine, count)
    return


def get_component_ip(machine_dict, count):
    """
    Get ip from machine dict. If an IP is not declared return a string

    :param machine_dict:
    :return: the IP found or "a_node"
    """
    if is_attribute_declared(key='public-ip', some_dict=machine_dict):
        return machine_dict.get('public-ip')
    else:
        return "MACHINE_" + str(count)


def parse_client_topology():
    """
    This will parse the client topology description and build out a euca-deploy compatible yaml for components with
     known IPs.

    :return:
    """
    nodes = {}
    count = 0
    for machine in get_topology():
        count += 1
        for component in machine.get('cloud-components'):
            if component == 'clc':
                topology['clc-1'] = get_component_ip(machine, count)
            elif component == 'cc':
                check_cluster_definition(machine=machine, component='cc-1', count=count)
            elif component == 'sc':
                check_cluster_definition(machine=machine, component='sc-1', count=count)
            elif component == 'walrus':
                topology['walrus'] = get_component_ip(machine, count)
            elif component == 'ufs':
                topology['user-facing'] = [get_component_ip(machine, count)]
            elif component == 'nc':
                if not is_attribute_declared(key="clusters", some_dict=topology):
                    nodes[machine.get('cluster-name')] = [get_component_ip(machine, count)]
                    topology['clusters'] = {machine.get('cluster-name'): {}}
                    topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
                elif machine.get('cluster-name') in topology['clusters'].keys():
                    if not is_attribute_declared(key=machine.get('cluster-name'), some_dict=nodes):
                        nodes[machine.get('cluster-name')] = [get_component_ip(machine, count)]
                    else:
                        nodes[machine.get('cluster-name')].append(machine.get('public-ip'))
                    topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
                else:
                    if not is_attribute_declared(key=machine.get('cluster-name'), some_dict=nodes):
                        nodes[machine.get('cluster-name')] = [get_component_ip(machine, count)]
                    else:
                        nodes[machine.get('cluster-name')].append(get_component_ip(machine, count))
                    topology['clusters'][machine.get('cluster-name')] = {}
                    topology['clusters'][machine.get('cluster-name')]['nodes'] = " ".join(nodes[machine.get('cluster-name')])
    return


def create_client_yml(in_dict, out_file):
    f = open(out_file, 'w')
    f.write(yaml.dump(in_dict))
    f.close()


def create_client_topology():
    """
    populate client information and write to file to be consumed by environment builder

    :return:
    """
    parse_client_topology()
    client_dict["default_attributes"] = {"eucalyptus": {"topology": topology}}
    create_client_yml(in_dict=client_dict, out_file='client.yml')
    return
