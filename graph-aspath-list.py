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



        
    #originASNs =  list(ASNofAllProbesClean.keys())
    for asn in probe_isps:
        if nx.has_path(g2, asn, 1299):
            paths =  nx.all_simple_paths(g2, asn, 1299)
            aspaths = []
            #paths = nx.all_shortest_paths(g2, asn, 1299)
            print("Paths between ASN %s and ASN %s" % (asn, '1299'))
            i = 0
            asn_hop = set()
            for path in paths:
                if 49544 in path:
                    continue

                if 32590 in path: 
                    continue

                if 57976 in path:
                    continue

                if 3356 in path:
                    continue

                if 6939 in path:
                    continue

                print("      PATH: %s" % path)
                i += 1
                for asno in path:
                    asn_hop.add(asno)
                aspaths.append(path)
            if i != 0:
                multigraph = nx.MultiDiGraph()
                last_asn_set = set()
                for path in aspaths:
                    last_asn = path[-2]
                    if last_asn in last_asn_set:
                        continue

                    last_asn_set.add(last_asn)

                    for asno in path:
                        index = path.index(asno)
                        next_id = index + 1 
                        if next_id != len(path):
                            multigraph.add_edge(asno, path[next_id])
                    n = 3
                    while (len(path) - n) > 1:
                        next_asn = path[-n]
                        if nx.has_path(g2, next_asn, 1299):
                            npaths = nx.all_simple_paths(g2, next_asn, 1299)
                            for npath in npaths:
                                if npath[-2] == last_asn:
                                    continue
                                for asno in npath:
                                    index = npath.index(asno)
                                    next_id = index + 1
                                    if next_id != len(npath):
                                        multigraph.add_edge(asno, npath[next_id])
                        n += 1
                #print("Node in multigraph: %s" %nx.number_of_nodes(multigraph))
                #nx.draw(multigraph, connectionstyle='arc3, rad = 0.1')
                #plt.show()
                #pyvisualise(multigraph, str(asn))
                fig = gv.vis(multigraph, show_node_label=True, show_edge_label=False)
                fig.display()
                 
            print("\n")
        else:
            print("No paths found between ASN %s and ASN %s" %(asn, '1299'))

            

