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
                           default='/scratch/probe-list/ping-measurements/probes-for-trace-filtered-by-avg-rtt-per-game-provider.json')

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
        median_probe = median_msm_probes[server]
        median_probe_set =  set(median_msm_probes[server])
        print("There are %s probes within range for traces to %s using median RTT filtering" %(len(median_probe),server))
        print("There are %s unique probes in the median probe" % len(median_probe_set))
        diff = avg_probe_set.symmetric_difference(median_probe_set)
        print("Difference between probes in the avg and median list for %s: %s" %(server, diff))
        print("\n")
        #for prb in probes:
        #    if prb not in median_probe_set:
        #        print("Probe %s not median probe set for %s" % (prb, server))
        #if len(median_probe) > len(probes):
        vars()[server] = median_probe

        #if len(probes) > len(median_probe):
        #    vars()[server] = probes


    print("Blizzard has %s filtered probes: " % len(Blizzard))
    print("Ubisoft has %s filtered probes: " % len(Ubisoft))
    print("Valve has %s filtered probes:\n" % len(Valve))

    

    with open('/scratch/probe-list/trace-measurements/filtered-valid-probes-per-server/Valve-1', 'r') as f:
        bl1 = f.read()
    bl1 = bl1.split(",")

    with open('/scratch/probe-list/trace-measurements/filtered-valid-probes-per-server/Valve-301', 'r') as f:
        bl301 = f.read()
    bl301 = bl301.split(",")

    with open('/scratch/probe-list/trace-measurements/filtered-valid-probes-per-server/Valve-601', 'r') as f:
        bl601 = f.read()
    bl601 = bl601.split(",")

    #with open('/scratch/probe-list/trace-measurements/filtered-valid-probes-per-server/Ubisoft-901', 'r') as f:
    #    bl901 = f.read()
    #bl901 = bl901.split(",")

    full_bl = bl1 + bl301 + bl601
    print("Number of probes from existing msm: %s" % len(full_bl))
    bl_int  = []
    for prb in full_bl:
        bl_int.append(int(prb))

    set_Blizzard = set(Valve)
    set_bl_int = set(bl_int)
    print("Number of probes in set of existing msm: %s" % len(set_bl_int))
    diff = set_Blizzard.symmetric_difference(set_bl_int)
    print(diff) 
    print("Number of probes to be included: %s" % len(diff))

    total = len(bl_int) + len(diff)
    print("Total now: %s" % total)
    print("Length of new prb: %s"  % len(Valve))
    prb_list = []
    for prb in diff:
        prb_list.append(str(prb))

    probe_list_out = ",".join(prb_list)
    with open('/scratch/probe-list/trace-measurements/filtered-valid-probes-per-server/Valve-extra', "w") as txt:
        txt.write(probe_list_out)
    #with open('/scratch/probe-list/ping-measurements/Blizzard-probe-rtt-list.json', 'r') as prb_list:
    #    blizzard = json.load(prb_list)

    #with open('/scratch/probe-list/ping-measurements/Ubisoft-probe-rtt-list.json', 'r') as prb_list:
    #    ubisoft = json.load(prb_list) 

    #with open('/scratch/probe-list/ping-measurements/Valve-probe-rtt-list.json', 'r') as prb_list:
    #    valve = json.load(prb_list)

    #blizzard_prb = set()
    #for prb_msm in blizzard: 
    #    for prb, msm in prb_msm.items(): 
    #        blizzard_prb.add(prb)

    #ubisoft_prb = set()
    #for prb_msm in ubisoft:
    #    for prb, msm in prb_msm.items():
    #        ubisoft_prb.add(prb)


    #valve_prb = set()
    #for prb_msm in valve:
    #    for prb, msm in prb_msm.items():
    #        valve_prb.add(prb)

    #print("Blizzard has: %s probes" %len(blizzard_prb))
    #print("Ubisoft  has: %s probes" %len(ubisoft_prb))
    #print("Valve has: %s probes" %len(valve_prb))
    #print("Diff between Blizzard and Ubisoft: %s" %(ubisoft_prb.symmetric_difference(blizzard_prb)))
    #print("Diff between Ubisoft and Valve: %s" %(ubisoft_prb.symmetric_difference(valve_prb)))
    #print("Diff between Blizzard and Valve: %s" %(blizzard_prb.symmetric_difference(valve_prb)))
    #diff_all_theree = ( blizzard_prb | ubisoft_prb | valve_prb ) - (blizzard_prb & ubisoft_prb & valve_prb)
    #print("All three diff: %s" % diff_all_theree)


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
