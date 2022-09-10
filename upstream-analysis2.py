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
from collections import defaultdict
import re
import json
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tabulate import tabulate
import ast


asnRankFile = '/scratch/asns.jsonl'
eyeballFile = '/scratch/eyeballdata2'
isocountryFile = '/scratch/countries_codes_and_coordinates.csv'

isocodes = ["EU"]
countries = ["European Union"]
iso_country = {"EU": "European Union"}
hypergiants = ["Google", "Microsoft", "Facebook", "CloudFlare", "Akamai", "Limelight",
               "Netflix", "Amazon", "Apple", "Twitter", "Alibaba", "Cdnetworks", "Fastly"]

hypergiantasns = [15169, 36385, 16591, 43515, 36384, 396982, 19527, 139070, 139190,
                  36492, 41264, 36040, 24424, 395973, 45566, 16550, 8075, 3598, 8070,
                  200517, 8069, 8068, 59067, 12076, 58862, 45139, 23468, 35106, 63314,
                  398961, 32934, 63293, 54115, 32787, 20940, 35994, 24319, 34164, 16625,
                  36183, 21342, 12222, 213120, 33905, 31984, 17204, 31109, 200005, 18717,
                  35204, 26008, 31108, 393234, 393560, 31377, 43639, 49846, 31110, 22822,
                  38622, 23059, 45396, 55429, 26506, 60261, 38621, 37377, 2906, 40027, 55095,
                  394406, 136292, 714, 6185, 2709, 13414, 63179, 35995, 54888, 24429, 37963,
                  45102, 16509, 7224, 19047, 36263, 14618, 8987, 62785, 36408, 38107, 204720,
                  54113, 394192, 13335, 395747, 394536, 14789, 209242, 132892, 202623, 203898,
                  139242]


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


def drawTopoGraph(graph):
    plt.subplot(111)
    pos = nx.spring_layout(graph)
    nodes = nx.draw_networkx_nodes(graph, pos)
    p2c_edges,  p2p_edges = seperateEdges(graph)
    edge_colors = ['r' if edge in p2c_edges else 'g' for edge in graph.edges]
    nodes.set_edgecolor('r')
    nx.draw_networkx_edges(graph, pos)
    nx.draw_networkx_edges(graph, pos, edge_color=edge_colors, min_source_margin=3, min_target_margin=3 )
    nodeList = list(graph.nodes)
    labels = {}
    for node in  nodeList:
        labels[node] = 'ASN'+node
    nx.draw_networkx_labels(graph, pos, labels, font_weight='bold')
    plt.show()
    #plt.savefig("inetTopo.png")


def createSubgraph(graph, node, neighbourNodes):
    if type(neighbourNodes) is not list:
        allNodes = list(neighbourNodes)
    else:
        allNodes = neighbourNodes
    allNodes.append(node)
    subgraphMaxNode = nx.subgraph(graph, allNodes)
    return subgraphMaxNode


def ReadAsnRankFile(filename):
    with open(filename, 'r') as json_file:
        InternetRank = list(json_file)
    return InternetRank


def ReadEyeballData(eyeballdata):
    with open(eyeballdata, 'r') as dfile:
        EYEDATASET = ast.literal_eval(dfile.read())

    for asn in EYEDATASET:
        asno = asn["asn"]
        asno = asno.replace("AS", "")
        asn["asn"] = int(asno)

    return EYEDATASET


def ReadIsoCountryCodes(isocountryfile):
    with open(isocountryfile, 'r') as isofile:
        isocodecsv = csv.reader(isofile)
        for country in isocodecsv:
            countries.append(country[0])
            country[1] = country[1].replace('"', "")
            country[1] = country[1].strip()
            isocodes.append(country[1])
            iso_country[country[1]] = country[0]


def FilterEyeballBySize(dataset, size):
    FILTEREDEYEDATA = []
    for asn in dataset:
        if asn["users"] >= size:
            FILTEREDEYEDATA.append(asn)
    return FILTEREDEYEDATA


def GetEyeballASNs(dataset):
    eyeballASNs = []
    for asn in dataset:
        eyeballASNs.append(asn["asn"])
    return eyeballASNs


