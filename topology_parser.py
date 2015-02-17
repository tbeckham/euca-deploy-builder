#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#

import json
import os
import yaml


def write_json_environment():
    environment_dict = yaml.load(open(environment_decriptor).read())
    filename = 'environment.json'
    with open(filename, 'w') as env_json:
        env_json.write(json.dumps(environment_dict, indent=4,
                                  sort_keys=True, separators=(',', ': ')))
    return

def determine_number_of_hosts(environment_yml):
    topo_dict = yaml.load(open(environment_yml).read())
    num_host = len(topo_dict['machine-topology'])
    return num_host


environment_decriptor = os.getenv('TOPOLOGY')
os.getenv('NUM_HOSTS', determine_number_of_hosts(environment_decriptor))

topo_dict = yaml.load(open(environment_decriptor).read())

print "This is the determined topology"
for i, v in enumerate(topo_dict['machine-topology']):
    print v['cloud-components']

print "\nWe need " + str(determine_number_of_hosts(environment_decriptor)) + " hosts\n"
