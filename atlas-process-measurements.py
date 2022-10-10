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
import ipaddress
from pprint import pprint
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tabulate import tabulate
import argparse


def getResults(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    mresp = requests.get(url)
    data = mresp.json()
    res_url = data['result']
    res_data = requests.get(res_url)
    results = res_data.json()
    return results


def getMsmTarget(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    resp = requests.get(url)
    data = resp.json()
    target = data["target_ip"]
    return target


if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Analyse measurements read from file',
            usage='%(prog)s [-p pingmsmfile]')

    argParser.add_argument('-p', dest='pingmsmfile',
                           help='''File where ping measurement ids
                                are written''',
                           type=str,
                           default='/scratch/measurements/ping/six-hour-interval-ping-msms.json')

    argParser.add_argument('-o', dest='plot_dir',
                           help='''Directory to write CDF plots''',
                           type=str,
                           default='/scratch/measurements/analysis')

    argParser.add_argument('-l', dest='min_rtt',
                           help='Minimum RTT to filter probes to consider',
                           type=float, default=35)

    argParser.add_argument('-u', dest='max_rtt',
                           help='Maximum RTT to filter probes to conider',
                           type=float, default=100)

    args = argParser.parse_args()
    path = Path(args.pingmsmfile)
    directory = Path(args.plot_dir)

    if path.is_file() is False:
        print("%s does not exist!!!" % args.pingmsmfile)
        sys.exit(-1)

    if directory.is_dir() is False:
        print("%s does not exist!!!" % args.plot_dir)
        sys.exit(-1)

    with open(args.pingmsmfile, 'r') as msmfile:
        msms = json.load(msmfile)

    # A Dictionary of measurements and probes with game server as key
    prov_msm_probes = {}

    for msm in msms:

        results = getResults(msm)
        target = getMsmTarget(msm)

        # print("Processing measurement: %s" % msm)
        if target == "162.254.197.36":
            
            if 'Valve' not in prov_msm_probes:
                prov_msm_probes['Valve'] = []
            prbs_by_msm = {}

            for result in results:
                if result["prb_id"] in prbs_by_msm:
                    prbs_by_msm[result["prb_id"]].append(result)
                else:
                    prbs_by_msm[result["prb_id"]] = [result]


            for prb, prb_msms in prbs_by_msm.items():
                prov_msm_probes['Valve'].append({prb: prb_msms})

        if target == "185.60.112.157":

            if 'Blizzard' not in prov_msm_probes:
                prov_msm_probes['Blizzard'] = []
            prbs_by_msm = {}

            for result in results:
                if result["prb_id"] in prbs_by_msm:
                    prbs_by_msm[result["prb_id"]].append(result)
                else:
                    prbs_by_msm[result["prb_id"]] = [result]

            for prb, prb_msms in prbs_by_msm.items():
                prov_msm_probes['Blizzard'].append({prb: prb_msms})

        if target == "5.200.20.245":

            if 'Ubisoft' not in prov_msm_probes:
                prov_msm_probes['Ubisoft'] = []
            prbs_by_msm = {}

            for result in results:
                if result["prb_id"] in prbs_by_msm:
                    prbs_by_msm[result["prb_id"]].append(result)
                else:
                    prbs_by_msm[result["prb_id"]] = [result]

            for prb, prb_msms in prbs_by_msm.items():
                prov_msm_probes['Ubisoft'].append({prb: prb_msms})

    prov_msm_probes_u = {}
    for server, prbs in prov_msm_probes.items():
        unique_prb_list = set()
        prb_by_msm_list = []
        for prb in prbs:
            for prb_id, msms in prb.items():
                if prb_id not in unique_prb_list:
                    prb_by_msm_list.append(prb)
                    unique_prb_list.add(prb_id)
        prov_msm_probes_u[server] = prb_by_msm_list

    prov_msm_probes = prov_msm_probes_u

    for server, prbs in prov_msm_probes.items():
        print("Measurements to %s" % server)
        i = 0
        for prb in prbs:
            for prb_id, msms in prb.items():
                if len(msms) != 8:
                    msm_id = msms[0]['msm_id']
                    #pprint(msms)
                    print("     Probe %s has %s results to %s server in %s"
                          % (prb_id, len(msms), server, msm_id))
                    i += 1

        #pprint(prbs)
        print("%s probes have measurements not equal to 8" % i)
        print("Total number of probes to %s: %s\n" % (server, len(prbs)))

    
    prov_prb_rtt = {}
    provider_probes_trace_median = {}
    for server, prbs in prov_msm_probes.items():
        for prb in prbs:
            for prb_id, msms in prb.items():
                msms_median_rtts = []
                if len(msms) >= 5:
                    i = 0
                    for msm in msms:
                        i += 1
                        rtt_vals = []
                        res = msm['result']
                        msm_id = msm['msm_id']
                        for rtt in res:
                            try:
                                rtt_vals.append(rtt['rtt'])
                            except KeyError:
                                print("RTT result for probe %s at interval %s in msm %s: %s"
                                      % (prb_id, i, msm_id, res))
                                continue
                        #print("RTT values for probe %s at interval %s in msm %s: %s"
                        #      % (prb_id, i, msm_id, rtt_vals))
                        if len(rtt_vals) > 1:
                            median_rtt = np.median(rtt_vals)
                        #print("Median RTT for probe %s at interval %s in msm: %s: %s"
                        #      % (prb_id, i, msm_id, median_rtt))
                        if not np.isnan(median_rtt):
                            msms_median_rtts.append(median_rtt)

                    
                    # print("\n")
                    if server not in prov_prb_rtt:
                        prov_prb_rtt[server] = [{prb_id: msms_median_rtts}]
                    else:
                        prov_prb_rtt[server].append({prb_id: msms_median_rtts})
                                    
                    if ((np.mean(msms_median_rtts) > args.min_rtt) and 
                            (np.mean(msms_median_rtts) < args.max_rtt)):
                        if server not in provider_probes_trace_median:
                            provider_probes_trace_median[server] = [prb_id]
                        else:
                            provider_probes_trace_median[server].append(prb_id)

    for server, prbs in prov_prb_rtt.items():
        filename ='/scratch/probe-list/ping-measurements/'+str(server)+'-probe-rtt-list.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(prbs, f, ensure_ascii=False, indent=4, sort_keys=True)

    with open('/scratch/probe-list/ping-measurements/probes-for-trace-filtered-by-median-rtt-per-game-provider.json', 'w', encoding='utf-8') as f:
        json.dump(provider_probes_trace_median, f, ensure_ascii=False)

    provider_probes_trace_avg = {}
    for server, prbs in prov_msm_probes.items():
        for prb in prbs:
            for prb_id, msms in prb.items():
                avg_rtt = []

                for msm in msms:
                    rtt_vals = []
                    if msm['avg'] > 0:
                        avg_rtt.append(msm['avg'])

                if len(avg_rtt) < 5:
                    continue

                if np.mean(avg_rtt) > args.max_rtt:
                    continue

                if np.mean(avg_rtt) < args.min_rtt:
                    continue

                avg_avg = np.mean(avg_rtt)
                if (avg_avg > args.min_rtt) and (avg_avg < args.max_rtt):
                    if server not in provider_probes_trace_avg:
                        provider_probes_trace_avg[server] = [prb_id]
                    else:
                        provider_probes_trace_avg[server].append(prb_id)

    with open('/scratch/probe-list/ping-measurements/probes-for-trace-filtered-by-avg-rtt-per-game-provider.json', 'w', encoding='utf-8') as f:
        json.dump(provider_probes_trace_avg, f, ensure_ascii=False)

    for server, prb_rtts in prov_prb_rtt.items():
        print("For %s:" % server)
        i = 0
        for prb_rtt in prb_rtts:
            for prb_id, median_rtt in prb_rtt.items():
                if len(median_rtt) != 8:
                    print("    Probe %s has %s median RTT values to %s"
                          % (prb_id, len(median_rtt), server))
                    i += 1
        print("%s probes have measurements not equal to 8" % i)
        print("Total number of probes with median RTT list to %s: %s\n"
              % (server, len(prb_rtts)))

    prov_prb_min_rtt = {}
    prov_prb_max_rtt = {}
    combined_prb_min_max = {}
    for server, prb_rtts in prov_prb_rtt.items():
        for prb_rtt in prb_rtts:
            for prb_id, median_rtt in prb_rtt.items():
                if len(median_rtt) >= 5:
                    min_median_rtt = np.min(median_rtt)
                    max_median_rtt = np.max(median_rtt)

                    if not np.isnan(min_median_rtt):
                        if server not in prov_prb_min_rtt:
                            prov_prb_min_rtt[server] = [(prb_id, min_median_rtt)]
                        else:
                            prov_prb_min_rtt[server].append((prb_id, min_median_rtt))

                    if not np.isnan(max_median_rtt):
                        if max_median_rtt > 200:
                            max_median_rtt = 200
                        if server not in prov_prb_max_rtt:
                            prov_prb_max_rtt[server] = [(prb_id, max_median_rtt)]
                        else:
                            prov_prb_max_rtt[server].append((prb_id, max_median_rtt))

                    if (not np.isnan(min_median_rtt)) and (not np.isnan(max_median_rtt)):
                        if max_median_rtt > 200:
                            max_median_rtt = 200
                        if server not in combined_prb_min_max:
                            combined_prb_min_max[server] = [(prb_id, min_median_rtt, max_median_rtt)]
                        else:
                            combined_prb_min_max[server].append((prb_id, min_median_rtt, max_median_rtt))


    for server, prb_min_max_rtts in combined_prb_min_max.items():

       if server == 'Blizzard':
           blizzard_df = pd.DataFrame(prb_min_max_rtts, columns=['Probe ID', 'Min RTT', 'Max RTT'])
           blizzard_df.sort_values(by='Min RTT', ascending=True, inplace=True)
           blizzard_df.reset_index(drop=True)
           blizzard_df['index'] = range(1, len(blizzard_df)+1)
           print(blizzard_df.head(20))
           fig, ax = plt.subplots()
           ax.scatter(blizzard_df['index'],
                      blizzard_df['Min RTT'], c="blue", s=2,
                      label="Minimum RTT/Probe")
           ax.scatter(blizzard_df['index'],
                      blizzard_df['Max RTT'], c="red", s=2,
                      label="Maximum RTT/Probe")
           plt.title("Scatter plot of minimum and maximum RTT values to Blizzard IP from %s probes [sorted by Min RTT]" % len(blizzard_df.index))
           plt.xlabel("Number of Probes)")
           plt.ylabel("RTT (ms)")
           plt.legend(fontsize=15)
           plt.grid(True)
           plt.show(block=True)


       if server == 'Ubisoft':
           ubisoft_df = pd.DataFrame(prb_min_max_rtts, columns=['Probe ID', 'Min RTT', 'Max RTT'])
           ubisoft_df.sort_values(by='Min RTT', ascending=True, inplace=True)
           ubisoft_df.reset_index(drop=True)
           ubisoft_df['index'] = range(1, len(ubisoft_df)+1)
           print(ubisoft_df.head(20))
           fig, ax = plt.subplots()
           ax.scatter(ubisoft_df['index'],
                      ubisoft_df['Min RTT'], c="blue", s=2,
                      label="Minimum RTT/Probe")
           ax.scatter(ubisoft_df['index'],
                      ubisoft_df['Max RTT'], c="red", s=2,
                      label="Maximum RTT/Probe")
           plt.title("Scatter plot of minimum and maximum  RTT values to Ubisoft IP  from %s probes [sorted by Min RTT]" % len(ubisoft_df.index)) 
           plt.xlabel("Number of Probes")
           plt.ylabel("RTT (ms)")
           plt.legend(fontsize=15)
           plt.grid(True)
           plt.show(block=True)

       if server == 'Valve':
           valve_df = pd.DataFrame(prb_min_max_rtts, columns=['Probe ID', 'Min RTT', 'Max RTT'])
           valve_df.sort_values(by='Min RTT', ascending=True, inplace=True)
           valve_df.reset_index(drop=True)
           valve_df['index'] = range(1, len(valve_df)+1)
           print(valve_df.head(20))
           fig, ax = plt.subplots()
           ax.scatter(valve_df['index'],
                      valve_df['Min RTT'], c="blue", s=2,
                      label="Minimum RTT/Probe")
           ax.scatter(valve_df['index'],
                      valve_df['Max RTT'], c="red", s=2,
                      label="Maximum RTT/Probe")
           plt.title("Scatter plot of minimum and maximum RTT values to Valve IP from %s probes [sorted by Min RTT]" % len(valve_df.index)) 
           plt.xlabel("Number of Probes")
           plt.ylabel("RTT (ms)")
           plt.legend(fontsize=15)
           plt.grid(True)
           plt.show(block=True)



    for server, prb_min_rtts in prov_prb_min_rtt.items():

        if server == 'Blizzard':
            blizzard_min_rtt_df = pd.DataFrame(prb_min_rtts,  columns=['Probe ID', 'Min RTT'])
            blizzard_min_rtt_df.sort_values(by='Min RTT', ascending=True, inplace=True)
            blizzard_min_rtt_df.reset_index(drop=True)
            blizzard_min_rtt_df['index'] = range(1, len(blizzard_min_rtt_df) +1)
            #blizzard_min_rtt_df.index = blizzard_min_rtt_df.index + 1
            print(blizzard_min_rtt_df.head(20))
            fig, ax = plt.subplots()
            ax.scatter(blizzard_min_rtt_df['index'],
                       blizzard_min_rtt_df['Min RTT'], c="blue", s=2,
                       label="Minimum RTT/Probe")
            plt.title("Scatter plot of minimum RTT value to Blizzard IP from %s probes [sorted]" % len(blizzard_min_rtt_df.index))
            plt.xlabel("Number of Probes")
            plt.ylabel("RTT (ms)")
            plt.legend(fontsize=15)
            plt.grid(True)
            plt.show(block=True)
            
        if server == 'Ubisoft':
            ubisoft_min_rtt_df = pd.DataFrame(prb_min_rtts, columns=['Probe ID', 'Min RTT'])
            ubisoft_min_rtt_df.sort_values(by='Min RTT', ascending=True, inplace=True)
            ubisoft_min_rtt_df.reset_index(drop=True)
            ubisoft_min_rtt_df['index'] = range(1, len(ubisoft_min_rtt_df) + 1)
            #ubisoft_min_rtt_df.index = ubisoft_min_rtt_df.index + 1
            print(ubisoft_min_rtt_df.head(20))
            fig, ax = plt.subplots()
            ax.scatter(ubisoft_min_rtt_df['index'],
                       ubisoft_min_rtt_df['Min RTT'], c="blue", s=2,
                       label="Minimum RTT/Probe")
            plt.title("Scatter plot of minimum RTT value to Ubisoft IP from %s probes [sorted]" % len(ubisoft_min_rtt_df.index)) 
            plt.xlabel("Number of Probes")
            plt.ylabel("RTT (ms)")
            plt.legend(fontsize=15)
            plt.grid(True)
            plt.show(block=True)

        if server == 'Valve':
            valve_min_rtt_df = pd.DataFrame(prb_min_rtts, columns=['Probe ID', 'Min RTT'])
            valve_min_rtt_df.sort_values(by='Min RTT', ascending=True, inplace=True)
            valve_min_rtt_df.reset_index(drop=True)
            valve_min_rtt_df['index'] = range(1, len(valve_min_rtt_df) +1)
            valve_min_rtt_df.index = valve_min_rtt_df.index + 1
            fig, ax = plt.subplots()
            ax.scatter(valve_min_rtt_df['index'],
                       valve_min_rtt_df['Min RTT'], c="blue", s=2,
                       label="Minimum RTT/Probe")
            plt.title("Scatter plot of minimum RTT value to Valve IP from %s probes [sorted]" % len(valve_min_rtt_df.index))
            plt.xlabel("Number of Probes")
            plt.ylabel("RTT (ms)")
            plt.legend(fontsize=15)
            plt.grid(True)
            plt.show(block=True)

    for server, prb_max_rtts in prov_prb_max_rtt.items():

        if server == 'Blizzard':
            blizzard_max_rtt_df = pd.DataFrame(prb_max_rtts, columns=['Probe ID', 'Max RTT'])
            blizzard_max_rtt_df.sort_values(by='Max RTT', ascending=True, inplace=True)
            blizzard_max_rtt_df.reset_index(drop=True)
            blizzard_max_rtt_df['index'] = range(1, len(blizzard_max_rtt_df)+1)
            #blizzard_max_rtt_df.index = blizzard_max_rtt_df.index + 1
            fig, ax = plt.subplots()
            ax.scatter(blizzard_max_rtt_df['index'],
                       blizzard_max_rtt_df['Max RTT'], c="red", s=2,
                       label="Maximum RTT/Probe")
            plt.title("Scatter plot of maximum RTT values to Blizzard IP from %s probes [sorted]" % len(blizzard_max_rtt_df.index))
            plt.xlabel("Number of Probes")
            plt.ylabel("RTT (ms)")
            plt.legend(fontsize=15)
            plt.grid(True)
            plt.show(block=True)

        if server == 'Ubisoft':
            ubisoft_max_rtt_df = pd.DataFrame(prb_max_rtts, columns=['Probe ID', 'Max RTT'])
            ubisoft_max_rtt_df.sort_values(by='Max RTT', ascending=True, inplace=True)
            ubisoft_max_rtt_df.reset_index(drop=True)
            ubisoft_max_rtt_df['index'] = range(1, len(ubisoft_max_rtt_df)+1)
            #ubisoft_max_rtt_df.index = ubisoft_max_rtt_df.index + 1 
            fig, ax = plt.subplots()
            ax.scatter(ubisoft_max_rtt_df['index'],
                       ubisoft_max_rtt_df['Max RTT'], c="red", s=2,
                       label="Maximum RTT/Probe")
            plt.title("Scatter plot of maximum RTT value to Ubisoft IP from %s probes [sorted]" % len(ubisoft_max_rtt_df.index))
            plt.xlabel("Number of Probes")
            plt.ylabel("RTT (ms)")
            plt.legend(fontsize=15)
            plt.grid(True)
            plt.show(block=True)

        if server == 'Valve':
            valve_max_rtt_df = pd.DataFrame(prb_max_rtts, columns=['Probe ID', 'Max RTT'])
            valve_max_rtt_df.sort_values(by='Max RTT', ascending=True, inplace=True)
            valve_max_rtt_df.reset_index(drop=True)
            valve_max_rtt_df['index'] = range(1, len(valve_max_rtt_df)+1)
            #valve_max_rtt_df.index = valve_max_rtt_df.index + 1
            fig, ax = plt.subplots()
            ax.scatter(valve_max_rtt_df['index'],
                       valve_max_rtt_df['Max RTT'], c="red", s=2,
                       label="Maximum RTT/Probe")
            plt.title("Scatter plot of maximum RTT value Valve IP from %s probes [sorted]" % len(valve_max_rtt_df.index)) 
            plt.xlabel("Number of Probes")
            plt.ylabel("RTT (ms)")
            plt.legend(fontsize=15)
            plt.grid(True)
            plt.show(block=True)

    print(blizzard_min_rtt_df.describe())
    #print(tabulate(blizzard_min_rtt_df, headers='keys', tablefmt='pretty'))

    fig, ax = plt.subplots()
    ax.scatter(blizzard_min_rtt_df['index'],
               blizzard_min_rtt_df['Min RTT'], c="blue", s=2,
               label="Minimum RTT/Probe")
    ax.scatter(blizzard_max_rtt_df['index'],
               blizzard_max_rtt_df['Max RTT'], c="red", s=2,
               label="Maximum RTT/Probe")
    plt.title("Scatter plot of minimum and maximum RTT values to Blizzard IP from %s probes [sorted]" % len(blizzard_max_rtt_df.index))
    plt.xlabel("Number of Probes")
    plt.ylabel("RTT (ms)")
    plt.legend(fontsize=15)
    plt.grid(True)
    plt.show(block=True)
    
    fig, ax = plt.subplots()
    ax.scatter(ubisoft_min_rtt_df['index'],
               ubisoft_min_rtt_df['Min RTT'], c="blue", s=2,
               label="Minimum RTT/Probe")
    ax.scatter(ubisoft_max_rtt_df['index'],
               ubisoft_max_rtt_df['Max RTT'], c="red", s=2,
               label="Maximum RTT/Probe")
    plt.title("Scatter plot of minimum and maximum RTT value to Ubisoft IP from %s probes [sorted]" % len(ubisoft_min_rtt_df.index))
    plt.xlabel("Number of Probes")
    plt.ylabel("RTT (ms)")
    plt.legend(fontsize=15)
    plt.grid(True)
    plt.show(block=True)

    fig, ax = plt.subplots()
    ax.scatter(valve_min_rtt_df['index'],
               valve_min_rtt_df['Min RTT'], c="blue", s=2,
               label="Minimum RTT/Probe")
    ax.scatter(valve_max_rtt_df['index'],
               valve_max_rtt_df['Max RTT'], c="red", s=2,
               label="Maximum RTT/Probe")
    plt.title("Scatter plot of minimum and maxiumum RTT value to Valve IP from %s probes [sorted]" % len(valve_max_rtt_df.index))
    plt.xlabel("Number of Probes")
    plt.ylabel("RTT (ms)")
    plt.legend(fontsize=15)
    plt.grid(True)
    plt.show(block=True)

    # Sort Probes by RTT values
    blizzard_min_rtt = blizzard_min_rtt_df['Min RTT'].tolist()
    blizzard_max_rtt = blizzard_max_rtt_df['Max RTT'].tolist()
    count, bins_count = np.histogram(blizzard_min_rtt, bins=10)
    pdf = count / sum(count)
    cdf = np.cumsum(pdf)
    fig, ax = plt.subplots()
    ax.plot(bins_count[1:], cdf, label="Min RTT Blizzard")
    plt.title("TEST CDF of minimum and maximum RTT values of %s probes to Blizzard server IP address" % len(blizzard_min_rtt))
    plt.xlabel("RTT (ms)")
    plt.ylabel("CDF")
    plt.legend(fontsize=15)
    plt.show(block=True)


    count, bins_count = np.histogram(blizzard_min_rtt, bins=100)
    pdf = count / sum(count)
    cdf = np.cumsum(pdf)
    mcount, mbins_count = np.histogram(blizzard_max_rtt, bins=100)
    mpdf = count / sum(mcount)
    mcdf = np.cumsum(mpdf)
    fig, ax = plt.subplots()
    ax.plot(bins_count[1:], cdf, label="Minimum RTT", color="blue")
    ax.plot(mbins_count[1:], mcdf, label="Maximum RTT", color="red")
    plt.title("CDF of minimum and maximum RTT values of %s probes to Blizzard server IP address" % len(blizzard_min_rtt))
    plt.xlabel("RTT (ms)")
    plt.ylabel("CDF")
    plt.legend(fontsize=15)
    plt.grid(True)
    plt.show(block=True)

    ubisoft_min_rtt = ubisoft_min_rtt_df['Min RTT'].tolist()
    ubisoft_max_rtt = ubisoft_max_rtt_df['Max RTT'].tolist()
    count, bins_count = np.histogram(ubisoft_min_rtt, bins=100)
    pdf = count / sum(count)
    cdf = np.cumsum(pdf)
    mcount, mbins_count = np.histogram(ubisoft_max_rtt, bins=100)
    mpdf = count / sum(mcount)
    mcdf = np.cumsum(mpdf)
    fig, ax = plt.subplots()
    ax.plot(bins_count[1:], cdf, label="Minimum RTT", color="blue")
    ax.plot(mbins_count[1:], mcdf, label="Maximum RTT", color="red")
    plt.title("CDF of minimum and maximum RTT values of %s probes to Ubisoft server IP address" %len(ubisoft_min_rtt))
    plt.xlabel("RTT (ms)")
    plt.ylabel("CDF")
    plt.legend(fontsize=15)
    plt.grid(True)
    plt.show(block=True)

    valve_min_rtt = valve_min_rtt_df['Min RTT'].tolist()
    valve_max_rtt = valve_max_rtt_df['Max RTT'].tolist()
    count, bins_count = np.histogram(valve_min_rtt, bins=100)
    pdf = count / sum(count)
    cdf = np.cumsum(pdf)
    mcount, mbins_count = np.histogram(valve_max_rtt, bins=100)
    mpdf = count / sum(mcount)
    mcdf = np.cumsum(mpdf)
    fig, ax = plt.subplots()
    ax.plot(bins_count[1:], cdf, label="Minimum RTT", color="blue")
    ax.plot(mbins_count[1:], mcdf, label="Maximum RTT", color="red")
    plt.title("CDF of minimum and maximum RTT values of %s probes to Valve server IP address" %len(valve_max_rtt))
    plt.xlabel("RTT (ms)")
    plt.ylabel("CDF")
    plt.legend(fontsize=15)
    plt.grid(True)
    plt.show(block=True)

