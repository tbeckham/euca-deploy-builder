#!/usr/bin/python
#
# Author: Tony Beckham tony.beckham@hp.com
#

import os
import yaml


environment_descriptor= os.getenv('TOPOLOGY')
topo_dict = yaml.load(environment_descriptor)
num_hosts=len(topo_dict['machine-topology'])
f = open('build.properties', 'w')
f.write("NUM_HOSTS="+ str(num_hosts))

print "\nThis is the determined topology"
for i, v in enumerate(topo_dict['machine-topology']):
    print v['cloud-components']

print "\nReserving " + str(num_hosts) + " hosts\n"
