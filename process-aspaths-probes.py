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
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from networkx import path_graph, random_layout
from pyvis.network import Network
import random
import csv


def seperateEdgesASRelData(graph):
    p2c_edges = []
    p2p_edges = []
    for edge in list(graph.edges):
        rel = graph.get_edge_data(edge[0],edge[1])
        #print("Attribute rel is %s\n" %rel) 
        if rel['relationship'] == 'p2c':
            p2c_edges.append(edge)

        if rel['relationship'] == 'p2p':
            p2p_edges.append(edge)
    return p2c_edges, p2p_edges


def pyvisualise(graph, asn):
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
    net.show('/scratch/measurements/analysis/Probe-And-ASpaths/pyvisualisation/'+str(asn)+'.html')


def readASRelData(ASRelDataFile):
    with open(ASRelDataFile, 'r') as f:
        try:
            ASRelData = csv.reader(f, delimiter='\t')
            graph = createGraph(ASRelData)
        except IndexError:
            ASRelData = csv.reader(f, delimiter='|')
            graph = createGraph(ASRelData)
        
    return graph


def createGraph(ASRelData):
    internetGraph = nx.DiGraph()
    for asRelLink in ASRelData:
        if asRelLink[2] != 'unknown':
            if (asRelLink[2] == 'p2c') or (asRelLink[2] == '-1'):
                internetGraph.add_edge(int(asRelLink[0]), int(asRelLink[1]),
                                       relationship='p2c')

            if (asRelLink[2] == 'c2p'):
                internetGraph.add_edge(int(asRelLink[1]), int(asRelLink[0]),
                                       relationship='p2c')

            if (asRelLink[2] == 'p2p') or (asRelLink[2] == '0'):
                internetGraph.add_edge(int(asRelLink[0]), int(asRelLink[1]),
                                       relationship='p2p')
                internetGraph.add_edge(int(asRelLink[1]), int(asRelLink[0]),
                                       relationship='p2p')
        else:
            internetGraph.add_edge(int(asRelLink[0]), int(asRelLink[1]),
                                   relationship='p2p')
            internetGraph.add_edge(int(asRelLink[1]), int(asRelLink[0]),
                                   relationship='p2p')

    #return internetGraph
    return internetGraph.reverse()


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
        
           

def drawTopoGraph(graph):
    plt.subplot(111)
    nodeList = list(graph.nodes)
    pos = nx.spring_layout(graph)
    nodes = nx.draw_networkx_nodes(graph, pos)
    red , blue, green  = seperateEdges(graph)
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


