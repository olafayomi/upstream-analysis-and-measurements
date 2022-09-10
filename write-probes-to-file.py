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
import argparse
import json
from pathlib import Path


if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Write list of probes in batch of 300',
            usage='%(prog)s [-i msm_and_probe_list]')

    argParser.add_argument('-i', dest='msm_probes',
                           help='JSON file of all filtered measurements and probes',
                           default='/scratch/probe-list/ping-measurements/eu-probes-filtered-by-avg-rtt.json')

    argParser.add_argument('-o', dest='probelistname',
                           help='Directory to write probe list',
                           type=str,
                           default='/scratch/probe-list/ping-measurements/avg-rtt-valid-probes')

    args = argParser.parse_args()

    path = Path(args.msm_probes)

    outdir = Path(args.probelistname)

    if path.is_file() is False:
        print("%s does not exist!!!" % args.msm_probes)
        sys.exit(-1)

    if outdir.is_dir() is False:
        print("%s directory does not exist!!!" % args.probelistname)
        sys.exit(-1)

    with open(args.msm_probes, 'r') as msmprobesj:
        msm_probes = json.load(msmprobesj)

    probes = []

    for msm, probe_list in msm_probes.items():
        for probe in probe_list:
            probes.append(str(probe))
    
    if len(probes) > 300:
        n = 300
        for i in range(0, len(probes)+1, n):
            print(i)
            print(probes[i])
            probe_list_out = ",".join(probes[i:i+n])
            filename = args.probelistname+'/'+'avg-rtt-valid-probes-'+str(i+1)
            with open(filename, "w") as txt:
                txt.write(probe_list_out)
