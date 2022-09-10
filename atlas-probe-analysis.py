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
import ast
import requests
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
import ipaddress 
import networkx as nx
import json
import csv
from pprint import pprint
from ipwhois import IPWhois
#from datetime import datetime
#from dateutil import parser

BASE_PROBE_URL = "https://atlas.ripe.net/api/v2/probes/?country_code="
PROBE_PARAMS = "&status=1"

ASNRelFile = "/scratch/asnLinks.jsonl"


def ReadAsnRelFile(filename):
    with open(filename, 'r') as json_file:
        AsnRelDat = list(json_file)
        Data = []
        for rel in AsnRelDat:
            res = json.loads(rel)
            Data.append(res)
    return Data


def createGraph(ASRelData):
    internetGraph = nx.DiGraph()
    for asrel in ASRelData:
        if asrel['relationship'] == 'customer':
            internetGraph.add_edge(asrel['asn0']['asn'],
                                   asrel['asn1']['asn'],
                                   relationship='p2c',
                                   numberPaths=asrel['numberPaths'],
                                   weight=1)

        if asrel['relationship'] == 'provider':
            internetGraph.add_edge(asrel['asn1']['asn'],
                                   asrel['asn0']['asn'],
                                   relationship='p2c',
                                   numberPaths=asrel['numberPaths'],
                                   weight=1)

        if asrel['relationship'] == 'peer':
            internetGraph.add_edge(asrel['asn1']['asn'],
                                   asrel['asn0']['asn'],
                                   relationship='p2p',
                                   numberPaths=asrel['numberPaths'],
                                   weight=2)

            internetGraph.add_edge(asrel['asn0']['asn'],
                                   asrel['asn1']['asn'],
                                   relationship='p2p',
                                   numberPaths=asrel['numberPaths'],
                                   weight=2)

    return internetGraph.reverse()


def seperateEdges(graph):
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


