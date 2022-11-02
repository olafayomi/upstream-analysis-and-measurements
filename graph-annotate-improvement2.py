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

import csv
import sys
import json
import requests
import argparse
import ipaddress
import _pyipmeta
import pytricia
from pprint import pprint
from pathlib import Path
from collections import OrderedDict, Counter
from pprint import pprint
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from networkx import path_graph, random_layout
from pyvis.network import Network
import numpy as np
from glob import glob

caida_prefix2as = "https://publicdata.caida.org/datasets/routing/routeviews-prefix2as/2022/09/routeviews-rv2-20220920-1200.pfx2as.gz"


def getResults(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    mresp = requests.get(url)
    data = mresp.json()
    res_url = data['result']
    res_data = requests.get(res_url)
    results = res_data.json()
    print("Fetched results for msm: %s" % measurement_id)
    return results


def getProbeInfo(probe_id):
    url = "https://atlas.ripe.net/api/v2/probes/"+str(probe_id)+"/"
    resp = requests.get(url)
    data = resp.json()
    return data


def validaspathsprobe(aspathsprb):
    aspath2prb_valid = {}
    for server, prbs in aspathsprb.items():
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
    return aspath2prb_valid

# remove strings and similar ASpaths
def aspathcleanup(aspathsprb):
    cleanedaspath = {}
    for server, prbs in aspathsprb.items():
        prb_asnpaths = []
        for prb in prbs:
            (prb_id, aspaths), = prb.items()
            prb_asnpath = {}
            aspath_prb = []
            for aspath in aspaths:
                str_elem = []
                for elem in aspath:
                    if isinstance(elem, str):
                        str_elem.append(elem)

                for str_e in str_elem:
                    aspath.remove(str_e)
                aspath_prb.append(aspath)
            if len(aspath_prb) > 2:
                print("There are more than two path for probe: %s"  %prb_id)

            if len(aspath_prb) == 2:
                if Counter(aspath_prb[0]) == Counter(aspath_prb[1]):
                    prb_asnpath[prb_id] = [aspath_prb[0]]
                else:
                    prb_asnpath[prb_id] = [aspath_prb[0]]
                    prb_asnpath[prb_id].append(aspath_prb[1])
            else:
                prb_asnpath[prb_id] = [aspath_prb[0]]
            prb_asnpaths.append(prb_asnpath)
        cleanedaspath[server] = prb_asnpaths
    return cleanedaspath


def fetchOriginASN(validset):
    prbASNs_server = {}
    for prb in validset:
        (prb_id, aspaths), = prb.items()
        for aspath in aspaths:
            origin_asn = aspath[0]
            if origin_asn not in prbASNs_server:
                prbASNs_server[origin_asn] = [prb_id]
            else:
                if prb_id not in prbASNs_server[origin_asn]:
                    prbASNs_server[origin_asn].append(prb_id)
    return prbASNs_server


def GetProbes(aspath2prb_valid):
    valve_valid_prb = set()
    ubi_valid_prb = set()
    bliz_valid_prb = set()
    for server, prbs in aspath2prb_valid.items():
        if server == 'Valve':

            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                valve_valid_prb.add(prb_id)

        if server == 'Ubisoft':

            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                ubi_valid_prb.add(prb_id)

        if server == 'Blizzard':

            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                bliz_valid_prb.add(prb_id)

    all_valid_probes_set = valve_valid_prb.union(ubi_valid_prb, bliz_valid_prb)
    common_probes_to_all_servers = set.intersection(valve_valid_prb, bliz_valid_prb, ubi_valid_prb)
    return common_probes_to_all_servers, all_valid_probes_set


def GetASNFromProbes(common_probes_to_all_servers,
                     valve_aspaths_from_prb,
                     ubisoft_aspaths_from_prb,
                     blizzard_aspaths_from_prb):
    asn_of_common_valid_probes = {}
    for prb_id in common_probes_to_all_servers:
        for prb in valve_aspaths_from_prb:
            (probe_id, aspaths), = prb.items()
            if probe_id != prb_id:
                continue
            for aspath in aspaths:
                origin_asn = aspath[0]
                if origin_asn not in asn_of_common_valid_probes:
                    asn_of_common_valid_probes[origin_asn] = [prb_id]
                else:
                    if prb_id not in asn_of_common_valid_probes[origin_asn]:
                        asn_of_common_valid_probes[origin_asn].append(prb_id)

        for prb in ubisoft_aspaths_from_prb:
            (probe_id, aspaths), = prb.items()
            if probe_id != prb_id:
                continue
            for aspath in aspaths:
                origin_asn = aspath[0]
                if origin_asn not in asn_of_common_valid_probes:
                    asn_of_common_valid_probes[origin_asn] = [prb_id]
                else:
                    if prb_id not in asn_of_common_valid_probes[origin_asn]:
                        asn_of_common_valid_probes[origin_asn].append(prb_id)

        for prb in blizzard_aspaths_from_prb:
            (probe_id, aspaths), = prb.items()
            if probe_id != prb_id:
                continue
            for aspath in aspaths:
                origin_asn = aspath[0]
                if origin_asn not in asn_of_common_valid_probes:
                    asn_of_common_valid_probes[origin_asn] = [prb_id]
                else:
                    if prb_id not in asn_of_common_valid_probes[origin_asn]:
                        asn_of_common_valid_probes[origin_asn].append(prb_id)
    return asn_of_common_valid_probes


def createGraph(asnFromProbeLst, valve_aspaths_from_prb,
                ubisoft_aspaths_from_prb,
                blizzard_aspaths_from_prb):
    pathasn = set()
    graph = nx.DiGraph()
    penultimate_asn = set()
    for asn, probes in asnFromProbeLst.items():
        for probe in probes:
            for prb in blizzard_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe:
                    continue
                for aspath in aspaths:
                    str_elem = []
                    for elem in aspath:
                        if isinstance(elem, str):
                            str_elem.append(elem)

                    for str_e in str_elem:
                        aspath.remove(str_e)
                    graph.add_nodes_from(aspath)
                    for asn in aspath:
                        pathasn.add(asn)
                        index = aspath.index(asn)
                        if index == (len(aspath) - 2):
                            penultimate_asn.add(asn)
                        next_id = index + 1
                        if next_id != len(aspath):
                            graph.add_edge(asn, aspath[next_id], color='blue')

            for prb in valve_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe:
                    continue
                for aspath in aspaths:
                    str_elem = []
                    for elem in aspath:
                        if isinstance(elem, str):
                            str_elem.append(elem)

                    for str_e in str_elem:
                        aspath.remove(str_e)
                    graph.add_nodes_from(aspath)
                    for asn in aspath:
                        pathasn.add(asn)
                        index = aspath.index(asn)
                        if index == (len(aspath) - 2):
                            penultimate_asn.add(asn)
                        next_id = index + 1
                        if next_id != len(aspath):
                            graph.add_edge(asn, aspath[next_id], color='red')

            for prb in ubisoft_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe:
                    continue
                for aspath in aspaths:
                    str_elem = []
                    for elem in aspath:
                        if isinstance(elem, str):
                            str_elem.append(elem)

                    for str_e in str_elem:
                        aspath.remove(str_e)
                    graph.add_nodes_from(aspath)
                    for asn in aspath:
                        pathasn.add(asn)
                        index = aspath.index(asn)
                        if index == (len(aspath) - 2):
                            penultimate_asn.add(asn)
                        next_id = index + 1
                        if next_id != len(aspath):
                            graph.add_edge(asn, aspath[next_id], color='green')
    return graph


def pyvisualise(graph, name):
    net = Network(height="1000px", width="100%", notebook=True, directed=True)
    net.toggle_physics(True)
    net.show_buttons(filter_=True)
    net.from_nx(graph)
    neigh_map = net.get_adj_list()
    new_map = {}
    for node, neigh in neigh_map.items():
        new_set = set()
        for n in neigh:
            new_set.add(str(n))
        new_map[node] = new_set

    for node in net.nodes:
        node["title"] = "ASN"+str(node['id'])+"'s Neighbors:\n\n" + "\n".join(new_map[node["id"]])
        node["label"] = str(node['id'])

    return net
    #net.show('/scratch/measurements/analysis/path-latency-visualisation/'+(name)+'.html')


def getMsmTarget(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    resp = requests.get(url)
    data = resp.json()
    target = data["target_ip"]
    return target


def rtt_to_aspath(res, aspath, ip2asn, pyt):
    trace1 = res[0]
    msm_id = trace1['msm_id']
    prb_id = trace1['prb_id']
    hops = trace1['result']
    asn_to_hops = {}
    for hop in hops:
        hop_nop = hop['hop']
        try:
            hop_results = hop['result']
        except KeyError:
            continue

        rtts = []
        hop_ip_addrs = set()
        hop_asn = set()
        for rtt_to_hop in hop_results:
            try:
                hop_ip_addrs.add(rtt_to_hop['from'])
            except KeyError:
                continue

            try:
                rtts.append(rtt_to_hop['rtt'])
            except KeyError:
                continue

        if len(rtts) > 0:
            median = np.median(rtts)
        else:
            median = 0

        for hop_ip in hop_ip_addrs:
            try:
                hopAddr = ipaddress.ip_address(hop_ip)
            except ValueError:
                continue

            if hopAddr.is_global:
                asn = None 
                if hop_ip in ip2asn:
                    asn = ip2asn[hop_ip]
                else:
                    asn = pyt.get(hop_ip)
                if asn is not None:

                    if not isinstance(asn, int):
                        asn = int(asn)

                    if asn not in asn_to_hops:
                        asn_to_hops[asn] = { hop_nop: { 'rtt': rtts,
                                                        'median rtt': median,
                                                        'hop ip': [hop_ip]}}
                    else:
                        if hop_nop not in asn_to_hops[asn]:
                            asn_to_hops[asn][hop_nop] = { 'rtt': rtts,
                                                          'median rtt': median,
                                                          'hop ip': [hop_ip]}
                        else:
                            asn_to_hops[asn][hop_nop]['hop ip'].append(hop_ip)

    print("ASN to hops for PROBE %s in MSM%s: %s" %(prb_id, msm_id, asn_to_hops))
    last_hop_asn = {}
    for asn, hops in asn_to_hops.items():
        hops_list = list(hops.keys())
        print("ASN %s has the following hops: %s" %(asn, hops_list))
        print("The last hop in ASN %s is %s" %(asn, max(hops_list)))
        print("Median RTT to last hop in ASN %s is %s"
              %(asn,asn_to_hops[asn][max(hops_list)]['median rtt']))
        
def rtt_to_aspath2(res, ip2asn, pyt):
    trace1 = res
    msm_id = trace1['msm_id']
    prb_id = trace1['prb_id']
    hops = trace1['result']
    asn_to_hops = {}
    for hop in hops:
        hop_nop = hop['hop']
        try:
            hop_results = hop['result']
        except KeyError:
            continue

        rtts = []
        hop_ip_addrs = set()
        hop_asn = set()
        for rtt_to_hop in hop_results:
            try:
                hop_ip_addrs.add(rtt_to_hop['from'])
            except KeyError:
                continue

            try:
                rtts.append(rtt_to_hop['rtt'])
            except KeyError:
                continue

        if len(rtts) > 0:
            median = np.median(rtts)
        else:
            median = 0

        for hop_ip in hop_ip_addrs:
            try:
                hopAddr = ipaddress.ip_address(hop_ip)
            except ValueError:
                continue

            if hopAddr.is_global:
                asn = None 
                if hop_ip in ip2asn:
                    asn = ip2asn[hop_ip]
                else:
                    asn = pyt.get(hop_ip)
                if asn is not None:

                    if not isinstance(asn, int):
                        asn = int(asn)

                    if asn not in asn_to_hops:
                        asn_to_hops[asn] = { hop_nop: { 'rtt': rtts,
                                                        'median rtt': median,
                                                        'hop ip': [hop_ip]}}
                    else:
                        if hop_nop not in asn_to_hops[asn]:
                            asn_to_hops[asn][hop_nop] = { 'rtt': rtts,
                                                          'median rtt': median,
                                                          'hop ip': [hop_ip]}
                        else:
                            asn_to_hops[asn][hop_nop]['hop ip'].append(hop_ip)

    return  asn_to_hops
    #print("ASN to hops for PROBE %s in MSM%s: %s" %(prb_id, msm_id, asn_to_hops))
    #last_hop_asn = {}
    #for asn, hops in asn_to_hops.items():
    #    hops_list = list(hops.keys())
    #    print("ASN %s has the following hops: %s" %(asn, hops_list))
    #    print("The last hop in ASN %s is %s" %(asn, max(hops_list)))
    #    print("Median RTT to last hop in ASN %s is %s"
    #          %(asn,asn_to_hops[asn][max(hops_list)]['median rtt']))


if __name__ == "__main__":

    msm_list = []
    for raw_msm in glob('/scratch/measurements/traceroute/raw-measurements-results/*.json'):
        with open(raw_msm, 'r') as f:
            msm_raw = json.load(f)
            msm_list.append(msm_raw)

    with open('/scratch/measurements/aspath/probes-asn-paths-to-server/list-of-asns-and-probes-common-to-msms-to-the-three-game-servers-and-their-paths.json', 'r') as validlist:
        commonASNsandProbes = json.load(validlist)

    pyt = pytricia.PyTricia(128)
    with open('/scratch/ip2as.pfx2as', 'r') as f:
        prefix2as_file = csv.reader(f, delimiter=' ')
        for prefix2as in prefix2as_file:
            pyt.insert(prefix2as[0], prefix2as[1])

    ipm = _pyipmeta.IpMeta()
    ipm_prov = ipm.get_provider_by_name("pfx2as")

    with open('/scratch/measurements/ip2asn/traceip2asn.json', 'r') as ip2asnjson:
        ip2asn = json.load(ip2asnjson)

    with open('/scratch/measurements/aspath/aspath-for-trace-msms-to-ubisoft-and-valve-servers.json', 'r') as f:
        aspathsprb_v_and_u = json.load(f)

    with open('/scratch/measurements/aspath/aspath-for-trace-msms-to-blizzard-server.json', 'r') as f:
        aspathsprb_blizzard = json.load(f)
        del aspathsprb_blizzard['Valve']
        del aspathsprb_blizzard['Ubisoft']
    with open('/scratch/measurements/aspath/probes-asn-paths-to-server/asn-and-probes-with-1299-3356-6969-in-the-paths.json', 'r') as f:
        asnsProbesWithProviderInPath = json.load(f)

    aspathsprb = {**aspathsprb_blizzard, **aspathsprb_v_and_u}
    aspath2prb_valid = validaspathsprobe(aspathsprb)

    valve_aspaths_from_prb = aspath2prb_valid['Valve']
    ubisoft_aspaths_from_prb = aspath2prb_valid['Ubisoft']
    blizzard_aspaths_from_prb = aspath2prb_valid['Blizzard']

    prb_asns_valve = fetchOriginASN(valve_aspaths_from_prb)
    prb_asns_ubisoft = fetchOriginASN(ubisoft_aspaths_from_prb)
    prb_asns_blizzard = fetchOriginASN(blizzard_aspaths_from_prb)
    CommonProbes, AllValid = GetProbes(aspath2prb_valid)
    ASNofCommonProbes = GetASNFromProbes(CommonProbes, valve_aspaths_from_prb,
                                         ubisoft_aspaths_from_prb,
                                         blizzard_aspaths_from_prb)
    g = createGraph(ASNofCommonProbes, valve_aspaths_from_prb,
                    ubisoft_aspaths_from_prb, blizzard_aspaths_from_prb)

    ASNsWithDisjointPaths = [3352, 12302, 13046, 15735, 20912, 24921, 34410, 34643, 48747,
                             56588, 58079, 62418, 199246, 201281, 201494, 208877, 212485]

    TraceMSMToValve = {}
    TraceMSMToBlizzard = {}
    TraceMSMToUbisoft = {}


    for msm in msm_list:
        for result in msm:
            if result["dst_name"] == "162.254.197.36":
                if result["prb_id"] in TraceMSMToValve:
                    TraceMSMToValve[result["prb_id"]].append(result)
                else:
                    TraceMSMToValve[result["prb_id"]] = [result]


            if result["dst_name"] == "185.60.112.157":

                if result["proto"] != "ICMP":
                    continue
                
                if result["prb_id"] in TraceMSMToBlizzard:
                    TraceMSMToBlizzard[result["prb_id"]].append(result)
                else:
                    TraceMSMToBlizzard[result["prb_id"]] = [result]


            if result["dst_name"] == "5.200.20.245":
                if result["prb_id"] in TraceMSMToUbisoft:
                    TraceMSMToUbisoft[result["prb_id"]].append(result)
                else:
                    TraceMSMToUbisoft[result["prb_id"]] = [result]


    for asn, vals in commonASNsandProbes.items():
        if int(asn) not in ASNsWithDisjointPaths:
            continue

        #if int(asn) != 34643:
        #    continue

        for val in vals:
            (val_key, val_val), = val.items()
            if val_key != 'disjointed':
                prb_id = int(val_key)
                aspaths = val_val

                valve = TraceMSMToValve[prb_id]
                blizzard = TraceMSMToBlizzard[prb_id]
                ubisoft = TraceMSMToUbisoft[prb_id]
                #print("ASN %s in aspath is type: %s" %(aspaths[0][0], type(aspaths[0][0])))
                #for msm in ubisoft:
                #    msm_id = msm['msm_id']
                #    prb_id = msm['prb_id']
                #    hops = msm['result']
                #    for hop in hops:
                #        rtt = []
                #    
                #        for res in hop['result']:
                #            try:
                #                rtt.append(res['rtt'])
                #            except KeyError:
                #                continue
                #        if len(rtt) > 1:
                #            median = np.median(rtt)
                #        else:
                #            median = 0
                #        print("MSM ID %s, PRB_ID: %s, Hop: %s, RTT: %s, Median RTT: %s" %(msm_id, prb_id, hop['hop'], rtt, median))

                asn_set = set()
                for aspath in aspaths:
                    for asp in aspath:
                        asn_set.add(asp)

                    #if aspath[-1] == 32590:
                        #valve_aspath_rtt = rtt_to_aspath(valve, aspath, ip2asn, pyt)
                        #print("\n")
                        #if len(valve) < 2:
                        #    print("PROBE ID: %s, MSM ID: %s" %(valve[0]['prb_id'], valve[0]['msm_id']))
                        #else:
                        #    for m in valve:
                        #        print("PROBE ID: %s, MSM ID: %s" %(m['prb_id'], m['msm_id']))
                        #if valve_aspath_rtt is not None:
                        #    print("AS path: %s" %aspath)
                        #    print("Traceroute RTT from probe %s to Valve: %s" % (prb_id, valve_aspath_rtt))

                    #if aspath[-1] == 49544:
                        #ubisoft_aspath_rtt = rtt_to_aspath(ubisoft, aspath, ip2asn, pyt)
                        #print("\n")
                        

                        #if len(ubisoft) < 2:
                        #    print("PROBE ID: %s, MSM ID: %s" %(ubisoft[0]['prb_id'], ubisoft[0]['msm_id']))
                        #else:
                        #    for m in ubisoft:
                        #        print("PROBE ID: %s, MSM ID: %s" %(m['prb_id'], m['msm_id']))

                        #if ubisoft_aspath_rtt is not None:
                        #    print("AS path: %s" %aspath)
                        #    print("Traceroute RTT from probe %s to Ubisoft: %s" % (prb_id, ubisoft_aspath_rtt))

                    #if aspath[-1] == 57976:
                        #blizzard_aspath_rtt = rtt_to_aspath(blizzard, aspath, ip2asn, pyt)
                        #print("\n")

                        #if len(blizzard) < 2:
                        #    print("PROBE ID: %s, MSM ID: %s" %(blizzard[0]['prb_id'], blizzard[0]['msm_id']))
                        #else:
                        #    for m in blizzard:
                        #        print("PROBE ID: %s, MSM ID: %s" %(m['prb_id'], m['msm_id']))

                        #if blizzard_aspath_rtt is not None:
                        #    print("AS path: %s" %aspath)
                        #    print("Traceroute RTT from probe %s to Blizzard: %s" % (prb_id, blizzard_aspath_rtt))
                #print("\n\n\n")

        subgraph = nx.subgraph(g, asn_set)

    providers = { 1299, 3356, 6939 }
    provider_last_hops = {}
    for asn, probes in asnsProbesWithProviderInPath.items():
        for probe in probes:
            prb_id = int(probe)
            valve = TraceMSMToValve[prb_id]
            blizzard = TraceMSMToBlizzard[prb_id]
            ubisoft = TraceMSMToUbisoft[prb_id]

            for msm in valve:
                #print("For probe %s in MSM %s to Valve:" %(msm['prb_id'], msm['msm_id']))
                aspath_rtt = rtt_to_aspath2(msm, ip2asn, pyt)
                asns = aspath_rtt.keys()
                intersect = providers.intersection(set(asns))
                if len(intersect) != 0:
                    aspath = list(aspath_rtt.keys())
                    if aspath[-2] in providers:
                        hops = aspath_rtt[aspath[-2]]
                        hop_list = list(hops.keys())
                        
                        ip_addrs = aspath_rtt[aspath[-2]][max(hop_list)]['hop ip']

                        if 'valve' not in provider_last_hops: 
                            provider_last_hops['valve'] = {aspath[-2]:[ip_addrs]}
                        else:
                            if aspath[-2] not in provider_last_hops['valve']:
                                provider_last_hops['valve'][aspath[-2]] = [ip_addrs]
                            else:
                                provider_last_hops['valve'][aspath[-2]].append(ip_addrs)
                                
                        for asn, hops in aspath_rtt.items():
                            hops_list = list(hops.keys())
                            #print("     ASN %s hops: %s" %(asn, hops_list))
                            #print("     ASN %s last: %s" %(asn, max(hops_list)))
                            #print("     ASN %s last hop IP address: %s"
                            #      %(asn, aspath_rtt[asn][max(hops_list)]['hop ip']))

                    #print("\n")

                    #print(aspath_rtt)


            for msm in blizzard:
                #print("For probe %s in MSM %s to Blizzard:" %(msm['prb_id'], msm['msm_id']))
                aspath_rtt = rtt_to_aspath2(msm, ip2asn, pyt)
                asns = aspath_rtt.keys()
                intersect = providers.intersection(set(asns))
                if len(intersect) != 0:
                    aspath = list(aspath_rtt.keys())
                    if aspath[-2] in providers:
                        hops = aspath_rtt[aspath[-2]]
                        hop_list = list(hops.keys())
                        
                        ip_addrs = aspath_rtt[aspath[-2]][max(hop_list)]['hop ip']

                        if 'blizzard' not in provider_last_hops: 
                            provider_last_hops['blizzard'] = {aspath[-2]:[ip_addrs]}
                        else:
                            if aspath[-2] not in provider_last_hops['blizzard']:
                                provider_last_hops['blizzard'][aspath[-2]] = [ip_addrs]
                            else:
                                provider_last_hops['blizzard'][aspath[-2]].append(ip_addrs)

                        for asn, hops in aspath_rtt.items():
                            hops_list = list(hops.keys())
                            #print("     ASN %s hops: %s" %(asn, hops_list))
                            #print("     ASN %s last: %s" %(asn, max(hops_list)))
                            #print("     ASN %s last hop IP address: %s"
                            #      %(asn, aspath_rtt[asn][max(hops_list)]['hop ip']))

                    #print("\n")

                    #print(aspath_rtt)


            for msm in ubisoft:
                #print("For probe %s in MSM %s to Ubisoft:" %(msm['prb_id'], msm['msm_id']))
                aspath_rtt = rtt_to_aspath2(msm, ip2asn, pyt)
                asns = aspath_rtt.keys()
                intersect = providers.intersection(set(asns))
                if len(intersect) != 0:
                    aspath = list(aspath_rtt.keys())
                    if aspath[-2] in providers:
                        hops = aspath_rtt[aspath[-2]]
                        hop_list = list(hops.keys())
                        
                        ip_addrs = aspath_rtt[aspath[-2]][max(hop_list)]['hop ip']

                        if 'ubisoft' not in provider_last_hops: 
                            provider_last_hops['ubisoft'] = {aspath[-2]:[ip_addrs]}
                        else:
                            if aspath[-2] not in provider_last_hops['ubisoft']:
                                provider_last_hops['ubisoft'][aspath[-2]] = [ip_addrs]
                            else:
                                provider_last_hops['ubisoft'][aspath[-2]].append(ip_addrs)

                        for asn, hops in aspath_rtt.items():
                            hops_list = list(hops.keys())
                            #print("     ASN %s hops: %s" %(asn, hops_list))
                            #print("     ASN %s last: %s" %(asn, max(hops_list)))
                            #print("     ASN %s last hop IP address: %s"
                            #      %(asn, aspath_rtt[asn][max(hops_list)]['hop ip']))

                    #print(aspath_rtt)
                    #print("\n")
    provider_last_hops_unique = {}
    for server, providers in provider_last_hops.items():
        provider_last_hops_unique[server] = {}
        print("For %s" % server)
        for prov_asn, addrs in providers.items():
            print("    From ASN  %s" % prov_asn)
            print("    Addresses: %s" % addrs)
            addr_set = set()
            for addr_lst in addrs:
                for addr in addr_lst:
                    addr_set.add(addr)
            print("   Address Set: %s" % addr_set)
            provider_last_hops_unique[server][prov_asn] = addr_set

    #print("Last hop ipaddresses of ASN 1299, 3356 and 6939 before the game servers: %s\n" % provider_last_hops)
    print("Sorted: %s" %provider_last_hops_unique)

    aspathprbclean =  aspathcleanup(aspath2prb_valid)
    provider_last_hops_whole_set = {}
    #    for probe in probes:
    #        prb_id = int(probe)
    #        valve = TraceMSMToValve[prb_id]
    #        blizzard = TraceMSMToBlizzard[prb_id]
    #        ubisoft = TraceMSMToUbisoft[prb_id]
    providers = { 1299, 3356, 6939 }

    for server, prb_aspaths in aspathprbclean.items():
        if server == 'Valve':
            for prb in prb_aspaths:
                (probe_id, aspaths),  = prb.items()
                prb_id = int(probe_id)
                for path in aspaths:
                    if path[-2] in providers:
                        msms = TraceMSMToValve[prb_id]
                        for msm in msms:
                            aspath_rtt = rtt_to_aspath2(msm, ip2asn, pyt)
                            asns = list(aspath_rtt.keys())
                            intersect = providers.intersection(set(asns))
                            if len(intersect) != 0:
                                aspath = list(aspath_rtt.keys())
                                if aspath[-2] in providers:
                                    hops = aspath_rtt[aspath[-2]]
                                    hop_list = list(hops.keys())

                                    ip_addrs = aspath_rtt[aspath[-2]][max(hop_list)]['hop ip']

                                    if 'valve' not in provider_last_hops_whole_set:
                                        provider_last_hops_whole_set['valve'] = {aspath[-2]:[ip_addrs]}
                                    else:
                                        if aspath[-2] not in provider_last_hops_whole_set['valve']:
                                            provider_last_hops_whole_set['valve'][aspath[-2]] = [ip_addrs]
                                        else:
                                            provider_last_hops_whole_set['valve'][aspath[-2]].append(ip_addrs)

        if server == 'Blizzard':
            for prb in prb_aspaths:
                (probe_id, aspaths),  = prb.items()
                prb_id = int(probe_id)
                for path in aspaths:
                    if path[-2] in providers:
                        msms = TraceMSMToBlizzard[prb_id]
                        for msm in msms:
                            aspath_rtt = rtt_to_aspath2(msm, ip2asn, pyt)
                            asns = list(aspath_rtt.keys())
                            #print("asns: %s" % asns)
                            #print("Providers: %s" % providers)
                            intersect = providers.intersection(set(asns))
                            if len(intersect) != 0:
                                aspath = list(aspath_rtt.keys())
                                if aspath[-2] in providers:
                                    hops = aspath_rtt[aspath[-2]]
                                    hop_list = list(hops.keys())
                        
                                    ip_addrs = aspath_rtt[aspath[-2]][max(hop_list)]['hop ip']

                                    if 'blizzard' not in provider_last_hops_whole_set:
                                        provider_last_hops_whole_set['blizzard'] = {aspath[-2]:[ip_addrs]}
                                    else:
                                        if aspath[-2] not in provider_last_hops_whole_set['blizzard']:
                                            provider_last_hops_whole_set['blizzard'][aspath[-2]] = [ip_addrs]
                                        else:
                                            provider_last_hops_whole_set['blizzard'][aspath[-2]].append(ip_addrs)

        if server == 'Ubisoft':
            for prb in prb_aspaths:
                (probe_id, aspaths),  = prb.items()
                prb_id = int(probe_id)
                for path in aspaths:
                    if path[-2] in providers:
                        msms = TraceMSMToUbisoft[prb_id]
                        for msm in msms:
                            aspath_rtt = rtt_to_aspath2(msm, ip2asn, pyt)
                            asns = list(aspath_rtt.keys())
                            intersect = providers.intersection(set(asns))
                            if len(intersect) != 0:
                                aspath = list(aspath_rtt.keys())
                                if aspath[-2] in providers:
                                    hops = aspath_rtt[aspath[-2]]
                                    hop_list = list(hops.keys())
                        
                                    ip_addrs = aspath_rtt[aspath[-2]][max(hop_list)]['hop ip']

                                    if 'ubisoft' not in provider_last_hops_whole_set:
                                        provider_last_hops_whole_set['ubisoft'] = {aspath[-2]:[ip_addrs]}
                                    else:
                                        if aspath[-2] not in provider_last_hops_whole_set['ubisoft']:
                                            provider_last_hops_whole_set['ubisoft'][aspath[-2]] = [ip_addrs]
                                        else:
                                            provider_last_hops_whole_set['ubisoft'][aspath[-2]].append(ip_addrs)

    provider_last_hops_unique_whole_set = {}
    for server, providers in provider_last_hops_whole_set.items():
        provider_last_hops_unique_whole_set[server] = {}
        print("For %s" % server)
        for prov_asn, addrs in providers.items():
            print("    From ASN  %s" % prov_asn)
            print("    Addresses: %s" % addrs)
            addr_set = set()
            for addr_lst in addrs:
                for addr in addr_lst:
                    addr_set.add(addr)
            print("   Address Set: %s" % addr_set)
            provider_last_hops_unique_whole_set[server][prov_asn] = addr_set
    pprint(provider_last_hops_unique_whole_set)
    print("Last hop unique small set: %s" %provider_last_hops_unique)
    print("Last hop unique whole set: %s" %provider_last_hops_unique_whole_set)
    for server, providers in provider_last_hops_unique.items():
        print("For %s" % server)
        print("     small set")
        for prov_asn, addrs in providers.items():
            print("      From ASN %s" % prov_asn)
            print("      Addresses: %s" % addrs)
        print("\n")

    for server, providers in provider_last_hops_unique_whole_set.items():
        print("For %s" % server)
        print("     whole set")
        for prov_asn, addrs in providers.items():
            print("      From ASN %s" % prov_asn)
            print("      Addresses: %s" % addrs)
        print("\n")

        #net = Network(height="1000px", width="100%", notebook=True, directed=True) 
        #net.toggle_physics(True)
        #net.show_buttons(filter_=True)
        #net.from_nx(subgraph)
        #neigh_map = net.get_adj_list()
        #new_map = {}
        #for node, neigh in neigh_map.items():
        #    new_set = set()
        #    for n in neigh:
        #        new_set.add(str(n))
        #    new_map[node] = new_set

        #for node in net.nodes:
        #    node["title"] = "ASN"+str(node['id'])+"'s Neighbors:\n\n" + "\n".join(new_map[node["id"]])
        #    node["label"] = str(node['id'])
        #    if node["id"] == 32590:
        #        node["label"] = "Valve ASN"+str(node["id"])

        #    if node["id"] == 49544:
        #        node["label"] = "Ubisoft ASN"+str(node["id"])

        #    if node["id"] == 57976:
        #        node["label"] = "Blizzard ASN"+str(node["id"])

        #for edge in net.get_edges():
        #    if (edge['from'] == 34643) and (edge['to'] == 9186):
        #        print("Setting weight for first edge: %s" % edge)
        #        rtt = ubisoft_aspath_rtt[34643]['rtt']
        #        print("RTT from %s to %s: %s" %(edge['from'],edge['to'], rtt))
        #        edge["width"] = float((1/rtt)*10)
        #        edge["title"] = str(rtt)+' ms'

        #    if (edge['from'] == 9186) and (edge['to'] == 13156):
        #        print("Setting weight for first edge: %s" % edge)
        #        rtt = ubisoft_aspath_rtt[9186]['rtt']
        #        print("RTT from %s to %s: %s" %(edge['from'],edge['to'], rtt))
        #        edge["width"] = float((1/rtt)*10)
        #        edge["title"] = str(rtt)+' ms'

        #    if (edge['from'] == 13156) and (edge['to'] == 6939):
        #        print("Setting weight for first edge: %s" % edge)
        #        rtt = ubisoft_aspath_rtt[13156]['rtt']
        #        print("RTT from %s to %s: %s" %(edge['from'],edge['to'], rtt))
        #        edge["width"] = float((1/rtt)*10)
        #        edge["title"] = str(rtt)+' ms'

        #    if (edge['from'] == 13156) and (edge['to'] == 174):
        #        print("Setting weight for first edge: %s" % edge)
        #        rtt = blizzard_aspath_rtt[13156]['rtt']
        #        print("RTT from %s to %s: %s" %(edge['from'],edge['to'], rtt))
        #        edge["width"] = float((1/rtt)*10)
        #        edge["title"] = str(rtt)+' ms'
        #net.show('/scratch/measurements/analysis/Probe-And-ASpaths/'+str(asn)+'annotated'+'.html')