if __name__ == "__main__":

    with open('/scratch/measurements/aspath/aspath-for-trace-msms-to-ubisoft-and-valve-servers.json', 'r') as f:
        aspathsprb_v_and_u = json.load(f)

    with open('/scratch/measurements/aspath/aspath-for-trace-msms-to-blizzard-server.json', 'r') as f:
        aspathsprb_blizzard = json.load(f) 
        del aspathsprb_blizzard['Valve']
        del aspathsprb_blizzard['Ubisoft']

    
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
            print("\n")

        if server == 'Ubisoft':

            print("There are %s valid probes with AS paths to %s"
                  % (len(prbs), server))
            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                ubi_valid_prb.add(prb_id)
            print("\n")
        
        if server == 'Blizzard':

            print("There are %s valid probes with AS paths to %s"
                  % (len(prbs), server))
            for prb in prbs:
                (prb_id, aspaths), = prb.items()
                bliz_valid_prb.add(prb_id)
            print("\n")

    print("Number of probes in valve_valid_prb: %s" % len(valve_valid_prb))
    print("Number of probes in ubi_valid_prb: %s" % len(ubi_valid_prb))
    print("Number of probes in bliz_valid_prb: %s" % len(bliz_valid_prb))

    

    all_valid_probes_set = valve_valid_prb.union(ubi_valid_prb, bliz_valid_prb)
    print("Number of probes with valid AS path to the three game servers: %s\n" % len(all_valid_probes_set))
    common_probes_to_all_servers = set.intersection(valve_valid_prb, bliz_valid_prb, ubi_valid_prb)
    print("%s probes are common to the three game servers\n"  % len(common_probes_to_all_servers))


    valve_aspaths_from_prb = aspath2prb_valid['Valve']
    ubisoft_aspaths_from_prb = aspath2prb_valid['Ubisoft']
    blizzard_aspaths_from_prb = aspath2prb_valid['Blizzard']
    #penultimate_asn = set()
    prb_asns_valve = {}
    for prb in valve_aspaths_from_prb:
        (prb_id, aspaths), = prb.items()
        for aspath in aspaths:
            origin_asn = aspath[0]
            #if isinstance(aspath[-2], int):
            #    penultimate_asn.add(aspath[-2])
            if origin_asn not in prb_asns_valve:
                prb_asns_valve[origin_asn] = [prb_id]
            else: 
                if prb_id not in prb_asns_valve[origin_asn]:
                    prb_asns_valve[origin_asn].append(prb_id)

    prb_asns_ubisoft = {}
    for prb in ubisoft_aspaths_from_prb:
        (prb_id, aspaths), = prb.items()
        for aspath in aspaths:
            #if isinstance(aspath[-2], int):
            #    penultimate_asn.add(aspath[-2])
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
            #if isinstance(aspath[-2], int):
            #    penultimate_asn.add(aspath[-2])
            if origin_asn not in prb_asns_blizzard:
                prb_asns_blizzard[origin_asn] = [prb_id]
            else:
                if prb_id not in prb_asns_blizzard[origin_asn]:
                    prb_asns_blizzard[origin_asn].append(prb_id)

    asn_of_all_valid_probes = {}
    for prb_id in all_valid_probes_set:
        for prb in valve_aspaths_from_prb:
            (probe_id, aspaths), = prb.items()
            if probe_id != prb_id:
                continue
            for aspath in aspaths:
                origin_asn = aspath[0]
                if origin_asn not in asn_of_all_valid_probes:
                    asn_of_all_valid_probes[origin_asn] = [prb_id]
                else:
                    if prb_id not in asn_of_all_valid_probes[origin_asn]:
                        asn_of_all_valid_probes[origin_asn].append(prb_id)

        for prb in ubisoft_aspaths_from_prb:
            (probe_id, aspaths), = prb.items()
            if probe_id != prb_id:
                continue
            for aspath in aspaths:
                origin_asn = aspath[0]
                if origin_asn not in asn_of_all_valid_probes:
                    asn_of_all_valid_probes[origin_asn] = [prb_id]
                else:
                    if prb_id not in asn_of_all_valid_probes[origin_asn]:
                        asn_of_all_valid_probes[origin_asn].append(prb_id)

        for prb in blizzard_aspaths_from_prb:
            (probe_id, aspaths), = prb.items()
            if probe_id != prb_id:
                continue
            for aspath in aspaths:
                origin_asn = aspath[0]
                if origin_asn not in asn_of_all_valid_probes:
                    asn_of_all_valid_probes[origin_asn] = [prb_id]
                else:
                    if prb_id not in asn_of_all_valid_probes[origin_asn]:
                        asn_of_all_valid_probes[origin_asn].append(prb_id)
        
    print("Number of ASNs of all probes with valid AS paths to the three game servers: %s" % len(asn_of_all_valid_probes))
    print("Number of ASNs of all probes with valid AS paths to the three game servers: %s" % len(asn_of_all_valid_probes.keys()))

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
                #print("In ubisoft: probe_id: %s, prb_id: %s, path: %s" % (probe_id, prb_id, aspath))
                #if prb_id in ubi_valid_prb:
                #    print("Yes")
                if origin_asn not in asn_of_common_valid_probes:
                    asn_of_common_valid_probes[origin_asn] = [prb_id]
                else:
                    if prb_id not in asn_of_common_valid_probes[origin_asn]:
                        asn_of_all_valid_probes[origin_asn].append(prb_id)

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

    print("Number of ASNs of valid probes common to the three game servers: %s" % len(asn_of_common_valid_probes))
    print("Number of ASNs  of valid probes common to the three game servers: %s" %  len(asn_of_common_valid_probes.keys()))

    for asn, probes in asn_of_common_valid_probes.items():
        print("Paths from probes in ASN:%s" % asn)
        for probe in probes:
            print("   From Probe: %s" % probe)
            print("        To Blizzard:")
            for prb in blizzard_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe: 
                    continue
                for aspath in aspaths:
                    print("           %s" % aspath)

            print("        To Valve:")
            for prb in valve_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe:
                    continue 
                for aspath in aspaths:
                    print("           %s" % aspath)

            print("        To Ubisoft:")
            for prb in ubisoft_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe:
                    continue
                for aspath in aspaths:
                    print("          %s" % aspath)

        print("\n")

    pathasn = set()
    graph = nx.DiGraph()
    penultimate_asn = set()
    validPenultimateASNs = [1299, 3356, 6939]
    asnProbesForPenultimateASNs = {}
    for asn, probes in asn_of_common_valid_probes.items():
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
                    for asname in aspath:
                        pathasn.add(asname)
                        index = aspath.index(asname)
                        if index == (len(aspath) - 2):
                            penultimate_asn.add(asname)
                            if asname in validPenultimateASNs:
                                if asname not in asnProbesForPenultimateASNs:
                                    asnProbesForPenultimateASNs[asn] = [prb_id]
                                else:
                                    if prb_id not in asnProbesForPenultimateASNs[asn]:
                                        asnProbesForPenultimateASNs[asn].append(prb_id)
                        next_id = index + 1
                        if next_id != len(aspath):
                            graph.add_edge(asname, aspath[next_id], color='blue')


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
                    for asname in aspath:
                        pathasn.add(asname)
                        index = aspath.index(asname)
                        if index == (len(aspath) - 2):
                            penultimate_asn.add(asname)
                            if asname in validPenultimateASNs:
                                if asn not in asnProbesForPenultimateASNs:
                                    asnProbesForPenultimateASNs[asn] = [prb_id]
                                else:
                                    if prb_id not in asnProbesForPenultimateASNs[asn]:
                                        asnProbesForPenultimateASNs[asn].append(prb_id)
                        next_id = index + 1
                        if next_id != len(aspath):
                            graph.add_edge(asname, aspath[next_id], color='red')

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
                    for asname in aspath:
                        pathasn.add(asname)
                        index = aspath.index(asname)
                        if index == (len(aspath) - 2):
                            penultimate_asn.add(asname)
                            if asname in validPenultimateASNs:
                                if asn not in asnProbesForPenultimateASNs:
                                    asnProbesForPenultimateASNs[asn] = [prb_id]
                                else:
                                    if prb_id not in asnProbesForPenultimateASNs[asn]:
                                        asnProbesForPenultimateASNs[asn].append(prb_id)
                        next_id = index + 1
                        if next_id != len(aspath):
                            graph.add_edge(asname, aspath[next_id], color='green')
        #drawTopoGraph(graph)
    common_asn_probes_paths = {}
    asns_with_disjoint_paths = [3352, 12302, 13046, 15735, 20912, 24921, 34410, 34643, 48747,
                                56588, 58079, 62418, 199246, 201281, 201494, 208877, 212485]
    for asn, probes in asn_of_common_valid_probes.items():
        print("Paths from probes in ASN:%s" % asn)
        asns_set = set()
        common_asn_probes_paths[asn] = []
        for probe in probes:
            print("   From Probe: %s" % probe)
            print("        To Blizzard:")
            paths = []
            for prb in blizzard_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe: 
                    continue
                for aspath in aspaths:
                    str_elem = []
                    for elem in aspath:
                        if isinstance(elem, int):
                            asns_set.add(elem)
                        
                        if isinstance(elem, str):
                            str_elem.append(elem)

                    for str_e in str_elem:
                        aspath.remove(str_e)
                    print("           %s" % aspath)

                if len(aspaths) == 2:
                    if Counter(aspaths[0]) == Counter(aspaths[1]):
                        paths.append(aspaths[0])
                    else:
                        paths.append(aspaths[0])
                        paths.append(aspaths[1])
                else:
                    paths.append(aspaths[0])

            print("        To Valve:")
            for prb in valve_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe:
                    continue 
                for aspath in aspaths:
                    print("           %s" % aspath)
                    for elem in aspath:
                        if isinstance(elem, int):
                            asns_set.add(elem)

                        if isinstance(elem, str):
                            str_elem.append(elem)

                    for str_e in str_elem:
                        aspath.remove(str_e)
                    print("           %s" % aspath)

                if len(aspaths) == 2:
                    if Counter(aspaths[0]) == Counter(aspaths[1]):
                        paths.append(aspaths[0])
                    else:
                        paths.append(aspaths[0])
                        paths.append(aspaths[1])
                else:
                    paths.append(aspaths[0])

            print("        To Ubisoft:")
            for prb in ubisoft_aspaths_from_prb:
                (prb_id, aspaths), = prb.items()
                if prb_id != probe:
                    continue
                for aspath in aspaths:
                    print("          %s" % aspath)
                    for elem in aspath:
                        if isinstance(elem, int):
                            asns_set.add(elem)

                        if isinstance(elem, str):
                            str_elem.append(elem)

                    for str_e in str_elem:
                        aspath.remove(str_e)
                    print("           %s" % aspath)

                if len(aspaths) == 2:
                    if Counter(aspaths[0]) == Counter(aspaths[1]):
                        paths.append(aspaths[0])
                    else:
                        paths.append(aspaths[0])
                        paths.append(aspaths[1])
                else:
                    paths.append(aspaths[0])

            common_asn_probes_paths[asn].append({probe : paths})
        if asn in asns_with_disjoint_paths:
            common_asn_probes_paths[asn].append({'disjointed': True})
        else:
            common_asn_probes_paths[asn].append({'disjointed': False})

        subgraph1 = nx.subgraph(graph, asns_set)
        #pyvisualise(subgraph1, asn)
        subgraph2 = nx.induced_subgraph(graph, asns_set)
        #pyvisualise(subgraph1, asn)
       
        print("\n")

    pprint(common_asn_probes_paths)
    print("Numer of asns with disjoint paths to the game servers: %s" % len(asns_with_disjoint_paths))
    #with open('/scratch/measurements/aspath/probes-asn-paths-to-server/list-of-asns-and-probes-common-to-msms-to-the-three-game-servers-and-their-paths.json', 'w', encoding='utf-8') as f:
     #   json.dump(common_asn_probes_paths, f, ensure_ascii=False, indent=4)
    print("Number of all penultimate ASNs before game server ASNs: %s" % len(penultimate_asn))
    gameServerAsns = {57976, 32590, 49544}
    commonPenultimateAsn = set()
    for asn in penultimate_asn:
    
        successors = set(list(graph.successors(asn)))
        intersect = successors.intersection(gameServerAsns)
        if len(intersect) > 1:
            commonPenultimateAsn.add(asn)

        #check = all(elem in successors for elem in gameServerAsns)
        #if check:
            #print("ASN%s is connected to at least two game servers" %asn)
            #print("Successors of Penultimate ASN%s are: %s" %(asn, successors))
        #print("\n")
    print("Number of penultimate ASNs that are neighbours of two or all of the game server: %s" %len(commonPenultimateAsn))
    ASRelGraph = readASRelData("/scratch/20220901.as-rel2-filtered.txt")

    all_edges = []
    for edge in list(ASRelGraph.edges):
        all_edges.append(edge)

    for asn in commonPenultimateAsn:
        i = 0

        blizzard = (57976, asn)
        ubisoft =  (49544, asn)
        valve =   (32590, asn)
        if blizzard in all_edges:
            i += 1

        if ubisoft in all_edges:
            i += 1

        if valve in all_edges:
            i += 1

        if i == 3:
            print("ASN %s has edges with all three game servers" %asn)

        if i == 2:
            print("ASN %s has edges with just two game servers" %asn)


    print("ASN and their probes that have 1299,3356 and 6969 as penultimate ASN to the game servers")
    print("They are: %s" %asnProbesForPenultimateASNs)
    with open('/scratch/measurements/aspath/probes-asn-paths-to-server/asn-and-probes-with-1299-3356-6969-in-the-paths.json', 'w', encoding='utf-8') as f:
        json.dump(asnProbesForPenultimateASNs, f, ensure_ascii=False, indent=4)

    #for asn in commonPenultimateAsn:
    #    predecessors = set(list(ASRelGraph.predecessors(asn)))

    #    #check = all(elem in predecessors for elem in gameServerAsns)
    #    intersect = predecessors.intersection(gameServerAsns)
    #    print("ASN %s:" %asn)
    #    if len(intersect) > 1:
    #        print("Validated with the AS relationship data:")
    #        print("ASN %s is connected to the two or all game servers" %asn)
    #        #print("Successors of Penultimate ASN%s are: %s" %(asn, successors))
    #        print("\n")
    #    else:
    #        for serverASN in gameServerAsns:
    #            if nx.has_path(ASRelGraph, serverASN, asn):
    #                shortest_paths = nx.shortest_path(ASRelGraph, serverASN, asn)
    #                print("Shortest paths between %s and %s" %(serverASN, asn))
    #                for path in shortest_paths:
    #                    print(path)
    #            else:
    #                print("No path between %s and %s" %(serverASN, asn))
    #            print("\n")



        #print("ASN%s Successors: %s" %(asn, successors))

    #for asn in penultimate_asn:
    #    print("To Blizzard ASN 57976")
    #    if nx.has_path(graph, asn, 57976):
    #        shortest_paths = nx.all_shortest_paths(graph, asn, 57976)
    #        for path in shortest_paths:
    #            print("          Path: %s" % path)
    #    print("To Valve ASN 32590")
    #    if nx.has_path(graph, asn, 32590):
    #        shortest_paths = nx.all_shortest_paths(graph, asn, 32590)
    #        for path in shortest_paths:
    #            print("          Path: %s" % path)

    #    print("To Ubisoft ASN 49544") 
    #    if nx.has_path(graph, asn, 49544):
    #        shortest_paths = nx.all_shortest_paths(graph, asn, 49544)
    #        for path in shortest_paths:
    #            print("          Path: %s" % path)
    #    print("\n")
        

    #print("Number of nodes/ASN in graph: %s" % graph.number_of_nodes())
    #print("Number of unique node/ASN for all common paths: %s" % len(pathasn))
    #seperateEdges(graph)
    #drawTopoGraph(graph)
    net_pyvis = Network(height="1000px", width="100%", notebook=True, directed=True) 
    net_pyvis.toggle_physics(True)
    #net_pyvis.show_buttons(filter_=['physics'])
    net_pyvis.show_buttons(filter_=True)
    net_pyvis.from_nx(graph)
    neigh_map = net_pyvis.get_adj_list()
    new_map = {}
    for node, neigh in neigh_map.items():
        new_set = set()
        for n in neigh:
            new_set.add(str(n))
        new_map[node] = new_set

    for node in net_pyvis.nodes:
        node["title"] = "ASN"+str(node['id'])+"'s Neighbors:\n\n" + "\n".join(new_map[node["id"]])
        node["label"] = str(node['id'])
        #print("Node: %s" % node)

    #for edge in net_pyvis.get_edges():
    #    lat = random.randint(1,100)

    #    edge["width"] = float((1/lat)*10) 
    #    edge["title"] = str(lat)+' ms'
    #    #print(edge)

    #net_pyvis.show('nx_fixes_asname.html')

