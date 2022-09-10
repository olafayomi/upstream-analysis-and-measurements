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
import argparse
import json
import csv
import ipaddress
from pprint import pprint
import numpy as np


def getResults(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    mresp = requests.get(url)
    data = mresp.json()
    res_url = data['result']
    res_data = requests.get(res_url)
    results = res_data.json()
    return results


if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Print measurements from msm ID',
            usage='%(prog)s [-i msm_id]')

    argParser.add_argument('-i', dest='msm',
                           help='''measurement id''',
                           type=int,
                           default=44243938)

    argParser.add_argument('-p', dest='probe',
                           help='''probe ID''',
                           type=int,
                           default=12328)

    args = argParser.parse_args()
    
    results = getResults(args.msm)
    
    msm_by_prb = {}

    for res in results:
        if res['prb_id'] in msm_by_prb:
            msm_by_prb[res['prb_id']].append(res)
        else:
            msm_by_prb[res['prb_id']] = [res]

    for prb_id, msms in msm_by_prb.items(): 
        min_rtt = []
        avg_rtt = []
        max_rtt = [] 
        print("Probe ID: %s" % prb_id)
        for msm in msms: 
            if msm['min'] > 0:
                min_rtt.append(msm['min'])

            if msm['avg'] > 0:
                avg_rtt.append(msm['avg'])

            if msm['max'] > 0:
                max_rtt.append(msm['max'])

        #print("There are %s measurements for each probe" % len(msms))
        #pprint(msms)
        len_min  = len(min_rtt)
        len_avg  = len(avg_rtt)
        len_max  = len(max_rtt)
        if (len_min < 1) and (len_avg < 1) and (len_max < 1):
            print("Min RTT: %s, Avg RTT: %s, Max RTT: %s" % (min_rtt, avg_rtt, max_rtt))
            print("\n")
            continue

        print("    Minimum value of min RTT: %s" % min(min_rtt))
        print("    Average value of min RTT: %s" % np.mean(min_rtt))
        print("    Median value of min RTT: %s"   % np.median(min_rtt))
        print("    Max value of min RTT: %s"  %max(min_rtt))
        print("    Standard Dev of min RTT: %s"  %np.std(min_rtt))
        print("    ----------------------------------------")
        print("    Minimum value of average RTT: %s" % min(avg_rtt))
        print("    Average value of average RTT: %s" % np.mean(avg_rtt))
        print("    Max value of average RTT: %s" % max(avg_rtt))
        print("    Median value of  average RTT: %s" % np.median(avg_rtt))
        print("    Standard Dev of average RTT: %s" % np.std(avg_rtt))
        print("    --------------------------------------------")
        print("    Minimum value of max RTT: %s" % min(max_rtt))
        print("    Average value of max RTT: %s" % np.mean(max_rtt))
        print("    Max value of max RTT: %s" % max(max_rtt))
        print("    Median value of max RTT: %s" % np.median(max_rtt))
        print("    Standard Dev of average RTT: %s" % np.std(max_rtt))
        print("\n")

    prb_within_range = []

    for prb_id, msms in msm_by_prb.items():
        min_rtt = []
        max_rtt = []
        avg_rtt = []
        for msm in msms:
            if msm['min'] > 0:
                min_rtt.append(msm['min'])

            if msm['max'] > 0:
                max_rtt.append(msm['max'])

            if msm['avg'] > 0: 
                avg_rtt.append(msm['avg'])

        len_min  = len(min_rtt)
        len_avg  = len(avg_rtt)
        len_max  = len(max_rtt)
        if (len_min < 1) and (len_avg < 1) and (len_max < 1):
            continue

        if np.mean(avg_rtt) > 100:
            continue

        if np.mean(avg_rtt) < 40:
            continue

        prb_within_range.append(prb_id)


    further_processed = []
    for prb in prb_within_range:
        msms = msm_by_prb[prb] 
        avg = []
        for msm in msms:
            if msm['avg'] > 0:
                avg.append(msm['avg']) 

        #min_of_avg = min(avg)
        #max_of_avg = max(avg)
        #diff = max_of_avg - min_of_avg
        #mean = np.mean(avg)
        #std_dev = np.std(avg)

        #if (min_of_avg > 35) and (std_dev >= 10):
        #    further_processed.append(prb)
            
        #if (min(avg) > 40) and (min(avg) < 100):
        #    further_processed.append(prb)
        
        avg_avg = np.mean(avg)
        if (avg_avg > 40) and (avg_avg < 100):
            further_processed.append(prb)


    min_rtt_probes = []
    avg_rtt_probes = []
    min_avg_probes = []
    avg_avg_probes = []

    for prb_id, msms in msm_by_prb.items():
        min_rtt = []
        avg_rtt = []

        for msm in msms:
            if msm['min'] > 0:
                min_rtt.append(msm['min'])

            if msm['avg'] > 0:
                avg_rtt.append(msm['avg'])

        len_min  = len(min_rtt)
        len_avg  = len(avg_rtt)
        if (len_min < 1) and (len_avg < 1):
            continue

        if (min(min_rtt) > 40) and (min(min_rtt) < 100):
            min_rtt_probes.append(prb_id)


        if (min(avg_rtt) > 40) and (min(avg_rtt) < 100):
            avg_rtt_probes.append(prb_id)
        
        avg_avg = np.mean(avg_rtt)
        if (avg_avg > 40) and (avg_avg < 100):
            avg_avg_probes.append(prb_id)

        min_avg = np.mean(min_rtt) 
        if (min_avg > 40) and (min_avg < 100): 
            min_avg_probes.append(prb_id)

    print("Total number of probes: %s" % len(msm_by_prb))
    #print("Probes using min RTT: %s" % min_rtt_probes)
    #print("Probes using average of min RTT: %s" % min_avg_probes)
    print("Probes using avg RTT: %s" % avg_rtt_probes)
    print("Probes using average of average RTT: %s" % avg_avg_probes)
    print("Probes for further process: %s"   % prb_within_range)
    print("Probes for futher processing: %s" % len(prb_within_range))
    print("\n")
    print("Further processed based on avg RTT: %s" % further_processed)
    print("Number of probes in further_processed: %s" % len(further_processed))
    
    for prb in further_processed: 
        print("Probe ID: %s" % prb)
        msms = msm_by_prb[prb]
        avg_rtt = [] 
        for msm in msms:
            if msm['avg'] > 0:
                avg_rtt.append(msm['avg'])
        print("   Average RTT across intervals: %s" % avg_rtt)
        print("   Standard dev of avg RTT: %s" % np.std(avg_rtt))
        print("\n")

    #for prb in avg_avg_probes:
    #    print("Probe ID: %s" % prb)
    #    msms = msm_by_prb[prb]
    #    min_rtt = []
    #    avg_rtt = []
    #    for msm in msms:
    #        min_rtt.append(msm['min'])
    #        avg_rtt.append(msm['avg'])

    #    print("    Minimum RTT across all pings: %s" % min_rtt)
    #    print("    Minimum of min RTT across all pings: %s" % min(min_rtt))
    #    print("    Average min RTT across all pings: %s" % np.mean(min_rtt))
    #    print("    Average RTT across all pings: %s" % avg_rtt)
    #    print("    Mininum of average RTT across all pings: %s" % min(avg_rtt))
    #    print("    Average of average RTT across all pings: %s" % np.mean(avg_rtt))
    #    print("\n")

    

    

