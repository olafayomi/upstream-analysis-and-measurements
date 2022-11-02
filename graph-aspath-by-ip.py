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
import gravis as gv
from datetime import datetime

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
    #net.toggle_physics(True)
    #net.show_buttons(filter_=True)
    opts = '''
        var options = {
          "physics": {
             "forceAtlas2Based": {
               "gravitationalConstant": -100,
               "centralGravity": 0.11,
               "springLength": 100,
               "springConstant": 0.09,
               "avoidOverlap": 1
             },
             "minVelocity": 0.75,
             "solver": "forceAtlas2Based",
             "timestep": 0.22
          }
        }'''
    net.set_options(opts)
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
    #net.set_edge_smooth('dynamic')
    #return net
    net.show('/scratch/measurements/analysis/Probe-And-ASpaths/multigraphs-probe-isps/'+(name)+'.html')


def seperateEdges(graph):
    red = []
    blue = []
    green = []
    for edge in list(graph.edges):
        data = graph.get_edge_data(edge[0], edge[1])
        if data['color'] == 'red':
            red.append(edge)

        if data['color'] == 'blue':
            blue.append(edge)

        if data['color'] == 'green':
            green.append(edge)

    return red, blue, green


def drawTopoGraph(graph, mgraph):
    plt.subplot(111)
    nodeList = list(graph.nodes)
    pos = nx.spring_layout(graph)
    nodes = nx.draw_networkx_nodes(graph, pos)
    red , blue, green  = seperateEdges(mgraph)
    edge_colors = ['r' if edge in red else 'g' if edge in green else 'b' for edge in graph.edges]
    #edges = graph.edges()
    nodes.set_edgecolor('black')
    nx.draw_networkx_edges(graph, pos)
    nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, min_source_margin=5, min_target_margin=5 )
    nodeList = list(graph.nodes)
    labels = {}
    for node in  nodeList:
        labels[node] = str(node)
    nx.draw_networkx_labels(graph, pos, labels, font_weight='bold')
    plt.show()


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
                        asn_to_hops[asn] = {hop_nop: {'rtt': rtts,
                                                      'median rtt': median,
                                                      'hop ip': [hop_ip]}}
                    else:
                        if hop_nop not in asn_to_hops[asn]:
                            asn_to_hops[asn][hop_nop] = {'rtt': rtts,
                                                         'median rtt': median,
                                                         'hop ip': [hop_ip]}
                        else:
                            asn_to_hops[asn][hop_nop]['hop ip'].append(hop_ip)

    print("ASN to hops for PROBE %s in MSM%s: %s" % (prb_id, msm_id, asn_to_hops))
    last_hop_asn = {}
    for asn, hops in asn_to_hops.items():
        hops_list = list(hops.keys())
        print("ASN %s has the following hops: %s" % (asn, hops_list))
        print("The last hop in ASN %s is %s" % (asn, max(hops_list)))
        print("Median RTT to last hop in ASN %s is %s"
              % (asn, asn_to_hops[asn][max(hops_list)]['median rtt']))


def rtt_to_aspath2(hops, ip2asn, pyt):
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
                all_ips.add(hop_ip)
                asn = None
                if hop_ip in ip2asn:
                    asn = ip2asn[hop_ip]
                else:
                    asn = pyt.get(hop_ip)
                if asn is not None:
                    
                    if not isinstance(asn, int):
                        asn = int(asn)
                        if float(asn) < 0:
                            continue

                    if asn not in asn_to_hops:
                        asn_to_hops[asn] = {hop_nop: {'rtt': rtts,
                                                      'median rtt': median,
                                                      'hop ip': [hop_ip]}}
                    else:
                        if hop_nop not in asn_to_hops[asn]:
                            asn_to_hops[asn][hop_nop] = {'rtt': rtts,
                                                         'median rtt': median,
                                                         'hop ip': [hop_ip]}
                        else:
                            asn_to_hops[asn][hop_nop]['hop ip'].append(hop_ip)

    return asn_to_hops


