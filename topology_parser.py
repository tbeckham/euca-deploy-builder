#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#
import os
import yaml


# environment_descriptor= os.getenv('TOPOLOGY')
# job_id= os.getenv('JOB_ID')

#simulate jenkins env vars
job_id= "tony-23"
environment_descriptor='''
version: 4.1
machine-topology:
  - cloud-components:
    - clc
  - cloud-components:
    - cc
    - sc
    cluster-name: one
  - cloud-components:
    - nc
    cluster-name: one
  - cloud-components:
    - nc
    cluster-name: one
  - cloud-components:
    - walrus
  - cloud-components:
    - ufs
    public-ip: 192.168.0.1
'''

topo_dict = yaml.load(environment_descriptor)
client_dict={'default_attributes':
                 {'eucalyptus':
                      {'topology':
                           {'clusters':
                                {'one':
                                     {'cc-1': 'CC-IP',
                                      'nodes': 'NC-IP',
                                      'sc-1': 'SC-IP'}},
                            'clc-1': 'CLC-IP',
                            'walrus': 'WALRUS-IP',
                            'user-facing': ['UFS-IP']}}},
             'name': job_id}

def set_number_hosts_to_reserve():
    num_hosts = 0
    for machine in get_topology():
        if not is_attribute_decalared(key="public-ip", dict=machine):
            num_hosts += 1
    f = open('build.properties', 'w')
    f.write("NUM_HOSTS="+ str(num_hosts) + "\n")
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

def is_attribute_decalared(key, dict):
    if key in dict.keys():
        return True
    else:
        return False

def create_client_yml():
    f = open('client.yml', 'w')
    f.write(yaml.dump(client_dict))
    f.close()

print"\n"
# for machine in get_topology():
#     print machine