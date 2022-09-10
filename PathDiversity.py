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

import os
import sys
import argparse
import networkx as nx
import time
import csv
import pybgpstream
from collections import defaultdict
import re
import json
import requests

URL = "https://api.asrank.caida.org/v2/graphql"
dataproviders = ["route-views.sydney",
                 "route-views.phoix",
                 "route-views.wide",
                 "route-views.eqix",
                 "route-views2", "route-view3",
                 "route-views4", "route-views6",
                 "route-views.isc", "route-views.kixp",
                 "route-views.jinx", "route-views.linx",
                 "route-views.telxatl",
                 "route-views.saopaulo",
                 "route-views.nwax",
                 "route-views.perth",
                 "route-views.sg",
                 "route-views.sfmix",
                 "route-views.soxrs",
                 "route-views.chicago",
                 "route-views.napafrica",
                 "route-views.flix",
                 "route-views.chile",
                 "route-views.asmix",
                 "rrc00", "rrc01", "rrc02",
                 "rrc03", "rrc04", "rrc05",
                 "rrc06", "rrc07", "rrc08",
                 "rrc09", "rrc10", "rrc11",
                 "rrc12", "rrc13", "rrc14",
                 "rrc15", "rrc16", "rrc17",
                 "rrc18", "rrc19", "rrc20",
                 "rrc21", "rrc22", "rrc23"
                ]
output_dir = "_PathDiversityOutput"

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
                internetGraph.add_edge(asRelLink[0], asRelLink[1],
                                       relationship='p2c')

            if (asRelLink[2] == 'c2p'):
                internetGraph.add_edge(asRelLink[1], asRelLink[0],
                                       relationship='p2c')

            if (asRelLink[2] == 'p2p') or (asRelLink[2] == '0'):
                internetGraph.add_edge(asRelLink[0], asRelLink[1],
                                       relationship='p2p')
                internetGraph.add_edge(asRelLink[1], asRelLink[0],
                                       relationship='p2p')

    return internetGraph.reverse()


def seperateEdges(graph):
    p2c_edges = []
    p2p_edges = []
    for edge in list(graph.edges):
        rel = graph.get_edge_data(edge[0], edge[1])
        #print("Attribute rel is %s\n" %rel)
        if rel['relationship'] == 'p2c':
            p2c_edges.append(edge)

        if rel['relationship'] == 'p2p':
            p2p_edges.append(edge)
    return p2c_edges, p2p_edges


def sortPeeringRel(graph, asn):
    customers = set()
    transit_peers = set()
    customer_edges = graph.in_edges(asn)
    transitpeer_edges = graph.out_edges(asn)

    for edge in customer_edges:
        customers.add(edge[0])

    for edge in transitpeer_edges:
        transit_peers.add(edge[1])

    for peerAS in transit_peers:
        if peerAS in customers:
            customers.discard(peerAS)

    return customers, transit_peers


def QueryProviders(transitAS, stubAS, customers, transitandpeers, numberOfProviders):
    filters = 'peer '+transitAS+' and path "_'+stubAS+'_"'
    prefixes = defaultdict(set)
    nextHops = defaultdict(set)

    for provider in dataproviders:
        stream = pybgpstream.BGPStream(from_time="2020-03-01 07:50:00",
                                       until_time="2020-03-02 07:50:00",
                                       collectors=[provider],
                                       record_type="ribs",
                                       filter=filters)
        for rec in stream.records():
            for elem in rec:
                pfx = elem.fields["prefix"]
                ases = elem.fields["as-path"].split(" ")
                next_hop = elem.fields['next-hop']
                if len(ases) > 0:
                    if numberOfProviders != 0:
                        if ases[-1] == stubAS and (ases[1] not in customers):
                            prefixes[pfx].add(tuple(ases))
                    else:
                        if ases[-1] == stubAS:
                            prefixes[pfx].add(tuple(ases))
                    nextHops[pfx].add(next_hop)
                    #print(elem)
    return prefixes, nextHops