def UpstreamStatsOverall(providers, output):
    upstream_list = []
    upstream_numbers_to_providers = {}
    for asns in providers:
        upstream = str(asns['asnDegree']['provider'])
        upstream_list.append(int(asns['asnDegree']['provider']))
        if upstream not in upstream_numbers_to_providers:
            upstream_numbers_to_providers.update({upstream: 1})
        else:
            upstream_numbers_to_providers[upstream] += 1

    s = pd.Series(upstream_list, name='upstreams')
    df = pd.DataFrame(s)
    #plt.title("KDE of upstreams observed for Tier-2/3 ISPs excluding hypergiants and eyeball networks smaller than 1000 users")
    #plt.xlabel("Distribution of number of upstreams amongst providers")
    #plt.ylabel("K-DENSITY")
    #s.plot.kde()
    #plt.xlim([0,9])
    #plt.savefig("/scratch/upstreamData/KDE_Test.png")
    print(df.describe())
    stats_df = df.groupby('upstreams')['upstreams'].agg('count').pipe(pd.DataFrame).rename(columns={'upstreams': 'providers'})
    print("Sum of the number of providers seen for each upstreams: %s" % sum(stats_df['providers']))
    stats_df['pdf'] = stats_df['providers'] / sum(stats_df['providers'])
    stats_df['cdf'] = stats_df['pdf'].cumsum()
    stats_df['percentage of providers'] = (stats_df['providers']/stats_df['providers'].sum()) * 100
    stats_df['Cumulative percentage for providers'] = stats_df['percentage of providers'].cumsum()
    stats_df['Reversed cumulative percentage of providers'] = stats_df.loc[::-1, 'percentage of providers'].cumsum()[::-1]
    filename = '/scratch/upstreamData/'+str(output)
    with open(filename, 'w') as f:
        f.write("Total number of providers considered: %s\n" % sum(stats_df['providers']))
        f.write("Table showing the CDF,PDF and percentage of providers with different upstreams\n")
        f.write(tabulate(stats_df, headers='keys', tablefmt='pretty'))

    print("Table showing the CDF,PDF and percentage of providers with different upstreams")
    print(tabulate(stats_df, headers='keys', tablefmt='pretty'))
    csv_out = '/scratch/upstreamData/'+str(output)+'.csv'
    stats_df.to_csv(csv_out)

    stats_df = stats_df.reset_index()
    #print(tabulate(stats_df, headers='keys', tablefmt='pretty'))
    return stats_df
    #stats_df.plot(x='upstreams', y=['pdf', 'cdf'], grid=True)

    #plt.title("CDF/PDF of upstreams observed for Tier-2/3 ISPs excluding hypergiants and eyeball networks smaller than 1000 users")
    #plt.xlabel("Number of upstreams amongst providers")
    #plt.ylabel("CDF/PDF")
    #plt.xlim([0,9])
    #plt.savefig("/scratch/upstreamData/CDF_test.png")
    #plt.show(block=True)


def PlotGraphs(**kwargs):
    fig, ax = plt.subplots()
    for name, df  in kwargs.items():
        if isinstance(df, pd.DataFrame):
            if name ==  'WithHGs':
                llabel = "Including Hypergiants"

            if name == 'ExcludingHGs':
                llabel = "Excluding Hypergiants"

            if name == 'ExcludingHGsEyeballs5000':
                llabel = "Excluding  Hypergiants and Eyeballs networks greater than 5000 users"

            if name == 'ExcludingHGsEyeballs2000':
                llabel = "Excluding  Hypergiants and Eyeballs networks greater than 2000 users"

            if name == 'ExcludingHGsEyeballs1000':
                llabel = "Excluding  Hypergiants and Eyeballs networks greater than 1000 users"

            if name == 'ExcludingHGsAllEyeballs':
                llabel = "Excluding Hypergiants and all eyeball networks"

            ax.plot(df['upstreams'], df['cdf'], label=llabel)
        else:
            pass
    plt.title("CDF of upstreams observed for Tier-2/3 ISPs")
    plt.xlabel("Number of upstreams amongst providers")
    plt.ylabel("CDF")
    plt.xlim([0,10])
    plt.legend(fontsize=15)
    plt.show(block=True)


