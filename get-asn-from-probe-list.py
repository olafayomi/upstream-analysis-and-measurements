#!/usr/bin/env python


# Copyright (c) 2020, WAND Network Research Group
#                     Department of Computer Science
#                     University of Waikato
#                     Hamilton
#                     New Zealand
#
# Author Dimeji Fayomi (oof1@students.waikato.ac.nz)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330,
# Boston,  MA 02111-1307  USA

import json
from pprint import pprint
import requests

def getProbeInfo(probe_id):
    url = "https://atlas.ripe.net/api/v2/probes/"+str(probe_id)+"/"
    resp = requests.get(url)
    data = resp.json()
    return data


if __name__ == "__main__":

    with open('/scratch/probe-list/ping-measurements/Blizzard-probe-rtt-list.json', 'r') as f:
        blizzard_probe_list = json.load(f)



    with open('/scratch/probe-list/ping-measurements/Ubisoft-probe-rtt-list.json', 'r') as f:
        ubisoft_probe_list = json.load(f)

    

    with open('/scratch/probe-list/ping-measurements/Valve-probe-rtt-list.json', 'r') as f:
        valve_probe_list = json.load(f)

    print(type(blizzard_probe_list))
    probes = set()
    for prb in blizzard_probe_list:
        (prb_id, msms), = prb.items()
        probes.add(prb_id)

    for prb in ubisoft_probe_list:
        (prb_id, msms), = prb.items()
        probes.add(prb_id)

    for prb in valve_probe_list:
        (prb_id, msms), = prb.items()
        probes.add(prb_id)

    print("Total number of probes used for measurements to the three servers: %s" % len(probes))
    prb_to_asn = {}
    for prb_id in probes:
        prb_info = getProbeInfo(prb_id)
        prb_asn = prb_info["asn_v4"]
        prb_to_asn[prb_id] = prb_asn

   
    blizzard_origin_asns = set()
    for prb in blizzard_probe_list:
        (prb_id, msms), = prb.items()
        blizzard_origin_asns.add(prb_to_asn[prb_id])

    print("Probes in measurement to blizzard are distributed across: %s ASNs" % len(blizzard_origin_asns))


    ubisoft_origin_asns = set()
    for prb in ubisoft_probe_list:
        (prb_id, msms), = prb.items()
        ubisoft_origin_asns.add(prb_to_asn[prb_id])

    print("Probes in measurement to ubisoft are distributed across: %s ASNs" % len(ubisoft_origin_asns))
    
    valve_origin_asns = set()
    for prb in valve_probe_list:
        (prb_id, msms), = prb.items()
        valve_origin_asns.add(prb_to_asn[prb_id])

    print("Probes in measurement to valve are distributed across: %s ASNs" % len(valve_origin_asns))
   
