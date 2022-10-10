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

import sys
import requests
import argparse
import json
from pprint import pprint
from pathlib import Path


def getResults(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    mresp = requests.get(url)
    data = mresp.json()
    res_url = data['result']
    res_data = requests.get(res_url)
    results = res_data.json()
    return results


if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Excluded lists of probes',
            usage='%(prog)s [-i msm_id]')

    argParser.add_argument('-i', dest='msm',
                           help='''measurement id''',
                           type=int,
                           default=44243938)

    argParser.add_argument('-b', dest='probelist',
                           help='''probe list in patch''',
                           type=str,
                           default='/scratch/probe-list/ping-measurements/avg-rtt-valid-probes/avg-rtt-valid-probes-601')

    argParser.add_argument('-o', dest='notmeasured',
                           help='''probe list not measured''',
                           type=str,
                           default='/scratch/probe-list/ping-measurements/avg-rtt-valid-probes')


    args = argParser.parse_args()

    path = Path(args.probelist) 
    outdir = Path(args.notmeasured)

    if path.is_file() is False: 
        print("%s does not exist!!!" % args.probelist)
        sys.exit(-1)

    if outdir.is_dir() is False:
        print("%s directory does not exist!!!" % args.notmeasured)
        sys.exit(-1)

    results = getResults(args.msm) 

    probes = set()

    for res in results:
       probes.add(res['prb_id'])
    
    print("Probes included in msm %s: %s" % (args.msm, len(probes)))
    with open(args.probelist, 'r') as stream:
        cont = stream.read()
        allprobes  = cont.strip().split(',')
        print("List of probes in %s file: %s" % (args.probelist, len(allprobes)))

    unique_set = {*allprobes}
    print("Unique list of porbes in %s file: %s" % (args.probelist, len(unique_set)))

    
    excluded_list = []
    for prb in allprobes: 
        prb_int = int(prb)
        if prb_int not in probes:
            excluded_list.append(prb)

    pprint(excluded_list)
    print(len(excluded_list))


    
