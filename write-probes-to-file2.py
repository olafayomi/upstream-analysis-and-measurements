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

    argParser.add_argument('-i', dest='avg_msm_probes',
                           help='JSON file of all filtered measurements and probes',
                           default='/scratch/probe-list/ping-measurements/probes-for-trace-filtered-by-median-rtt-per-game-provider.json')

    argParser.add_argument('-j', dest='median_msm_probes',
                           help='JSON file of all filtered measurements and probes',
                           default='/scratch/probe-list/ping-measurements/probes-for-trace-filtered-by-median-rtt-per-game-provider.json')
    
    argParser.add_argument('-o', dest='probelistname',
                           help='Directory to write probe list',
                           type=str,
                           default='/scratch/probe-list/trace-measurements/filtered-valid-probes-per-server')

    args = argParser.parse_args()

    path1 = Path(args.avg_msm_probes)
    path2 = Path(args.median_msm_probes)

    outdir = Path(args.probelistname)

    if path1.is_file() is False:
        print("%s does not exist!!!" % args.avg_msm_probes)
        sys.exit(-1)

    if path2.is_file() is False:
        print("%s does not exist!!!" % args.median_msm_probes)
        sys.exit(-1)

    if outdir.is_dir() is False:
        print("%s directory does not exist!!!" % args.probelistname)
        sys.exit(-1)

    with open(args.avg_msm_probes, 'r') as msmprobesj:
        avg_msm_probes = json.load(msmprobesj)

    with open(args.median_msm_probes, 'r') as msmprobesj:
        median_msm_probes = json.load(msmprobesj)


    for server, probes in avg_msm_probes.items():
        print("There are %s probes within range for traces to %s using avg RTT filtering" %(len(probes), server))
        print("There are %s unique probes in the list" % len(set(probes)))
        avg_probe_set = set(probes)
        median_probe_set =  set(median_msm_probes[server])
        diff = avg_probe_set.symmetric_difference(median_probe_set)
        print("Difference between probes in the avg and median list for %s: %s" %(server, diff))
        for prb in probes:
            if prb not in median_probe_set:
                print("Probe %s not median probe set for %s" % (prb, server))
        vars()[server] = probes 

    print("Blizzard has %s probes: " % len(Blizzard))
    print("Ubisoft has %s probes: " % len(Ubisoft))
    print("Valve has %s probes:" % len(Valve))

    

    #diff = ( Blizzard | Ubisoft | Valve) - ( Blizzard & Ubisoft & Valve)
    #print(diff)
    #print(len(diff))
    #
    #l = [Blizzard,  Ubisoft, Valve]
    #diff2 = set.union(*l) - set.intersection(*l)
    #print(diff2)
    #print(len(diff2))
    #probes = Ubisoft
    #
    #if diff == diff2:
    #    for prb in diff:
    #        probes.add(prb)

    #print("All probes: %s" % len(probes))
    
    #probes = []

    #for msm, probe_list in msm_probes.items():
    #    for probe in probe_list:
    #        probes.append(str(probe))
    
    #if len(probes) > 300:
    #    n = 300
    #    for i in range(0, len(probes)+1, n):
    #        print(i)
    #        print(probes[i])
    #        probe_list_out = ",".join(probes[i:i+n])
    #        filename = args.probelistname+'/'+'avg-rtt-valid-probes-'+str(i+1)
    #        with open(filename, "w") as txt:
    #            txt.write(probe_list_out)

    strBlizzard = []
    for prb in Blizzard:
        strBlizzard.append(str(prb))

    strUbisoft = []
    for prb in Ubisoft:
        strUbisoft.append(str(prb))

    strValve = []
    for prb in Valve:
        strValve.append(str(prb))

    Blizzard = strBlizzard
    Ubisoft = strUbisoft
    Valve = strValve

    if len(Blizzard) > 300:
        n = 300
        for i in range(0, len(Blizzard)+1, n):
            print(i)
            print(Blizzard[i])
            probe_list_out = ",".join(Blizzard[i:i+n])
            filename = args.probelistname+'/'+'Blizzard-'+str(i+1)
            with open(filename, "w") as txt:
                txt.write(probe_list_out)

    if len(Ubisoft) > 300:
        n = 300
        for i in range(0, len(Ubisoft)+1, n):
            print(i)
            print(Ubisoft[i])
            probe_list_out = ",".join(Ubisoft[i:i+n])
            filename = args.probelistname+'/'+'Ubisoft-'+str(i+1)
            with open(filename, "w") as txt:
                txt.write(probe_list_out)

    if len(Valve) > 300:
        n = 300
        for i in range(0, len(Valve)+1, n):
            print(i)
            print(Ubisoft[i])
            probe_list_out = ",".join(Valve[i:i+n])
            filename = args.probelistname+'/'+'Valve-'+str(i+1)
            with open(filename, "w") as txt:
                txt.write(probe_list_out)
    
