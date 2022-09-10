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
import requests
import json 
import time
import ast
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import csv


APNIC_URL = "https://stats.labs.apnic.net/cgi-bin/aspopjson"
#response = requests.get(APNIC_URL)
#DATASET = ast.literal_eval(response.text)

with open('/scratch/eyeballdata2', 'r') as dfile:
    DATASET = ast.literal_eval(dfile.read())

with open('/scratch/asns.jsonl', 'r') as json_file:
    internet = list(json_file)


with open('/scratch/countries_codes_and_coordinates.csv', 'r') as ccfile:
    ccode = csv.reader(ccfile) 
    for country in ccode: 
        print(country)

users = []
FILTERED_EYEDATASET = []
for asn in DATASET:
    ASN = asn["asn"] 
    ASN = ASN.replace("AS", "")
    asn["asn"] = int(ASN)
    users.append(int(asn["users"]))
    if asn["users"] >= 5000:
        FILTERED_EYEDATASET.append(asn)
    #print("ASN: %s" %asn)
print(FILTERED_EYEDATASET)
eyeballasns = [] 
for asn in FILTERED_EYEDATASET:
    eyeballasns.append(asn["asn"])

print("User list size is %s" %len(users))
print("Eyeball dataset size is %s" %len(DATASET))
if 139036 in eyeballasns:
    print("139036 is an eyeball network and tier2 provider")
valid_eyeball = []
for user in users:
    if user >= 2000:
        valid_eyeball.append(user) 

print("There are %s eyeball networks with 2000 or more users" %len(valid_eyeball))
s = pd.Series(users, name = 'users')
#s.plot.kde()
df = pd.DataFrame(s) 
stats_df = df.groupby('users')['users'].agg('count').pipe(pd.DataFrame).rename(columns =  {'users': 'frequency'})

#stats_df['pdf'] = stats_df['frequency'] /sum(stats_df['frequency'])
#stats_df['cdf'] = stats_df['pdf'].cumsum() 
#print(stats_df)
#stats_df = stats_df.reset_index()

#stats_df.plot(x = 'users', y = ['pdf', 'cdf'], grid = True)

#plt.xlabel("Estimated users in eyeball networks")
#plt.ylabel("CDF/PDF")
#plt.show(block=True)


