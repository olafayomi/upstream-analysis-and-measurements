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
#from IPython.display import display
from tabulate import tabulate
import ast

with open('/scratch/asns.jsonl', 'r') as json_file:
    internet = list(json_file)

with open('/scratch/eyeballdata2', 'r') as dfile:
    EYEDATASET = ast.literal_eval(dfile.read())

ccodes = ["EU"]
countries = ["European Union"]

with open('/scratch/countries_codes_and_coordinates.csv', 'r') as ccfile:
    ccode = csv.reader(ccfile) 
    for country in ccode:
        countries.append(country[0]) 
        ccodes.append(country[1])

FILTERED_EYEDATASET = []

for asn in EYEDATASET: 
    asno = asn["asn"]
    asno = asno.replace("AS", "")
    asn["asn"] = int(asno)
    # Filter eyeball networks with less than 1000 estimated users
    if asn["users"] >= 1000:
        FILTERED_EYEDATASET.append(asn)

eyeballasns = []

for asn in FILTERED_EYEDATASET:
    eyeballasns.append(asn["asn"])

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
seen_asn = []
stub_asns = [] 
non_stub_asns = []
provider_asns = []
no_prefix_announced = []
no_address_announced = []
zero_degree = []
tier1_asns = []
for json_str in internet:
    result = json.loads(json_str)
    #print("Result: %s" %result)
    if result['seen'] is True:
        seen_asn.append(result)

    if result['asnDegree']['total'] == 0:
        zero_degree.append(result)

    if result['asnDegree']['customer'] == 0: 
        stub_asns.append(result)
    else:
        non_stub_asns.append(result)

    if (result['asnDegree']['provider'] != 0) and (result['asnDegree']['transit'] != 0):
        asn = int(result["asn"])
        if (asn not in hypergiantasns) and (asn not in eyeballasns):
            provider_asns.append(result)

    if (result['asnDegree']['provider'] == 0) and (result['asnDegree']['transit'] != 0):
        asn = int(result["asn"])
        if (asn not in hypergiantasns) and (asn not in eyeballasns):
            tier1_asns.append(result)

    if result['announcing']['numberPrefixes']  == 0:
        no_prefix_announced.append(result)
    
    if result['announcing']['numberAddresses'] == 0:
        no_address_announced.append(result)

print("There are %s ASNs in dataset" %len(internet))
print("There are %s Tier-1 ASNs in dataset"  %len(tier1_asns))
print("There are %s seen ASNs in dataset" %len(seen_asn))
print("There are %s ASNs with zero degrees in dataset" %len(zero_degree))
print("There are %s stub ASNs in the dataset" %len(stub_asns))
print("There are %s non stub ASNs in the dataset" %len(non_stub_asns))
print("There are %s provider ASNs in the dataset" %len(provider_asns))
print("There are %s ASNs with no prefixes announced" %len(no_prefix_announced))
print("There are %s ASNs with no addresses announced" %len(no_address_announced))

upstream_numbers_to_providers = {}
upstream_list = []
for asns in provider_asns: 
    upstream = str(asns['asnDegree']['provider'])
    upstream_list.append(int(asns['asnDegree']['provider']))
    #print(upstream)
    if upstream not in upstream_numbers_to_providers:
        upstream_numbers_to_providers.update({upstream: 1})
    else:
        upstream_numbers_to_providers[upstream] += 1


#print(upstream_numbers_to_providers)
#print("Upstream for each provider: %s" %upstream_list)
#print("Length of upstream list: %s" %len(upstream_list))
for upstreams in upstream_numbers_to_providers:
    percentage = (float(upstream_numbers_to_providers[upstreams])/len(provider_asns))*100.0

upstream_provider = pd.DataFrame({"Upstreams": upstream_numbers_to_providers.keys(), "Providers": upstream_numbers_to_providers.values()})                      # [upstream_numbers_to_providers])
length = len(upstream_numbers_to_providers)

s = pd.Series(upstream_list, name = 'upstreams') 

df = pd.DataFrame(s) 
plt.title("KDE of upstreams observed for Tier-2/3 ISPs excluding hypergiants and eyeball networks smaller than 1000 users")
#plt.title("KDE of upstreams observed for Tier-2/3 ISPs excluding hypergiants")
plt.xlabel("Distribution of number of upstreams amongst providers")
plt.ylabel("K-DENSITY")
s.plot.kde()
print(df.describe())
stats_df = df.groupby('upstreams')['upstreams'].agg('count').pipe(pd.DataFrame).rename(columns =  {'upstreams': 'providers'})
print("Sum of the number of providers seen for each upstreams: %s" %sum(stats_df['providers']))
stats_df['pdf'] = stats_df['providers'] / sum(stats_df['providers'])
stats_df['cdf'] = stats_df['pdf'].cumsum()
stats_df['percentage of providers'] = (stats_df['providers']/stats_df['providers'].sum()) * 100
print("stats_df calculated using Stackflow link")
#print(stats_df)
print("Table showing the CDF,PDF and percentage of providers with different upstreams")
print(tabulate(stats_df, headers = 'keys', tablefmt = 'pretty'))
stats_df = stats_df.reset_index()
stats_df.plot(x = 'upstreams', y = ['pdf', 'cdf'], grid = True)
plt.title("CDF/PDF of upstreams observed for Tier-2/3 ISPs excluding hypergiants and eyeball networks smaller than 1000 users")
#plt.title("CDF/PDF of upstreams observed for Tier-2/3 ISPs excluding hypergaints")
plt.xlabel("Number of upstreams amongst providers")
#plt.ylabel("DENSITY")
plt.ylabel("CDF/PDF")

#stats_df.plot.bar(x = 'upstreams', y = ['pdf', 'cdf'], grid = True)
#plt.savefig("test_histogram.png")
plt.show(block=True)
#plt.bar(x = 'upstreams', y = ['pdf', 'cdf'], grid = True)



#print(upstream_provider)
#print(upstream_provider.dtypes)
#print(upstream_provider.nlargest(40, 'Providers'))
#count, bins_count = np.histogram(upstream_provider['Upstreams'].astype(str).astype(int), bins = 39)
#print(bins_count)
#upstream_provider['pdf'] = upstream_provider['Providers']/sum(upstream_provider['Providers'])
#print("Initial attempts")
#print(upstream_provider)
#upstream_provider['cdf'] = upstream_provider['pdf'].cumsum()
#upstream_provider = upstream_provider.reset_index()
#print("again")
#print(upstream_provider)







#provider_df = pd.DataFrame(provider_asns)
#print(provider_df)
#print(provider_df.info())
#asnDegree = provider_df[['asnDegree']]
#print(asnDegree)
#jsonObj = pd.read_json('/scratch/asns.jsonl', lines=True)
#jsonObj.head()
#print(jsonObj)
#jsonObj.info()
#asn_degree = jsonObj[["asn", "asnDegree", "announcing"]]
#print(asn_degree)
