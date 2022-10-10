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
import json
from collections import OrderedDict, Counter
from pprint import pprint

if __name__ == "__main__":

    #with open('/scratch/measurements/aspath/aspath-for-trace-msms-to-game-servers.json','r') as f:
    with open('/scratch/measurements/aspath/aspath-for-trace-msms-to-ubisoft-and-valve-servers.json', 'r') as f:
        aspathsprb_v_and_u = json.load(f)

    with open('/scratch/measurements/aspath/aspath-for-trace-msms-to-blizzard-server.json', 'r') as f:
        aspathsprb_blizzard = json.load(f) 
        del aspathsprb_blizzard['Valve']
        del aspathsprb_blizzard['Ubisoft']

    with open('/scratch/measurements/aspath/invalid-aspaths-to-game-servers.json', 'r') as f:
        invalidaspathsprb = json.load(f)

    with open('/scratch/measurements/aspath/valid-aspaths-to-game-servers.json', 'r') as f:
        validaspathsprb = json.load(f) 
    
    aspathsprb = { **aspathsprb_blizzard, **aspathsprb_v_and_u }

    for server, prbs in aspathsprb.items():
        if server == 'Valve':
            print("There are  %s probe-path for %s" % (len(prbs), server))
            prb_set = set()
            valve_asn_set = set()
            for prb in prbs: 
                (prb_id, aspaths), = prb.items()
                prb_set.add(prb_id)
                for aspath in aspaths:
                    valve_asn_set.add(aspath[0])
            print("Unique probes in probes-path: %s for %s" % (len(prb_set), server))
            print("Probes in trace measurements to %s are distributed across: %s ASNs"
                  % (server, len(valve_asn_set)))

        if server == 'Ubisoft':
            print("There are %s probe-path for %s" %(len(prbs), server))
            prb_set = set()
            ubisoft_asn_set = set()
            for prb in prbs: 
                (prb_id, aspaths), = prb.items()
                prb_set.add(prb_id)
                for aspath in aspaths:
                    ubisoft_asn_set.add(aspath[0])
            print("Unique probes in probes-path: %s for %s" % (len(prb_set), server))
            print("Probes in trace measurements to %s are distributed across: %s ASNs"
                  % (server, len(ubisoft_asn_set)))

        if server == 'Blizzard':
            print("There are %s probe-path for %s" %(len(prbs), server))
            prb_set = set()
            blizzard_asn_set = set()
            for prb in prbs: 
                (prb_id, aspaths), = prb.items()
                prb_set.add(prb_id)
                for aspath in aspaths:
                    blizzard_asn_set.add(aspath[0])
            print("Unique probes in probes-path: %s for %s" % (len(prb_set), server))
            print("Probes in trace measurements to %s are distributed across: %s ASNs"
                  % (server, len(blizzard_asn_set)))
    
    aspath2prb_valid = {}
    aspath2prb_invalid = {}

    for server, prbs in aspathsprb.items():
        print("%s AS path vetting" % server)
        prb_aspaths_valid = []
        prb_aspaths_invalid = []

        for prb in prbs:
            (prb_id, aspaths), = prb.items()
            valid = []
            invalid = []
            if len(aspaths) < 2:
                i = 0
                for asn in aspaths[0]:
                    if isinstance(asn, int):
                        i += 1

                if i > 3:
                    valid.append(aspaths[0])
                else:
                    invalid.append(aspaths[0])

                if len(invalid) != 0:
                    prb_aspaths_invalid.append({prb_id: invalid})
                
                if len(valid) != 0:
                    prb_aspaths_valid.append({prb_id: valid})
            else:
                if len(aspaths) > 2:
                    print("Probe %s has %s AS paths resolved to %s"
                          % (prb_id, len(aspaths), server))

                #if Counter(aspaths[0]) != Counter(aspaths[1]):
                #    print("Different AS paths observed for probe %s to %s"
                #          % (prb_id, server))
                #    print("     Path 1: %s" % aspaths[0])
                #    print("     Path 2: %s" % aspaths[1])
                #    print("\n")

                for aspath in aspaths:
                    i = 0
                    for asn in aspath:
                        if isinstance(asn, int):
                            i += 1

                    if i > 3:
                        valid.append(aspath)
                    else:
                        invalid.append(aspath)

                if len(invalid) != 0:
                    prb_aspaths_invalid.append({prb_id: invalid})

                if len(valid) != 0:
                    prb_aspaths_valid.append({prb_id: valid})

        aspath2prb_valid[server] = prb_aspaths_valid
        aspath2prb_invalid[server] = prb_aspaths_invalid

    valve_valid_prb = set()
    ubi_valid_prb = set()
    bliz_valid_prb = set()
    for server, prbs in aspath2prb_valid.items():
        if server == 'Valve':

            print("There are %s valid probes with AS paths to %s"
                  % (len(prbs), server))
            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                valve_valid_prb.add(prb_id)
                #print("    Probe %s to %s via valid AS paths: %s"
                #      % (prb_id, server, aspaths))
            print("\n")

        if server == 'Ubisoft':

            print("There are %s valid probes with AS paths to %s"
                  % (len(prbs), server))
            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                ubi_valid_prb.add(prb_id)
                #print("    Probe %s to %s via valid AS paths: %s"
                #      % (prb_id, server, aspaths))
            print("\n")
        
        if server == 'Blizzard':

            print("There are %s valid probes with AS paths to %s"
                  % (len(prbs), server))
            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                bliz_valid_prb.add(prb_id)
                #print("    Probe %s to %s via valid AS paths: %s"
                #      % (prb_id, server, aspaths))
            print("\n")

    print("Number of probes in valve_valid_prb: %s" % len(valve_valid_prb))
    print("Number of probes in ubi_valid_prb: %s" % len(ubi_valid_prb))
    print("Number of probes in bliz_valid_prb: %s" % len(bliz_valid_prb))



    all_valid_probes_set = valve_valid_prb.union(ubi_valid_prb, bliz_valid_prb)
    print("Number of probes with valid AS path to the three game servers: %s" % len(all_valid_probes_set))
    common_probes_to_all_servers = set.intersection(valve_valid_prb, ubi_valid_prb, bliz_valid_prb)
    print("%s probes are common to the three game servers"  % len(common_probes_to_all_servers))
    #print("Probes common to the three game servers:  %s"  % valid_probes_to_all_servers)

    for server, prbs in aspath2prb_invalid.items():

        if server == 'Valve':
            i = 0
            print("There are %s probes with invalid AS paths to %s"
                  % (len(prbs), server))
            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                if prb_id in valve_valid_prb:
                    i += 1
                #print("    Probe %s to %s AS paths: %s"
                #      % (prb_id, server, aspaths))
            print("There %s probes that are also in the valid probe list for valve" % i)
            print("\n")

        if server == 'Ubisoft':
            i = 0
            print("There are %s probes with invalid AS paths to %s"
                  % (len(prbs), server))
            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                if prb_id in ubi_valid_prb:
                    i += 1
                #print("    Probe %s to %s AS paths: %s"
                #      % (prb_id, server, aspaths))
            print("There %s probes that are also in the valid probe list for Ubisoft" % i)
            print("\n")

        if server == 'Blizzard':
            i = 0
            print("There are %s probes with invalid AS paths to %s"
                  % (len(prbs), server))
            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                if prb_id in bliz_valid_prb:
                    i += 1
                #print("    Probe %s to %s AS paths: %s"
                #      % (prb_id, server, aspaths))
            print("There %s probes that are also in the valid probe list for Blizzard" % i)
            print("\n")
    
    valve_aspaths_from_prb = aspath2prb_valid['Valve']
    ubisoft_aspaths_from_prb = aspath2prb_valid['Ubisoft']
    blizzard_aspaths_from_prb = aspath2prb_valid['Blizzard']

    prb_asns_valve = {}
    
    for prb in valve_aspaths_from_prb:
        (prb_id, aspaths), = prb.items()
        for aspath in aspaths:
            origin_asn = aspath[0]
            if origin_asn not in prb_asns_valve:
                prb_asns_valve[origin_asn] = [prb_id]
            else: 
                if prb_id not in prb_asns_valve[origin_asn]:
                    prb_asns_valve[origin_asn].append(prb_id)

    prb_asns_ubisoft = {}
    for prb in ubisoft_aspaths_from_prb:
        (prb_id, aspaths), = prb.items()
        for aspath in aspaths:
            origin_asn = aspath[0]
            if origin_asn not in prb_asns_ubisoft:
                prb_asns_ubisoft[origin_asn] = [prb_id]
            else:
                if prb_id not in prb_asns_ubisoft[origin_asn]:
                    prb_asns_ubisoft[origin_asn].append(prb_id)
    
    prb_asns_blizzard = {}
    for prb in blizzard_aspaths_from_prb:
        (prb_id, aspaths), = prb.items()
        for aspath in aspaths:
            origin_asn = aspath[0]
            if origin_asn not in prb_asns_blizzard:
                prb_asns_blizzard[origin_asn] = [prb_id]
            else:
                if prb_id not in prb_asns_blizzard[origin_asn]:
                    prb_asns_blizzard[origin_asn].append(prb_id)
    
    print("Number of origin ASNs to Valve from probes: %s" % len(prb_asns_valve))
    #print("ASNs and their probes to Valve: %s" % prb_asns_valve)
    asns_with_multi_probes_valve = {}
    for asn, prbs in prb_asns_valve.items():
        if len(prbs) > 1:
            asns_with_multi_probes_valve[asn] = prbs
    print("Number of origin ASNs with multiple probes to Valve: %s" % len(asns_with_multi_probes_valve))
    #for asn, prbs in asns_with_multi_probes_valve.items():
    #    print("ASN to Valve: %s" % asn)
    #    for prb_id in prbs:
    #        for prb in valve_aspaths_from_prb:
    #            (probe_id, aspaths), = prb.items()
    #            if prb_id != probe_id:
    #                continue
    #            #print("   Probe %s in ASN%s" % (prb_id, asn))
    #            if len(aspaths) > 1:
    #                print("      AS path 1: %s" % (aspaths[0]))
    #                print("      AS path 2: %s" % (aspaths[1]))
    #            else:
    #                #print("      AS path: %s" % (aspaths[0]))
    #    print("\n")

    #print("\n")

    print("Number of origin ASNs to Ubisoft from probes: %s" % len(prb_asns_ubisoft))
    #print("ASNs and their probes to Ubisoft: %s" % prb_asns_ubisoft)
    asns_with_multi_probes_ubisoft = {}
    for asn, prbs in prb_asns_ubisoft.items():
        if len(prbs) > 1:
            asns_with_multi_probes_ubisoft[asn] = prbs
    print("Number of origin ASNs with multiple probes to Ubisoft: %s" % len(asns_with_multi_probes_ubisoft))
    #for asn, prbs in asns_with_multi_probes_ubisoft.items():
    #    print("ASN to Ubisoft: %s" % asn)
    #    for prb_id in prbs:
    #        for prb in ubisoft_aspaths_from_prb:
    #            (probe_id, aspaths), = prb.items()
    #            if prb_id != probe_id:
    #                continue
    #            print("   Probe %s in ASN%s" % (prb_id, asn))
    #            if len(aspaths) > 1:
    #                print("      AS path 1: %s" % (aspaths[0]))
    #                print("      AS path 2: %s" % (aspaths[1]))
    #            else:
    #                print("      AS path: %s" % (aspaths[0]))
    #    print("\n")
    

    print("Number of origin ASNs to Ubisoft from probes: %s" % len(prb_asns_ubisoft))
    #print("ASNs and their probes to Ubisoft: %s" % prb_asns_ubisoft)
    asns_with_multi_probes_ubisoft = {}
    for asn, prbs in prb_asns_ubisoft.items():
        if len(prbs) > 1:
            asns_with_multi_probes_ubisoft[asn] = prbs
    print("Number of origin ASNs with multiple probes to Ubisoft: %s" % len(asns_with_multi_probes_ubisoft))
    print("ASN with probes using different paths to Ubisoft")
    probes_in_the_same_asn_with_diff_paths = []
    for asn, prbs in asns_with_multi_probes_ubisoft.items():
        #print("ASN to Blizzard: %s" % asn)
        prb_asnpaths = {}
        all_asnpath_prb_list = []
        for prb_id in prbs:
            for prb in ubisoft_aspaths_from_prb:
                (probe_id, aspaths), = prb.items()
                if prb_id != probe_id:
                    continue
                aspath_prb = []
                for aspath in aspaths:
                    str_elem = []
                    for elem in aspath:
                        if isinstance(elem, str):
                            str_elem.append(elem)

                    for str_e in str_elem:
                        aspath.remove(str_e)
                    if aspath not in all_asnpath_prb_list:
                        all_asnpath_prb_list.append(aspath)
                    aspath_prb.append(aspath)
                #if len(aspath_prb) == 2:
                #    if Counter(aspath_prb[0]) == Counter(aspath_prb[1]):
                #        prb_asnpaths[prb_id] =[aspath_prb[0]] 
                #else:
                prb_asnpaths[prb_id] = aspath_prb
       
        asnpaths_multiple = []
        #print("prb_asnpaths: %s" % prb_asnpaths)
        for prb_id, asnpaths in prb_asnpaths.items():
            if len(asnpaths) > 2:
                print("Greater than two, check")

            if len(asnpaths) == 2:
                if Counter(asnpaths[0]) == Counter(asnpaths[1]):
                    i = 0
                    for comp_path in asnpaths_multiple:
                        if Counter(asnpaths[0]) == Counter(comp_path):
                            i += 1
                    if i == 0:
                        if asnpaths[0] not in asnpaths_multiple:
                            asnpaths_multiple.append(asnpaths[0])
                else:
                    i = 0
                    for comp_path in asnpaths_multiple:
                        if Counter(asnpaths[0]) == Counter(comp_path):
                            i += 1

                    if i == 0:
                        if asnpaths[0] not in asnpaths_multiple:
                            asnpaths_multiple.append(asnpaths[0])
                    i = 0
                    for comp_path in asnpaths_multiple:
                        if Counter(asnpaths[1]) == Counter(comp_path):
                            i += 1
                    if i == 0:
                        if asnpaths[1] not in asnpaths_multiple:
                            asnpaths_multiple.append(asnpaths[1])
            else:
                i = 0
                for comp_path in asnpaths_multiple:
                    if Counter(asnpaths[0]) == Counter(comp_path):
                        i += 1

                if i == 0:
                    if asnpaths[0] not in asnpaths_multiple:
                        asnpaths_multiple.append(asnpaths[0])
        #print("Length of probes: %s" % len(prbs))
        #print("Length of prb_asnpaths: %s" % len(prb_asnpaths))
        #if len(asnpaths_multiple) > 1:
        #    print("ASN to Ubisoft: %s" % asn)
        #    probes_in_the_same_asn_with_diff_paths.append(prb_asnpaths)
        #    for prb, paths in prb_asnpaths.items():
        #        print("Probe: %s" % prb)
        #        if len(paths) > 1:
        #            if  Counter(paths[0]) != Counter(paths[1]):
        #                print("     Path1:  %s" %paths[0])
        #                print("     Path2:  %s" %paths[1])
        #            else:
        #                print("     Path:   %s" %paths[0])
        #        else:
        #            print("     Path: %s" %paths[0])
        #    print("\n")

    #with open('/scratch/measurements/aspath/probes-asn-paths-to-server/probes-in-the-same-asn-with-different-aspaths-to-ubisoft.json', 'w', encoding='utf-8') as f:
    #    json.dump(probes_in_the_same_asn_with_diff_paths, f, ensure_ascii=False, indent=4)

    probe_asns_and_paths = {}
    count = 0
    print("length of prb_asns_blizzard: %s" % len(prb_asns_blizzard))
    for asn, prbs in prb_asns_blizzard.items():
        #prb_asnpaths = {}
        all_paths_for_asn = []
        #print("For Blizzard server:")
        for prb_id in prbs:
            for prb in blizzard_aspaths_from_prb:
                (probe_id, aspaths), = prb.items()
                if prb_id != probe_id:
                    continue
                #aspath_prb = []
                for aspath in aspaths:
                    str_elem = []
                    for elem in aspath:
                        if isinstance(elem, str):
                            str_elem.append(elem)

                    for str_e in str_elem:
                        aspath.remove(str_e)

                    if aspath not in all_paths_for_asn:
                        all_paths_for_asn.append(aspath)
                    #aspath_prb.append(aspath)
                #if len(aspath_prb) == 2:
                #    if Counter(aspath_prb[0]) == Counter(aspath_prb[1]):
                #        prb_asnpaths[prb_id] =[aspath_prb[0]] 
                #else:
                #prb_asnpaths[prb_id] = aspath_prb
        #print("ASN %s" % asn)
        #print("   UNIQUE PATHS: %s" % all_paths_for_asn)
        if len(all_paths_for_asn) > 1:
            count += 1
        probe_asns_and_paths[asn] = all_paths_for_asn

    print("All ASNs in probe_asns_paths: %s" % len(probe_asns_and_paths))
    print("All ASNs with multiple paths: %s" % count)
    #with open('/scratch/measurements/aspath/probes-asn-paths-to-server/asn-and-paths-of-probes-to-blizzard-server.json', 'w', encoding='utf-8') as f:
    #    json.dump(probe_asns_and_paths, f, ensure_ascii=False, indent=4)



                #print("   Probe %s in ASN%s" % (prb_id, asn))
                #if len(aspaths) > 1:
                #    print("      AS path 1: %s" % (aspaths[0]))
                #    print("      AS path 2: %s" % (aspaths[1]))
                #else:
                #    print("      AS path: %s" % (aspaths[0]))
        #print("\n")

    
    #asn_aspath_valve = {} 
    #for asn, prbs in prb_asns_valve.items():
    #    asn_paths_to_server = []
    #    all_aspaths_asn = []
    #    for prb_id in prbs:
    #        for prb in valve_aspaths_from_prb:
    #            (probe_id, aspaths), = prb.items()
    #            if prb_id != probe_id:
    #                continue
    #            for aspath in aspaths:
    #                all_aspaths_asn.append(aspath)
    #    for aspath in all_aspaths_asn:
    #        i = 0
    #        for aspath_comp in all_aspaths_asn:
    #            if Counter(aspath) == Counter(aspath_comp):
    #                i += 1

    #        if i == 1:
    #            asn_paths_to_server.append(aspath)

    #        if i > 1:
    #            if aspath not in asn_paths_to_server:
    #                asn_paths_to_server.append(aspath)
    #    asn_aspath_valve[asn] = asn_paths_to_server

    #asn_count = 0
    #print("Disjointed paths per AS to Valve:")
    #for asn, paths in asn_aspath_valve.items():
    #    asn_paths = []
    #    all_aspaths_asn = []
    #    for path in paths:
    #        str_elems = []
    #        for elem in path:
    #            if isinstance(elem, str):
    #                str_elems.append(elem)

    #        for str_e in str_elems:
    #            path.remove(str_e)
    #        all_aspaths_asn.append(path)

    #    for aspath in all_aspaths_asn:
    #        i = 0
    #        for path_comp in all_aspaths_asn:
    #            if Counter(aspath) == Counter(path_comp):
    #                i += 1

    #        if i == 1:
    #            asn_paths.append(aspath)

    #        if i > 1:
    #            if aspath not in asn_paths:
    #                asn_paths.append(aspath)
    #    if len(asn_paths) > 1:
    #        asn_count += 1 
    #    print("ASN %s" % asn)
    #    if len(asn_paths) > 1:
    #        for path in asn_paths:
    #            print("     Path: %s" %path)
    #        print("\n")
    #
    #print("%s ASNs have disjointed paths to Valve" %asn_count)
