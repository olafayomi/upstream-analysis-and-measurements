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

ipv4_latency = '/scratch/amp-latency-ipv6-june.csv' 

with open('/scratch/RIPE-Atlas-measurement-2-probe-1004619.json', 'r') as json_file:
    measurement = json.load(json_file)

print(type(measurement))
for item in measurement:
    print("Address: %s , Name: %s, Probe Source Address: %s, Probe Public IP Address(From): %s"
          % (item['addr'], item['name'], item['src_addr'], item['from']))

#df = pd.read_csv(ipv4_latency) 
#df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
#df['rtt_ms'] = pd.to_numeric(df['rtt_ms'], errors = 'coerce').fillna(9.6).astype('float')
##df2 = df[1500:1600]
#print(df)
#print("Min RTT is %sms" %df['rtt_ms'].min())
#print("Mean RTT is %sms" %df['rtt_ms'].mean())
#print("Median RTT is %sms" %df['rtt_ms'].median())
#df.plot(x='timestamp', y='rtt_ms', grid=False)
#plt.title("Time series for AMP latency data")
#plt.xlabel("Time")
#plt.ylabel("RTT")
#plt.show(block=True)