def PlotGraphsCountry(df, countryName, graphtype):
    fig, ax = plt.subplots(figsize=(12,7))
    if graphtype ==  'WithHGs':
        llabel = "Including Hypergiants in "+str(countryName)
    if graphtype == 'ExcludingHGs':
        llabel = "Excluding Hypergiants in "+str(countryName)
    if graphtype == 'ExcludingHGsEyeballs5000':
        llabel = "Excluding  Hypergiants and Eyeballs networks greater than 5000 users in "+str(countryName)
    if graphtype == 'ExcludingHGsEyeballs2000':
        llabel = "Excluding  Hypergiants and Eyeballs networks greater than 2000 users in "+str(countryName)
    if graphtype == 'ExcludingHGsEyeballs1000':
        llabel = "Excluding  Hypergiants and Eyeballs networks greater than 1000 users in "+str(countryName)
    if graphtype == 'ExcludingHGsAndAllENs':
        llabel = "Excluding Hypergiants and all Eyeball networks in "+str(countryName)

    ax.plot(df['upstreams'], df['cdf'], label=llabel)
    plt.title("CDF of upstreams observed for Tier-2/3 ISPs in "+str(countryName))
    plt.xlabel("Number of upstreams amongst providers")
    plt.ylabel("CDF")
    plt.xlim([0,10])
    plt.legend(fontsize=5)
    graphname = "/scratch/upstreamData/excludingHGs/"+str(countryName)+".png"
    plt.savefig(graphname)
    #plt.show(block=True)


def PlotGraphsTopCountries(topcountries):
    fig, ax = plt.subplots(figsize=(12,7))
    for country, df in topcountries.items():
        if isinstance(df, pd.DataFrame):
            print(df)
            llabel = "Providers in "+str(country)
            ax.plot(df['upstreams'], df['cdf'], label=llabel)
        else:
            pass
    plt.title("CDF of upstreams in top 5 countries plus Australia and NZ")
    plt.xlabel("Number of upstreams amongst providers")
    plt.ylabel("CDF")
    plt.xlim([0,10])
    plt.legend(fontsize=5)
    plt.show(block=True)
            

def GetProvidersByCountry(providers, isocode):
    ISPsByCountry = []
    for asns in providers:
        if isocode == asns['country']['iso']:
            ISPsByCountry.append(asns)
        else:
            pass

    return ISPsByCountry