def getResults(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    mresp = requests.get(url)
    data = mresp.json()
    res_url = data['result']
    res_data = requests.get(res_url)
    results = res_data.json()
    return results
    #for res in results:
    #    print(res)
    #    print("\n")
    
    #print(results)

def getProbes(isocode):
    url = BASE_PROBE_URL+str(isocode)+PROBE_PARAMS
    resp = requests.get(url)
    data = resp.json()
    #if 'results' in data:
    #    for probe in data['results']:
    #        print(probe)

    if 'count' in data:
        print("Number of probes in count: %s" % data['count'])
        print("Number of probes in result: %s" % len(data['results']))
        probes = data['results']
        while data['next'] is not None:
            url = data['next']
            resp = requests.get(url)
            data = resp.json()
            probes.extend(data['results'])

        print("Number of probes: %s" % len(probes))
        return probes
    else:
        print("There are no probes in: %s" % isocode)
        return None

def getProbeInfo(probe_id):
    url = "https://atlas.ripe.net/api/v2/probes/"+str(probe_id)+"/"
    resp = requests.get(url)
    data = resp.json()
    #addrv4 = data["address_v4"], addrv6 = data["address_v6"]
    #asnv4 = data["asn_v4"], id=data["id"],public=data["is_public"]
    #anchor= data["is_anchor"]
    return data


def pingHops(probes, path, start, end):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    res_url = "/results/?probe_ids="
    for probe in probes:
        p_id = probe['id']
        url = (base_url+str(path)+res_url+str(p_id)
                +"&start="+str(start)+"&stop="+str(end)+"&format=json")
        resp = requests.get(url)
        data = resp.json()
        if isinstance(data, list):
            for m in data:
                print("Address: %s, Name: %s, Probe Source Address: %s, "
                      "Probe Public IP Address(From): %s"
                      % (m['addr'], m['name'], m['src_addr'], m['from']))
        print("\n")

def getNATedProbes(probes, path, start, end):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    res_url = "/results/?probe_ids="
    NATedProbes = []
    for probe in probes:
        p_id = probe['id']
        url = (base_url+str(path)+res_url+str(p_id)
                +"&start="+str(start)+"&stop="+str(end)+"&format=json")
        resp = requests.get(url)
        data = resp.json()
        probe['is_nat'] = False
        if isinstance(data, list):
            for m in data:
                try:
                    srcAddr = ipaddress.ip_address(m['src_addr'])
                except ValueError:
                    print("%s: src_addr not a valid IP!!!" % m['src_addr'])
                    continue
                
                try:
                    hopAddr = ipaddress.ip_address(m['addr'])
                except ValueError:
                    print("%s: Hop address is not a valid IP!!!" % m['addr'])
                    continue

                try:
                    hopName = ipaddress.ip_address(m['name'])
                except ValueError:
                    print("%s: Hop name is not a valid IP!!!" % m['name'])
                    continue

                try:
                    publicIP = ipaddress.ip_address(m['from'])
                except ValueError:
                    print("%s: Public IP address is not a valid IP!!!" % m['from'])
                    continue

                if srcAddr != publicIP:
                    if srcAddr.is_private:
                        probe['is_nat'] = True
                    else:
                        probe['is_nat'] = False
                else:
                    if publicIP.is_global:
                        probe['is_nat'] = False
                    else:
                        try:
                            prefix = ipaddress.ip_network(probe['prefix_v4'])
                        except ValueError:
                            print("%s: Probe IPv4 net prefix is invalid!!!" % probe['prefix_v4'])
                            continue
                    
                        if hopAddr in prefix:
                            if hopAddr.is_global: 
                                probe['is_nat'] = True
                        else:
                            if hopAddr.is_global:
                                probe['is_nat'] = True 

            if probe['is_nat'] is True:
                NATedProbes.append(probe)
    return NATedProbes

def WhoisQuery(ipaddr):
    try:
        IpAddr = ipaddress.ip_address(ipaddr)
    except ValueError:
        print("%s is not a valid IP address!!!" % ipaddr)
        return None
    
    if IpAddr.is_private:
        print("%s is not a public IP address" % ipaddr)
        return None

    queryObj = IPWhois(ipaddr)
    result = queryObj.lookup_rdap(depth=1)
    return result

        
    
if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Get probes and measurements from RIPE Atlas',
            usage='%(prog)s [-c country_code]')
    argParser.add_argument('-c', dest='country_code',
                           help='Country code in lower case',
                           default=None)

    argParser.add_argument('-s', "--startdate",
                           help="Unix timestamp for measurement start time",
                           type=int,
                           required=True)

    argParser.add_argument('-e', "--enddate",
                           help="Unix timestamp for measurement end time",
                           type=int,
                           required=True)

    argParser.add_argument('-p', "--pinghop",
                           help="""Ping the 1st, 2nd or 2nd alternative hop
                                from probe. 1 = 1st hop, 2 = 2nd hop,
                                100 = 2nd alternative hop""",
                           type=int,
                           default=1)

    argParser.add_argument('-t', "--transit",
                           help="ASN for target transit providing PAR in country",
                           type=int)

    argParser.add_argument('-m', "--measurementid",
                           help="Unique id for measurement",
                           type=int)

    args = argParser.parse_args()

    if args.country_code is None:
        print("Please supply a country code to query for probes!!!\n")
        sys.exit(-1)

    print(args.startdate)
    getProbeInfo(18599)
    #Relationship = ReadAsnRelFile(ASNRelFile)
    #iNetGraph = createGraph(Relationship)
    #p2c_edges, p2p_edges = seperateEdges(iNetGraph)
    #peers_and_customers = list(iNetGraph.predecessors(str(args.transit)))
    probe_id = []
    probes = []
    msm_results = getResults(args.measurementid)
    prd_id_res_count = 0
    msm_by_prb = {}
    aspath_from_prb = {}
    valid_prbs = {}
    for result in msm_results:
        if result['type'] == 'traceroute':
            msm_by_prb[result['prb_id']] = result

        if result['type'] == 'ping':
            if result['prb_id'] in msm_by_prb:
                msm_by_prb[result['prb_id']].append(result)
            else:
                msm_by_prb[result['prb_id']] = []
        #pprint(result)

    for prb_id, msms in msm_by_prb.items():
        if isinstance(msms, list):
            if msms[0]['type'] == 'ping':
                min_rtt = []
                for msm in msms: 
                    min_rtt.append(msm['min'])
                if min(min_rtt) >= 100:
                    print("Probe %s to be excluded\n" % prb_id)
                else:
                    valid_prbs[prb_id] = msms

        if isinstance(msms, dict):
            if msms['type'] == 'traceroute':
                srcAddr = msms['from']
                dstAddr = msms['dst_addr']
                hops = msms['result']
                prb_info = getProbeInfo(msms['prb_id'])
                prb_asn = prb_info["asn_v4"]
                aspath = []
                aspath.append(prb_asn)
                #whois_query_res = WhoisQuery(srcAddr)
                #pprint(msms)
                for hop in hops: 
                    try:
                        hop_addr = hop['result'][0]['from']
                    except KeyError:
                        path = 'hop-'+str(hop['hop'])
                        aspath.append(path)
                        continue

                    try:
                        hopAddr = ipaddress.ip_address(hop_addr)
                    except ValueError:
                        path = 'hop-'+str(hop['hop'])
                        aspath.append(path)
                        continue

                    if hop['hop'] == 1:
                        
                        if hopAddr.is_private:
                            prb_info = getProbeInfo(msms['prb_id'])
                            asn = prb_info["asn_v4"] 
                            aspath.append(asn)
                        else:
                            whois_query_res = WhoisQuery(hop_addr)

                            if whois_query_res is not None:
                                asn = whois_query_res["asn"]
                                try:
                                    aspath.append(int(asn))
                                except (ValueError, TypeError) as error:
                                    path = 'hop-'+str(hop['hop'])
                                    aspath.append(path)

                    if hopAddr.is_global:
                        whois_query_res = WhoisQuery(hop_addr)

                        if whois_query_res is not None:
                            asn = whois_query_res["asn"]
                            try:
                                aspath.append(int(asn))
                            except (ValueError, TypeError) as error:
                                path = 'hop-'+str(hop['hop'])
                                aspath.append(path)
                print("AS-Path from %s (ASN %s) to 155.133.246.66: %s" % (msms['prb_id'], prb_asn, aspath))
                aspath_from_prb[msms['prb_id']] = aspath

    print("Total number of measurements for all probes: %s" % len(msm_results))
    print("Number of results for Probe %s: %s" % (1000422, len(msm_by_prb[1000422])))
    print("Total number of probes: %s" % len(msm_by_prb))

    for prb_id, msms in msm_by_prb.items():
        print("Probe ID: %s" % prb_id)
        pprint(msms)
        print("AS path: %s\n" % aspath_from_prb[prb_id])

    #for prb_id, msms in msm_by_prb.items():
    #    min_rtt = []
    #    for msm in msms:
    #        min_rtt.append(msm['min'])
    #    #print("Number of measurements for probe %s: %s" % (prb_id, len(msms)))
    #    if min(min_rtt) >= 22.5:
    #        print("Probe %s excluded\n" % prb_id)
    #    else:
    #        valid_prbs[prb_id] = msms 

            

    #with open('/scratch/eu_member_states.csv', 'r') as eu_file:
    #    eu_countries = csv.reader(eu_file)
    #    for country in eu_countries:
    #        if (country[3] == 'ES') or (country[3] == 'PT'):
    #            print("Getting probes in %s" % country[1])
    #            country_probes = getProbes(country[3])
    #            if country_probes is not None:
    #                probes.extend(country_probes)
    #
    #for probe in probes:
    #    probe_id.append(str(probe['id']))

    #probe_list_out = ",".join(probe_id)
    #with open("/scratch/spain-portugal-probe-list.txt", "w") as txt_file:
    #    txt_file.write(probe_list_out)


    #asns = [ 6058, 6327, 46478, 577, 852, 395075, 19397, 855, 6327, 5769, 20473,
    #         16509, 1403, 21659, 396982,16276, 54632, 394256, 53356, 62513, 395152,
    #         239, 14061, 4508, 923, 5645, 7122, 22684, 32881]
    #for asn in asns:
    #    print("Finding path between %s and %s"  % (args.transit, asn))
    #    try:
    #        paths = list(nx.all_shortest_paths(iNetGraph, str(args.transit), str(asn), weight='weight'))
    #    except nx.exception.NetworkXNoPath:
    #        print("There are no provider paths from %s to %s\n" % (args.transit, asn))
    #        paths = None

    #    if isinstance(paths, list):
    #        print("All paths between %s and %s: %s" % (args.transit, asn, paths))
    #        if len(paths) >= 1:
    #            for path in paths:
    #                if len(path) > 1:
    #                    if path[1] not in peers_and_customers:
    #                        print("Provider Paths between %s and %s: %s\n" %(args.transit, asn, path))
    #    

    #    


    #print(peers_and_customers)
    #print(len(peers_and_customers))

    #probes = getProbes(args.country_code)
    #for probe in probes:
    #    print(probe) 
    #    print("\n")
    #pingHops(probes, args.pinghop, args.startdate, args.enddate)
    #NATProbes_1st_hop = getNATedProbes(probes, 1, args.startdate, args.enddate)
    #NATProbes_2nd_hop = getNATedProbes(probes, 2, args.startdate, args.enddate)
    #NATProbes_2nd_Alt_hop = getNATedProbes(probes, 100, args.startdate, args.enddate)
    #print("NAT'ed probes by first hop: %s" % len(NATProbes_1st_hop))
    #print("NAT'ed probes by second hop: %s" % len(NATProbes_2nd_hop))
    #print("NAT'ed probes by second alt hop: %s" % len(NATProbes_2nd_Alt_hop))
    #print("There are %s probes in  total" % len(probes))
    #
    #if len(NATProbes_1st_hop) > len(NATProbes_2nd_hop):
    #    for probe in NATProbes_1st_hop:
    #        if probe not in NATProbes_2nd_hop:
    #            print("Probe ID: %s, ASN: %s, Address: %s" % (probe['id'], probe['asn_v4'], probe['address_v4']))
    #else:
    #    for probe in NATProbes_2nd_hop:
    #        if probe not in NATProbes_1st_hop:
    #            print("Probe ID: %s, ASN: %s, Address: %s" % (probe['id'], probe['asn_v4'], probe['address_v4']))

    #            
    #print("\n\n\n")
    #for probe in NATProbes_1st_hop:
    #    print("Probe ID: %s, ASN: %s" % (probe['id'], probe['asn_v4']))
    #    
    #        
    #transit_probes = []
    #for probe in probes:
    #    if probe['asn_v4'] == args.transit:
    #        transit_probes.append(probe)
    #print("Probes in  ASN %s: %s" % (args.transit, len(transit_probes)))
    ##Remove transit probes from NAT'ed probes
    #external_probes = []
    #for probe in NATProbes_1st_hop: 
    #    if probe['asn_v4'] != args.transit:
    #        external_probes.append(probe)
    #print("Final list of probes that can be used: %s" % len(external_probes))



    

    