def output(prefixes, nextHops, transitAS, stubAS):
    print("Prefixes originated by AS %s are reachable from AS %s via the following paths:\n" %
          (stubAS, transitAS))
    for pfx, paths in prefixes.items():
        print("Prefix: %s" % pfx)
        for path in paths:
            print("       ("+",".join(path)+")")
        next_hops = nextHops[pfx]
        print("       Next-hop routers:")
        for next_hop in next_hops:
            print("       %s" %next_hop)
        print("\n")


def AsnQuery(asn): 
    return """{
        asn(asn:"%i") {
            asn
            asnName
            rank
            organization {
                orgId
                orgName
            }
            cliqueMember
            seen
            longitude
            latitude
            cone {
                numberAsns
                numberPrefixes
                numberAddresses
            }
            country {
                iso
                name
            }
            asnDegree {
                provider
                peer
                customer
                total
                transit
                sibling
            }
            announcing {
                numberPrefixes
                numberAddresses
            }
        }
    }""" % (asn)


if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Get path diversity between a transit AS and stub AS',
            usage='%(prog)s [-I as-rel.datafile -t target ASN -s stub AS]')
    argParser.add_argument('-I', dest='as_rel_data', help='AS relation data file',
                           default=None)
    argParser.add_argument('-t', dest='transitASN', help='Target AS number',
                           default=None)
    argParser.add_argument('-s', dest='stubAS', help='Stub AS', default=None)
    argParser.add_argument('-O', dest='pathDivFile', help='Filename to write path diversity search',
                           default='PathDiversityOutput.txt')
    args = argParser.parse_args()

    if (args.as_rel_data is None):
        print("AS relationship data file not provided!!!")
        sys.exit(-1)

    if (args.transitASN is None) or (args.stubAS is None):
        print("Transit AS or Stub AS not provided!!!")
        sys.exit(-1)

    query = AsnQuery(int(args.transitASN))
    request = requests.post(URL, json={'query':query})
    if request.status_code == 200:
        asrank = request.json()
        asnName = asrank['data']['asn']['asnName']
        asnProviderNo = asrank['data']['asn']['asnDegree']['provider']
        asnCustNo = asrank['data']['asn']['asnDegree']['customer']
        asnPeerNo = asrank['data']['asn']['asnDegree']['peer']
        asnRank = asrank['data']['asn']['rank']
    else:
        print("ASRank Query failed to run returned code of %d " %(request.status_code))
        sys.exit(-1)

    graphData = readASRelData(args.as_rel_data)
    customers, transitAndPeers = sortPeeringRel(graphData, args.transitASN)
    prefix_origin, nextHops = QueryProviders(args.transitASN, args.stubAS, customers, transitAndPeers, asnProviderNo)

    with open(os.path.join(output_dir, args.pathDivFile), "w") as pathDivRes:
        if asnProviderNo == 0:
            pathDivRes.write("%s(ASN %s) ranked at %s is a Tier-1 transit provider\n"
                             %(asnName, args.transitASN, asnRank))
        else:
            pathDivRes.write("%s(ASN %s) ranked at %s is not a Tier-1 transit provider\n"
                             %(asnName, args.transitASN, asnRank))
        pathDivRes.write("Prefixes originated by AS %s are reachable from AS %s via the following paths:\n" 
                         %(args.stubAS, args.transitASN))
        pathDivRes.write("\n")
        for pfx, paths in prefix_origin.items():
            pathDivRes.write("Prefix: %s\n" % pfx)
            for path in paths:
                pathDivRes.write("       ("+",".join(path)+")\n")
            pathDivRes.write("       Next-hop routers:\n")
            for next_hop in nextHops[pfx]:
                pathDivRes.write("       %s\n" % next_hop)
            pathDivRes.write("\n\n")
        

    #output(prefix_origin, nextHops, args.transitASN,  args.stubAS)

