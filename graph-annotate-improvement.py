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

caida_prefix2as = "https://publicdata.caida.org/datasets/routing/routeviews-prefix2as/2022/09/routeviews-rv2-20220920-1200.pfx2as.gz"


def getResults(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    mresp = requests.get(url)
    data = mresp.json()
    res_url = data['result']
    res_data = requests.get(res_url)
    results = res_data.json()
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

def rtt_to_aspath(res, aspaths, valve,
                  ubisoft, blizzard, ip2asn, pyt):
    valve_path_rtt = {}
    ubisoft_path_rtt = {}
    blizzard_path_rtt = {}
    common_path_rtt = {}
    for aspath in aspaths:
        if aspath[-1] == 32590
            for asn in aspath: 
                valve_path_rtt[asn] = '0ms'

        if aspath[-1] == 49544
            for asn in aspath: 
                ubisoft_path_rtt[asn] = '0ms'

        if aspath[-1] == 57976
            for asn in aspath: 
                blizzard_path_rtt[asn] = '0ms'

    trace1 = res[0]
    hops = trace1['result']
    hop_dict_med = {}
    for hop in hops:
        hop_nop = hop['hop']
        try:
            hop_results = hop['result']
        except KeyError:
            continue
        rtts = []
        hop_ip_addrs = set()
        for rtt_to_hop in hop_results:
            try:
                hop_ip_addrs.add(rtt_to_hop['from'])
            except KeyError:
                continue

            try:
                rtts.append(rtt_to_hop['rtt'])
            except KeyError:
                continue


        if len(hop_ip_addrs) > 1:
            hop_asn = set()
            for hop_ip_addr in hop_ip_addrs:
                try:
                    hopAddr = ipaddress.ip_address(hop_ip_addr)
                except ValueError:
                    continue
                
                if hopAddr.is_global:
                    if hop_ip_addr in ip2asn:
                        hop_asn.append(ip2asn[hop_ip_addr])
                    else: 
                        asn = pyt.get(hop_ip_addr)
                        if asn in not None:
                            hop_asn.append(asn)
        else:
            try:
                hopAddr = ipaddress.ip_address(hop_ip_addrs[0])
            except ValueError:
                continue
            
            if hopAddr.is_global:
                if hop_ip_addrs[0] in ip2asn:
                    hop_asn.append(ip2asn[hop_ip_addrs[0]])
                else: 
                    asn = pyt.get(hop_ip_addrs[0])
                    if asn in not None:
                        hop_asn.append(asn)
        hop_dict_med['hop'] = hop_nop
        hop_dict_med['asn'] = hop_asn
        if len(rtts) > 1:
            hop_dict_med['median rtt'] = np.median(rtts)



if __name__ == "__main__":

    msm_list = []
    with open('/scratch/measurements/traceroute/trace-measurements-for-filtered-probes.json', 'r') as msms:
        msm_list.extend(json.load(msms))

    with open('/scratch/measurements/traceroute/trace-measurements-for-icmp-traces-to-blizzard-for-filtered-probes.json', 'r') as bmsms:
        msm_list.extend(json.load(bmsms))

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
        results = getResults(msm) 
        target = getMsmTarget(msm)

        if target == "162.254.197.36":

            for result in results:
                if result["prb_id"] in TraceMSMToValve:
                    TraceMSMToValve[result["prb_id"]].append(result)
                else:
                    TraceMSMToValve[result["prb_id"]] = [result]
        
        if target == "185.60.112.157":
            
            for result in results:
                if result["proto"] != "ICMP":
                    continue

                if result["prb_id"] in Blizzard_prb_msm:
                    TraceMSMToBlizzard[result["prb_id"]].append(result)
                else:
                    TraceMSMToBlizzard[result["prb_id"]] = [result]

        if target == "5.200.20.245":

            for result in results:
                if result["prb_id"] in Ubisoft_prb_msm:
                    TraceMSMToUbisoft[result["prb_id"]].append(result)
                else:
                    TraceMSMToUbisoft[result["prb_id"]] = [result]

    for asn, vals in commonASNsandProbes.items()
        if asn not in ASNsWithDisjointPaths:
            continue

        for val in vals:
            (val_key, val_val), = val.items() 
            if val_key != 'disjointed': 
                prb_id = val_key
                aspaths = val_val

                valve = TraceMSMToValve[prb_id] 
                blizzard = TraceMSMToBlizzard[prb_id]
                ubisoft = TraceMSMToUbisoft[prb_id]



        
        