def UpstreamStatsByCountry(providers, isocodes):
    providers_per_country = {}
    top5plusAusandNZ = {}
    #fig, ax = plt.subplots()

    for iso in isocodes:
        if iso == 'Alpha-2 code':
            continue

        if iso in iso_country:
            countryName = iso_country[iso]
        else:
            countryName = iso

        print("Getting Tier 2/3 ISPs in: %s" % countryName)
        CountryISPs = GetProvidersByCountry(providers, iso)
        providers_per_country[countryName] = len(CountryISPs)
        if len(CountryISPs) != 0:
            print("Provider to upstream Stats for: %s" % countryName)
            upstream_list = []
            upstream_numbers_to_providers = {}
            for asns in CountryISPs:
                upstream = str(asns['asnDegree']['provider'])
                upstream_list.append(int(asns['asnDegree']['provider']))
                if upstream not in upstream_numbers_to_providers:
                    upstream_numbers_to_providers.update({upstream: 1})
                else:
                    upstream_numbers_to_providers[upstream] += 1
            if (len(upstream_list) == 1) and (upstream_list[0] == 1):
                continue
            else:
                s = pd.Series(upstream_list, name='upstreams')
                df = pd.DataFrame(s)
                print(df.describe())
                stats_df = df.groupby('upstreams')['upstreams'].agg('count').pipe(pd.DataFrame).rename(columns={'upstreams': 'providers'})
                print("Sum of the number of providers seen for upstreams in %s: %s" % (sum(stats_df['providers']), countryName))
                stats_df['pdf'] = stats_df['providers'] / sum(stats_df['providers'])
                stats_df['cdf'] = stats_df['pdf'].cumsum()
                stats_df['percentage of providers'] = (stats_df['providers']/stats_df['providers'].sum()) * 100
                stats_df['Cumulative percentage for providers'] = stats_df['percentage of providers'].cumsum()
                stats_df['Reversed cumulative percentage of providers'] = stats_df.loc[::-1, 'percentage of providers'].cumsum()[::-1]
                filename = '/scratch/upstreamData/excludingHGs/'+str(countryName)
                with open(filename, 'w') as f:
                    f.write("Table showing the CDF,PDF and percentage of providers with different upstreams\n")
                    f.write(tabulate(stats_df, headers = 'keys', tablefmt = 'pretty'))

                print("Table showing the CDF,PDF and percentage of providers with different upstreams in %s" %countryName)
                print(tabulate(stats_df, headers='keys', tablefmt='pretty'))
                csv_out = '/scratch/upstreamData/excludingHGs/'+str(countryName)+'.csv'
                stats_df.to_csv(csv_out)
                stats_df = stats_df.reset_index()
                print("\n")
        else:
            print("%s has no tier 2/3 ISP\n" % countryName)
        hg = 'WithHGs'
        xg = 'ExcludingHGs'
        allEns = 'ExcludingHGsAndAllENs'

        #if stats_df.shape[0] >= 2:
        #    PlotGraphsCountry(stats_df, countryName, xg)


        if countryName == 'United States':
            llabel = "Providers in "+str(countryName)
            #ax.plot(stats_df['upstreams'], stats_df['cdf'], label=llabel)
            
            top5plusAusandNZ[countryName] = stats_df

        if countryName == 'Russia':
            llabel = "Providers in "+str(countryName)
            #ax.plot(stats_df['upstreams'], stats_df['cdf'], label=llabel)

            top5plusAusandNZ[countryName] = stats_df

        if countryName == 'Brazil':
            llabel = "Providers in "+str(countryName)
            #ax.plot(stats_df['upstreams'], stats_df['cdf'], label=llabel)

            top5plusAusandNZ[countryName] = stats_df

        if countryName == 'Germany':
            llabel = "Providers in "+str(countryName)
            #ax.plot(stats_df['upstreams'], stats_df['cdf'], label=llabel)

            top5plusAusandNZ[countryName] = stats_df

        if countryName == 'Ukraine':
            llabel = "Providers in "+str(countryName)
            #ax.plot(stats_df['upstreams'], stats_df['cdf'], label=llabel)

            top5plusAusandNZ[countryName] = stats_df

        if countryName == 'Australia':
            llabel = "Providers in "+str(countryName)
            #ax.plot(stats_df['upstreams'], stats_df['cdf'], label=llabel)
            top5plusAusandNZ[countryName] = stats_df

        if countryName == 'New Zealand':
            llabel = "Providers in "+str(countryName)
            #ax.plot(stats_df['upstreams'], stats_df['cdf'], label=llabel)
            top5plusAusandNZ[countryName] = stats_df
        
        #if stats_df.shape[0] >= 2:
        #    PlotGraphsCountry(stats_df, countryName, xg)
    #plt.title("CDF of upstreams in top 5 countries plus Australia and NZ")
    #plt.xlabel("Number of upstreams amongst providers")
    #plt.ylabel("CDF")
    #plt.xlim([0,10])
    #plt.legend(fontsize=5)
    #plt.show(block=True)

    providers_per_country_sorted = sorted(providers_per_country.items(), key=lambda x:x[1], reverse=True)
    
    for i in range(0,30):
        print("Rank %s: %s" %(i+1,providers_per_country_sorted[i]))


    #print(top5plusAusandNZ)
    PlotGraphsTopCountries(top5plusAusandNZ)

    print(providers_per_country_sorted)


def ShowTopProvidersByUpstreamConn(providers):
    topProviders = []
    for asns in providers:
        upstreams = asns['asnDegree']['provider']
        if upstreams >= 10: 
            topProviders.append(asns)
            print(asns)
            print("\n")
    return topProviders