if __name__ == "__main__":

    all_ips = set()
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
    ASNofAllProbes = GetASNFromProbes(AllValid, valve_aspaths_from_prb,
                                      ubisoft_aspaths_from_prb,
                                      blizzard_aspaths_from_prb)

    g1 = createGraph(ASNofAllProbes, valve_aspaths_from_prb,
                    ubisoft_aspaths_from_prb, blizzard_aspaths_from_prb)

    aspathprbclean = aspathcleanup(aspath2prb_valid)
    valve_aspaths_clean = aspathprbclean['Valve']
    ubisoft_aspaths_clean = aspathprbclean['Ubisoft']
    blizzard_aspaths_clean = aspathprbclean['Blizzard']
    prb_asns_valve_clean = fetchOriginASN(valve_aspaths_clean)
    prb_asns_ubisoft_clean = fetchOriginASN(ubisoft_aspaths_clean)
    prb_asns_blizzard_clean = fetchOriginASN(blizzard_aspaths_clean)
    CommonProbesClean, AllValidClean  = GetProbes(aspathprbclean)
    ASNofAllProbesClean = GetASNFromProbes(AllValidClean, valve_aspaths_clean,
                                           ubisoft_aspaths_clean,
                                           blizzard_aspaths_clean)

    g2 = createGraph(ASNofAllProbesClean, valve_aspaths_clean,
                    ubisoft_aspaths_clean, blizzard_aspaths_clean)

    if nx.utils.graphs_equal(g1, g2):
        print("Yes, they are equal")

    if nx.is_isomorphic(g1, g2):
        print("They are isomorphic")
    #pprint(aspathprbclean)
    probe_isps = set()
    for server, prbs in aspathprbclean.items():
        for prb in prbs:
            (prb_id, aspaths), = prb.items()
            for aspath in aspaths:
                probe_isps.add(aspath[1])

    IPGraphs = nx.MultiDiGraph()
    mismatched = set()
    for msm in msm_list:
        for result in msm:
            if str(result["prb_id"]) not in AllValid:
                continue

            if result["dst_name"] == "185.60.112.157":
                
                if result["proto"] != "ICMP":
                    continue
            msm_id = result["msm_id"]
            prb_id = result["prb_id"]
            prb_src_addr = result["from"]
            prb_act_src = result["src_addr"]
            dst = result["dst_name"]
            all_ips.add(dst)
            all_ips.add(prb_src_addr)
            timestamp = datetime.utcfromtimestamp(
                                result["stored_timestamp"]).strftime(
                                                    '%Y-%m-%d %H:%M:%S')
            hops = result['result']
            asn_to_hops = rtt_to_aspath2(hops, ip2asn, pyt)
            for asn, prb_ids in ASNofAllProbes.items():
                if str(prb_id) in prb_ids:
                    prb_asn = asn
                    break

            prb_src_ip_asn = None
            if prb_src_addr in ip2asn:
                prb_src_ip_asn =  ip2asn[prb_src_addr]
            else:
                prb_src_ip_asn = pyt.get(prb_src_addr)

            if prb_src_ip_asn != str(prb_asn):
                prb_src_ip_asn = prb_asn

            if not IPGraphs.has_node(prb_src_addr): 
                IPGraphs.add_node(prb_src_addr,
                                  asn=prb_asn,
                                  probe=prb_id,
                                  destination=[dst],
                                  time=[timestamp],
                                  msm_id=[msm_id])
            else:
                IPGraphs.nodes[prb_src_addr]['destination'].append(dst)
                IPGraphs.nodes[prb_src_addr]['time'].append(timestamp)
                IPGraphs.nodes[prb_src_addr]['msm_id'].append(msm_id)

            i = 0
            for hop_asn, hops in asn_to_hops.items():
                if i == 0:
                    k = 0
                    for hop_no, hop_vals in hops.items():
                        median_rtt = hop_vals['median rtt']
                        hop_ips = hop_vals['hop ip']
                        for addr in hop_ips:
                            if not IPGraphs.has_node(addr):
                                IPGraphs.add_node(addr,
                                                  asn=hop_asn,
                                                  probe=[prb_id],
                                                  destination=[dst],
                                                  time=[timestamp],
                                                  msm_id=[msm_id])
                            else:
                                IPGraphs.nodes[addr]['probe'].append(prb_id)
                                IPGraphs.nodes[addr]['destination'].append(dst)
                                IPGraphs.nodes[addr]['time'].append(timestamp)
                                IPGraphs.nodes[addr]['msm_id'].append(msm_id)

                            if k == 0:
                                IPGraphs.add_edge(prb_src_addr, addr,
                                                  rtt=median_rtt,
                                                  probe=prb_id,
                                                  destination=dst,
                                                  timestamp=timestamp,
                                                  msm_id=msm_id)
                                #previous = (hop_no, hop_asn, hop_ips, med_rtt)
                            else:
                                prv_hop, prv_hop_asn, prv_hop_ips, prv_med_rtt = previous
                                hop_rtt = median_rtt - prv_med_rtt
                                for prv_ip in prv_hop_ips:
                                    IPGraphs.add_edge(prv_ip, addr,
                                                      rtt=abs(hop_rtt),
                                                      probe=prb_id,
                                                      destination=dst,
                                                      timestamp=timestamp,
                                                      msm_id=msm_id)
                        previous = (hop_no, hop_asn, hop_ips, median_rtt)
                        k += 1
                else:
                    for hop_no, hop_vals in hops.items():
                        median_rtt = hop_vals['median rtt']
                        hop_ips = hop_vals['hop ip']
                        for addr in hop_ips:
                            if not IPGraphs.has_node(addr):
                                IPGraphs.add_node(addr,
                                                  asn=hop_asn,
                                                  probe=[prb_id],
                                                  destination=[dst],
                                                  time=[timestamp],
                                                  msm_id=[msm_id])
                            else:
                                IPGraphs.nodes[addr]['probe'].append(prb_id)
                                IPGraphs.nodes[addr]['destination'].append(dst)
                                IPGraphs.nodes[addr]['time'].append(timestamp)
                                IPGraphs.nodes[addr]['msm_id'].append(msm_id)

                            prv_hop, prv_hop_asn, prv_hop_ips, prv_med_rtt = previous
                            hop_rtt = median_rtt - prv_med_rtt
                            for prv_ip in prv_hop_ips:
                                IPGraphs.add_edge(prv_ip, addr,
                                                  rtt=abs(hop_rtt),
                                                  probe=prb_id,
                                                  destination=dst,
                                                  timestamp=timestamp,
                                                  msm_id=msm_id)
                        previous = (hop_no, hop_asn, hop_ips, median_rtt)
                i += 1


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

    probe_with_alt_paths = set()
    for prb in valve_aspaths_clean:       
        (probe_id, aspaths), = prb.items()
        prb_msms = TraceMSMToValve[int(probe_id)]
        prbDiGraph = nx.MultiDiGraph()
        for result in prb_msms:
            msm_id = result["msm_id"]
            prb_id = result["prb_id"]
            prb_src_addr = result["from"]
            prb_act_src = result["src_addr"]
            dst = result["dst_name"]
            timestamp = datetime.utcfromtimestamp(
                                result["stored_timestamp"]).strftime(
                                                    '%Y-%m-%d %H:%M:%S')
            hops = result['result']
            asn_to_hops = rtt_to_aspath2(hops, ip2asn, pyt)
            for asn, prb_ids in ASNofAllProbes.items():
                if str(prb_id) in prb_ids:
                    prb_asn = asn
                    break

            prb_src_ip_asn = None
            if prb_src_addr in ip2asn:
                prb_src_ip_asn =  ip2asn[prb_src_addr]
            else:
                prb_src_ip_asn = pyt.get(prb_src_addr)

            if prb_src_ip_asn != str(prb_asn):
                prb_src_ip_asn = prb_asn

            if not prbDiGraph.has_node(prb_src_addr): 
                prbDiGraph.add_node(prb_src_addr,
                                    asn=prb_asn,
                                    probe=prb_id,
                                    destination=[dst],
                                    time=[timestamp],
                                    msm_id=[msm_id])
            else:
                prbDiGraph.nodes[prb_src_addr]['destination'].append(dst)
                prbDiGraph.nodes[prb_src_addr]['time'].append(timestamp)
                prbDiGraph.nodes[prb_src_addr]['msm_id'].append(msm_id)

            i = 0
            for hop_asn, hops in asn_to_hops.items():
                if i == 0:
                    k = 0
                    for hop_no, hop_vals in hops.items():
                        median_rtt = hop_vals['median rtt']
                        hop_ips = hop_vals['hop ip']
                        for addr in hop_ips:
                            if not prbDiGraph.has_node(addr):
                                    prbDiGraph.add_node(addr,
                                                        asn=hop_asn,
                                                        probe=[prb_id],
                                                        destination=[dst],
                                                        time=[timestamp],
                                                        msm_id=[msm_id])
                            else:
                                prbDiGraph.nodes[addr]['probe'].append(prb_id)
                                prbDiGraph.nodes[addr]['destination'].append(dst)
                                prbDiGraph.nodes[addr]['time'].append(timestamp)
                                prbDiGraph.nodes[addr]['msm_id'].append(msm_id)
                                
                            if k == 0:
                                prbDiGraph.add_edge(prb_src_addr, addr,
                                                    rtt=median_rtt,
                                                    probe=prb_id,
                                                    destination=dst,
                                                    timestamp=timestamp,
                                                    msm_id=msm_id)
                            
                            else:
                                prv_hop, prv_hop_asn, prv_hop_ips, prv_med_rtt = previous
                                hop_rtt = median_rtt - prv_med_rtt
                                for prv_ip in prv_hop_ips:
                                    prbDiGraph.add_edge(prv_ip, addr,
                                                        rtt=abs(hop_rtt),
                                                        probe=prb_id,
                                                        destination=dst,
                                                        timestamp=timestamp,
                                                        msm_id=msm_id)
                        previous = (hop_no, hop_asn, hop_ips, median_rtt)
                        k += 1
                else:
                    for hop_no, hop_vals in hops.items():
                        median_rtt = hop_vals['median rtt']
                        hop_ips = hop_vals['hop ip']
                        for addr in hop_ips:
                            if not prbDiGraph.has_node(addr):
                                prbDiGraph.add_node(addr,
                                                    asn=hop_asn,
                                                    probe=[prb_id],
                                                    destination=[dst],
                                                    time=[timestamp],
                                                    msm_id=[msm_id])
                            else:
                                prbDiGraph.nodes[addr]['probe'].append(prb_id)
                                prbDiGraph.nodes[addr]['destination'].append(dst)
                                prbDiGraph.nodes[addr]['time'].append(timestamp)
                                prbDiGraph.nodes[addr]['msm_id'].append(msm_id)

                            prv_hop, prv_hop_asn, prv_hop_ips, prv_med_rtt = previous
                            hop_rtt = median_rtt - prv_med_rtt
                            for prv_ip in prv_hop_ips:
                                prbDiGraph.add_edge(prv_ip, addr,
                                                    rtt=abs(hop_rtt),
                                                    probe=prb_id,
                                                    destination=dst,
                                                    timestamp=timestamp,
                                                    msm_id=msm_id)
                        previous = (hop_no, hop_asn, hop_ips, median_rtt)
                i += 1

        
        result = prb_msms[0]
        prbSubGraph =  nx.DiGraph()
        msm_id = result["msm_id"]
        prb_id = result["prb_id"]
        prb_src_addr = result["from"]
        prb_act_src = result["src_addr"]
        dst = result["dst_name"]
        timestamp = datetime.utcfromtimestamp(
                            result["stored_timestamp"]).strftime(
                                                '%Y-%m-%d %H:%M:%S')
        hops = result['result']
        asn_to_hops = rtt_to_aspath2(hops, ip2asn, pyt)
        for asn, prb_ids in ASNofAllProbes.items():
            if str(prb_id) in prb_ids:
                prb_asn = asn
                break

        prb_src_ip_asn = None
        if prb_src_addr in ip2asn:
            prb_src_ip_asn =  ip2asn[prb_src_addr]
        else:
            prb_src_ip_asn = pyt.get(prb_src_addr)

        if prb_src_ip_asn != str(prb_asn):
            prb_src_ip_asn = prb_asn

        if not prbSubGraph.has_node(prb_src_addr): 
            prbSubGraph.add_node(prb_src_addr,
                                 asn=prb_asn,
                                 probe=prb_id,
                                 destination=[dst],
                                 time=[timestamp],
                                 msm_id=[msm_id])
        else:
            prbSubGraph.nodes[prb_src_addr]['destination'].append(dst)
            prbSubGraph.nodes[prb_src_addr]['time'].append(timestamp)
            prbSubGraph.nodes[prb_src_addr]['msm_id'].append(msm_id)
        i = 0

        for hop_asn, hops in asn_to_hops.items():

            if i == 0:
                k = 0
                for hop_no, hop_vals in hops.items():
                    median_rtt = hop_vals['median rtt']
                    hop_ips = hop_vals['hop ip']
                    for addr in hop_ips:
                        if not prbSubGraph.has_node(addr):
                            prbSubGraph.add_node(addr,
                                                 asn=hop_asn,
                                                 probe=[prb_id],
                                                 hop=hop_no,
                                                 destination=[dst],
                                                 time=[timestamp],
                                                 msm_id=[msm_id])
                        else:
                            prbSubGraph.nodes[addr]['probe'] = [prb_id]
                            prbSubGraph.nodes[addr]['destination'] = [dst]
                            prbSubGraph.nodes[addr]['time'] = [timestamp]
                            prbSubGraph.nodes[addr]['msm_id'] = [msm_id]
                            
                        if k == 0:
                            prbSubGraph.add_edge(prb_src_addr, addr,
                                                 rtt=median_rtt,
                                                 probe=prb_id,
                                                 destination=dst,
                                                 timestamp=timestamp,
                                                 msm_id=msm_id)
                        
                        else:
                            prv_hop, prv_hop_asn, prv_hop_ips, prv_med_rtt = previous
                            hop_rtt = median_rtt - prv_med_rtt
                            for prv_ip in prv_hop_ips:
                                prbSubGraph.add_edge(prv_ip, addr,
                                                     rtt=abs(hop_rtt),
                                                     probe=prb_id,
                                                     destination=dst,
                                                     timestamp=timestamp,
                                                     msm_id=msm_id)
                    if '162.254.197.36' not in hop_ips: 
                        previous = (hop_no, hop_asn, hop_ips, median_rtt)
                    k += 1

            else:
                prv_hop, prv_hop_asn, prv_hop_ips, prv_med_rtt = previous
                if (hop_asn == 32590) and (prv_hop_asn != 32590):
                    gsProviderLastHop = (prv_hop_ips[0], prv_hop_asn)

                for hop_no, hop_vals in hops.items():
                    median_rtt = hop_vals['median rtt']
                    hop_ips = hop_vals['hop ip']
                    for addr in hop_ips:
                        if not prbSubGraph.has_node(addr):
                            prbSubGraph.add_node(addr,
                                                 asn=hop_asn,
                                                 probe=[prb_id],
                                                 hop=hop_no,
                                                 destination=[dst],
                                                 time=[timestamp],
                                                 msm_id=[msm_id])
                        else:
                            prbSubGraph.nodes[addr]['probe'] = [prb_id]
                            prbSubGraph.nodes[addr]['destination'] = [dst]
                            prbSubGraph.nodes[addr]['time'] = [timestamp]
                            prbSubGraph.nodes[addr]['msm_id'] = [msm_id]

                        prv_hop, prv_hop_asn, prv_hop_ips, prv_med_rtt = previous
                        hop_rtt = median_rtt - prv_med_rtt
                        for prv_ip in prv_hop_ips:
                            prbSubGraph.add_edge(prv_ip, addr,
                                                 rtt=abs(hop_rtt),
                                                 probe=prb_id,
                                                 destination=dst,
                                                 timestamp=timestamp,
                                                 msm_id=msm_id)
                    if '162.254.197.36' not in hop_ips:
                        previous = (hop_no, hop_asn, hop_ips, median_rtt)
            i += 1
        print("For probe %s in ASN %s with IP address %s, the lasthop before Valve network is: %s" %(prb_id,prb_asn, prb_src_addr, (gsProviderLastHop,)))
        gsProviderLHip, gsProviderAsn = gsProviderLastHop
        try:
            path = nx.shortest_path(prbSubGraph, prb_src_addr, gsProviderLHip)
            #path = nx.shortest_path(prbDiGraph, prb_src_addr, gsProviderLHip)
        except nx.exception.NodeNotFound:
            print("Funky path between Probe %s with IP %s and provider hop %s in ASN %s"
                  %(prb_id, prb_src_addr, gsProviderLHip, gsProviderAsn))
            continue
        if path:
            n = 3
            penultimateIPset = set()
            penultimateIPset.add(path[-2])
            print("Primary  path: %s" %path)
            while (len(path) - n) > 1:
                ipHop = path[-n] 
                if nx.has_path(IPGraphs, ipHop, gsProviderLHip):
                    alt_paths = nx.all_shortest_paths(IPGraphs, ipHop, gsProviderLHip)
                    prbDiverseProviderPathGraph = prbSubGraph
                    for altpath in alt_paths:

                        if '185.60.112.157' in altpath:
                            continue

                        if '5.200.20.245' in altpath:
                            continue

                        if '162.254.197.36' in altpath:
                            continue
                        
                        for pathAddr in altpath:
                            pathAddrAsn = IPGraphs.nodes[pathAddr]['asn']
                            if isinstance(pathAddrAsn, str):
                                if int(pathAddrAsn) == 57976:
                                    continue

                                if int(pathAddrAsn) == 49544:
                                    continue

                                if int(pathAddrAsn) == 32590:
                                    continue
                            else:
                                if pathAddrAsn == 57976:
                                    continue

                                if pathAddrAsn == 49544:
                                    continue

                                if pathAddrAsn == 32590:
                                    continue


                        #if altpath[-2] in penultimateIPset:
                        if all(addr in altpath for addr in penultimateIPset):
                            continue
                        
                        print("       Alternate path from %s to %s: %s" %(ipHop, gsProviderLHip, altpath))
                        altpath_edges = list(nx.utils.pairwise(altpath))
                        print("       Edges of alternate from %s to %s: %s" %(ipHop, gsProviderLHip,altpath_edges))
                        for edge in altpath_edges:
                            data = IPGraphs.get_edge_data(*edge)
                            addrA, addrB = edge

                            if not prbDiverseProviderPathGraph.has_node(addrA):
                                prbDiverseProviderPathGraph.add_node(addrA,
                                                                     asn=IPGraphs.nodes[addrA]['asn'],
                                                                     probe=IPGraphs.nodes[addrA]['probe'],
                                                                     destination=IPGraphs.nodes[addrA]['destination'],
                                                                     time=IPGraphs.nodes[addrA]['time'],
                                                                     msm_id=IPGraphs.nodes[addrA]['msm_id'])

                            if not prbDiverseProviderPathGraph.has_node(addrB):
                                prbDiverseProviderPathGraph.add_node(addrB,
                                                                     asn=IPGraphs.nodes[addrB]['asn'],
                                                                     probe=IPGraphs.nodes[addrB]['probe'],
                                                                     destination=IPGraphs.nodes[addrB]['destination'],
                                                                     time=IPGraphs.nodes[addrB]['time'],
                                                                     msm_id=IPGraphs.nodes[addrB]['msm_id'])

                            if len(data) == 1:
                                (num, attrs), = data.items()
                                best_attr = attrs
                            else: 
                                best_attr = data[0]
                                for num_attr, attrs in data.items():
                                    rtt = attrs['rtt'] 
                                    if rtt < best_attr['rtt']:
                                        best_attr = attrs
                            if not prbDiverseProviderPathGraph.has_edge(*edge):
                                prbDiverseProviderPathGraph.add_edge(addrA, addrB, 
                                                                     rtt=best_attr['rtt'],
                                                                     probe=best_attr['probe'],
                                                                     destination=best_attr['destination'],
                                                                     timestamp=best_attr['timestamp'],
                                                                     msm_id=best_attr['msm_id'])


                        #penultimateIPset.add(altpath[-2])
                        for ipaddr in altpath:
                            penultimateIPset.add(ipaddr)
                        probe_with_alt_paths.add(prb_id)
                n += 1
        if prb_id in  probe_with_alt_paths:     
            net = Network(height="1000px", width="100%", notebook=True, directed=True)
            net.toggle_physics(True)
            net.show_buttons(filter_=True)
            net.from_nx(prbDiverseProviderPathGraph)
            neigh_map = net.get_adj_list()
            new_map = {}
    
            for node, neigh in neigh_map.items():
                new_set = set()
                for n in neigh:
                    new_set.add(str(n))
                new_map[node] = new_set

            for node in net.nodes:
                #print(node)
                dest = set(node['destination'])
                msm_id = [str(x) for x in node['msm_id']]
                if isinstance(node['probe'], list):
                    prbs = set(node['probe'])
                    prb_id = [str(x) for x in prbs]
                else:
                    prb_id = [str(node['probe'])]


                node["title"] = "ASN"+str(node['asn']) + "\nIP: "+ node['id'] + "\n Destination: "+" ".join(dest) + "\n time:" + "\n".join(node['time']) + "\n MSM ID:" + "\n".join(msm_id)+ "\nProbe:" +"\n".join(prb_id)+"\n Neighbors:\n\n"+"\n".join(new_map[node["id"]])

                node["label"] = "ASN"+str(node['asn'])
                #+"\nIP: "+node['id']
                #print(node)
            for edge in net.get_edges():
                #edge["label"] = str(edge['rtt'])+' ms'

                try:
                    pred = edge['from']
                except KeyError:
                    pred = ''

    
                try:
                    succ = edge['to']
                except KeyError:
                    succ = ''
                prb = str(edge['probe'])
                msm_id = str(edge['msm_id'])

                edge["title"] = "RTT: "+str(edge['rtt'])+"ms\n"+pred +" -> "+ succ +"\n Probe: "+prb+"\nMSM ID: "+msm_id+"\n Timestamp: "+edge['timestamp']+"\n Destination: "+edge['destination']
                #print(edge)
            print("Writing html for: %s" % probe_id)
            name= 'probe'+str(prb_id)
            net.set_edge_smooth('dynamic')
            net.show('/scratch/measurements/analysis/probes-to-valve-latency-visualisation-diverse-paths/'+probe_id+'.html')
            
    print("Using shortest_path algo without weights, there are %s probes with alt paths" %len(probe_with_alt_paths))
    #for msm in msm_list:
    #    for result in msm:
    #        if str(result["prb_id"]) not in AllValid:
    #            continue

    #        if result["dst_name"] == "185.60.112.157":
    #            
    #            if result["proto"] != "ICMP":
    #                continue
    #        msm_id = result["msm_id"]
    #        prb_id = result["prb_id"]
    #        prb_src_addr = result["from"]
    #        prb_act_src = result["src_addr"]
    #        dst = result["dst_name"]
    #        timestamp = datetime.utcfromtimestamp(
    #                            result["stored_timestamp"]).strftime(
    #                                                '%Y-%m-%d %H:%M:%S')
    #        hops = result['result']
    #        asn_to_hops = rtt_to_aspath2(hops, ip2asn, pyt)
    #        for asn, prb_ids in ASNofAllProbes.items():
    #            if str(prb_id) in prb_ids:
    #                prb_asn = asn
    #                break

    #        prb_src_ip_asn = None
    #        if prb_src_addr in ip2asn:
    #            prb_src_ip_asn =  ip2asn[prb_src_addr]
    #        else:
    #            prb_src_ip_asn = pyt.get(prb_src_addr)

    #        if prb_src_ip_asn != str(prb_asn):
    #            prb_src_ip_asn = prb_asn

    #        



    #pprint(IPGraphs.nodes.data())
    #for node, attr in IPGraphs.nodes.data():
    #    if node == '162.254.197.36':
    #        print("Node: %s" %node)
    #        pprint(attr)
    #        print("\n")

    #print("There are %s nodes/IP addresses in the graph" % IPGraphs.number_of_nodes())
    #print("All IPs from measurements: %s" %len(all_ips))
    #for edge in IPGraphs.edges(data=True, keys=True):
    #    pprint(edge)