if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Get customers of an AS and subgraph',
            usage='%(prog)s [-I as-rel.datafile]')
    argParser.add_argument('-I', dest='as_rel_data', help='AS relation data file',
                           default=None)
    args = argParser.parse_args()

    if args.as_rel_data is None:
        print("AS relationship data file not provided!!!\n")
        sys.exit(-1)

    graphData = readASRelData(args.as_rel_data)
    p2c_edges,  p2p_edges = seperateEdges(graphData)

    ReadIsoCountryCodes(isocountryFile)
    ASRank = ReadAsnRankFile(asnRankFile)
    EYEBALLS = ReadEyeballData(eyeballFile)
    ALL_EYEBALLS_ASNS = GetEyeballASNs(EYEBALLS)
    FILTERED_EYEBALLS_1000 = FilterEyeballBySize(EYEBALLS, 1000)
    FILTERED_EYEBALL_ASNS_1000 = GetEyeballASNs(FILTERED_EYEBALLS_1000)

    FILTERED_EYEBALLS_2000 = FilterEyeballBySize(EYEBALLS, 2000)
    FILTERED_EYEBALL_ASNS_2000 = GetEyeballASNs(FILTERED_EYEBALLS_2000)


    FILTERED_EYEBALLS_5000 = FilterEyeballBySize(EYEBALLS, 5000)
    FILTERED_EYEBALL_ASNS_5000 = GetEyeballASNs(FILTERED_EYEBALLS_5000)

    # Filter ASNs using ASN Ranks dataset
    seen_asns = []
    stub_asns = []
    non_stub_asns = []
    provider_asns = []
    no_prefix_announced = []
    no_address_announced = []
    zero_degree = []
    tier1_asns = []

    prov_asn_with_hgs = []
    prov_asn_ex_hgs = []
    prov_asn_ex_hgs_en_5000 = []
    prov_asn_ex_hgs_en_2000 = []
    prov_asn_ex_hgs_en_1000 = []
    prov_asn_ex_hgs_all_en = []

    for jsonStr in ASRank:
        res = json.loads(jsonStr)

        if res['seen'] is True:
            seen_asns.append(res)

        if res['asnDegree']['total'] == 0:
            zero_degree.append(res)

        if res['asnDegree']['customer'] == 0:
            stub_asns.append(res)
        else:
            non_stub_asns.append(res)

        if (res['asnDegree']['provider'] != 0) and (res['asnDegree']['transit'] != 0) and (res['asnDegree']['customer'] != 0):
            asn = int(res["asn"])
            prov_asn_with_hgs.append(res)
            if (asn not in hypergiantasns):
                prov_asn_ex_hgs.append(res)

            if (asn not in hypergiantasns) and (asn not in ALL_EYEBALLS_ASNS):
                prov_asn_ex_hgs_all_en.append(res)

            if (asn not in hypergiantasns) and (asn not in FILTERED_EYEBALL_ASNS_5000):
                prov_asn_ex_hgs_en_5000.append(res)

            if (asn not in hypergiantasns) and (asn not in FILTERED_EYEBALL_ASNS_2000):
                prov_asn_ex_hgs_en_2000.append(res)

            if (asn not in hypergiantasns) and (asn not in FILTERED_EYEBALL_ASNS_1000):
                prov_asn_ex_hgs_en_1000.append(res)


        if (res['asnDegree']['provider'] == 0) and (res['asnDegree']['transit'] != 0):
            asn = int(res["asn"])
            if (asn not in hypergiantasns) and (asn not in ALL_EYEBALLS_ASNS):
                tier1_asns.append(res)

        if res['announcing']['numberPrefixes'] == 0:
            no_prefix_announced.append(res)

        if res['announcing']['numberAddresses'] == 0:
            no_address_announced.append(res)

    print("There are %s ASNs in dataset" % len(ASRank))
    print("There are %s Tier-1 ASNs in dataset" % len(tier1_asns))
    print("There are %s seen ASNs in dataset" % len(seen_asns))
    print("There are %s ASNs with zero degrees in dataset" % len(zero_degree))
    print("There are %s stub ASNs in the dataset" % len(stub_asns))
    print("There are %s non stub ASNs in the dataset" % len(non_stub_asns))
    print("There are %s provider ASNs in the dataset" % len(provider_asns))
    print("There are %s ASNs with no prefixes announced" % len(no_prefix_announced))
    print("There are %s ASNs with no addresses announced" % len(no_address_announced))


    print("There are %s provider ASNs including hypergiants" % len(prov_asn_with_hgs))
    print("There are %s provider ASNs excluding hypergiants" % len(prov_asn_ex_hgs))

    #upstreamStatsWithHGs = UpstreamStatsOverall(prov_asn_with_hgs, 'with_HGs')
    upstreamStatsExHGs = UpstreamStatsOverall(prov_asn_ex_hgs, 'Ex_HGs') 
    #upstreamStatsExHGs5000 = UpstreamStatsOverall(prov_asn_ex_hgs_en_5000, 'Ex_HGs_and_EN_5000') 
    #upstreamStatsExHGs2000 = UpstreamStatsOverall(prov_asn_ex_hgs_en_2000, 'Ex_HGS_and_EN_2000')
    #upstreamStatsExHGs1000 = UpstreamStatsOverall(prov_asn_ex_hgs_en_1000, 'Ex_HGS_and_EN_1000')
    #upstreamStatsExHGsAndEN = UpstreamStatsOverall(prov_asn_ex_hgs_all_en, 'Ex_HGS_and_all_ENs')
    #PlotGraphs(WithHGs=upstreamStatsWithHGs)
    #PlotGraphs(ExcludingHGs=upstreamStatsExHGs)
    #PlotGraphs(WithHGs=upstreamStatsWithHGs,
    #        ExcludingHGs=upstreamStatsExHGs,
    #        ExcludingHGsAllEyeballs=upstreamStatsExHGsAndEN)

    #PlotGraphs(ExcludingHGsEyeballs5000=upstreamStatsExHGs5000)
    #PlotGraphs(ExcludingHGsEyeballs2000=upstreamStatsExHGs2000)
    #PlotGraphs(ExcludingHGsEyeballs1000=upstreamStatsExHGs1000)
    #PlotGraphs(WithHGs=upstreamStatsWithHGs,
    #        ExcludingHGs=upstreamStatsExHGs)
    #PlotGraphs(ExcludingHGsEyeballs5000=upstreamStatsExHGs5000,
    #        ExcludingHGsEyeballs2000=upstreamStatsExHGs2000,
    #        ExcludingHGsEyeballs1000=upstreamStatsExHGs1000)
    #PlotGraphs(WithHGs=upstreamStatsWithHGs,
    #        ExcludingHGs=upstreamStatsExHGs,
    #        ExcludingHGsEyeballs5000=upstreamStatsExHGs5000,
    #        ExcludingHGsEyeballs2000=upstreamStatsExHGs2000,
    #        ExcludingHGsEyeballs1000=upstreamStatsExHGs1000)



    topproviders = ShowTopProvidersByUpstreamConn(prov_asn_ex_hgs)
    outlier_providers = []
    for asn in topproviders:
        customers = []
        #neigh = graphData[asn["asn"]]
        upstreams = []
        for edge in graphData.out_edges(asn["asn"]):
            if edge not in p2p_edges:
                upstreams.append(edge)

        if len(upstreams) != asn['asnDegree']['provider']:
            print("Providers in dataset does not match ASRank: %s vs %s" %(len(upstreams), asn['asnDegree']['provider']))

        for edge in graphData.in_edges(asn["asn"]):
            if edge not in p2p_edges:
                cust, asno = edge
                cust_pred = list(graphData.predecessors(cust))
                customers.append(cust)
                #print(cust_pred)
                if len(cust_pred) != 0:
                    downstream_cust_edges = graphData.in_edges(cust)
                    for down_cust_edge in downstream_cust_edges:
                        if down_cust_edge not in p2p_edges:
                            down_cust, up_cust = down_cust_edge
                            customers.append(down_cust)
                            #    print("Yes!!!")
                #customers.append(cust)
        sGraph = createSubgraph(graphData, asn["asn"], customers)
        print("Drawing graph for %s  %s   %s" %(asn["asn"], asn["asnName"], asn["organization"]["orgName"]))
        asdetails = {'ASN': asn["asn"], 'AS Name': asn["asnName"],
                'Org Name': asn["organization"]["orgName"],
                'Providers': asn['asnDegree']['provider'],
                'Customers': asn['asnDegree']['customer']}
        drawTopoGraph(sGraph)
        astype = input("Set type of Network")
        asdetails['Type of provider'] = astype
        outlier_providers.append(asdetails)

    with open('/scratch/upstreamData/top-asns', 'w') as f:
        f.write("Table showing the types of networks with large number of providers\n")
        f.write(tabulate(outlier_providers, headers='keys', tablefmt='pretty'))

        #print(customers)
    #print(p2p_edges)

    #UpstreamStatsByCountry(prov_asn_ex_hgs, isocodes)

    #print(isocodes)
    #print(iso_present)
