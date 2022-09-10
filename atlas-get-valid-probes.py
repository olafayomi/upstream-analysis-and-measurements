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
from pathlib import Path
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
            description='Get valid probes from ping measurements',
            usage='%(prog)s [-p pingmsmfile]')

    argParser.add_argument('-p', dest='pingmsmfile',
                           help='''File where ping measurement ids
                                are written''',
                           type=str,
                           default='/scratch/measurements/ping/ping.json')

    argParser.add_argument('-o', dest='validpingprobes',
                           help='''File to write valid ping probes''',
                           type=str,
                           default='/scratch/probe-list/ping-measurements/valid-probes.json')

    argParser.add_argument('-e', dest='invalidmsms',
                           help='''Invalid/empty measurements list''',
                           type=str,
                           default='/scratch/measurements/invalid-msms.json')

    argParser.add_argument('-l', dest='min_rtt',
                           help='Minimum RTT to filter probes to consider',
                           type=float, default=40)

    argParser.add_argument('-u', dest='max_rtt',
                           help='Maximum RTT to filter probes to conider',
                           type=float, default=100)

    args = argParser.parse_args()
    path = Path(args.pingmsmfile)
    invalidpath = Path(args.invalidmsms)

    if path.is_file() is False:
        print("%s does not exist!!!" % args.pingmsmfile)
        sys.exit(-1)

    if invalidpath.is_file() is False:
        print("%s does not exist!!!" % args.invalidmsms)

    with open(args.invalidmsms, 'r') as invalids:
        invalidmsms = json.load(invalids)

    with open(args.pingmsmfile, 'r') as pingjson:
        ping_msms = json.load(pingjson)

    msm_probes = {}

    for msm in ping_msms:

        if msm in invalidmsms:
            continue

        results = getResults(msm)
        msm_by_prb = {}

        for res in results:
            if res['prb_id'] in msm_by_prb:
                msm_by_prb[res['prb_id']].append(res)
            else:
                msm_by_prb[res['prb_id']] = [res]

        for prb_id, msms in msm_by_prb.items():
            avg_rtt = []
            for rmsm in msms:
                if rmsm['avg'] > 0:
                    avg_rtt.append(rmsm['avg'])

            if len(avg_rtt) < 1:
                continue

            if np.mean(avg_rtt) > args.max_rtt:
                continue

            if np.mean(avg_rtt) < args.min_rtt:
                continue

            avg_avg = np.mean(avg_rtt)
            if (avg_avg > args.min_rtt) and (avg_avg < args.max_rtt):
                if msm not in msm_probes:
                    # print("Probe %s to be included in: %s\n" % (prb_id, msm))
                    msm_probes[msm] = [prb_id]
                else:
                    msm_probes[msm].append(prb_id)

    prov_msm_probe = {}
    for msm, probes in msm_probes.items():
        results = getResults(msm)
        result = results[0]
        if result["dst_addr"] == "162.254.197.36":
            if 'Valve' not in prov_msm_probe:
                prov_msm_probe['Valve'] = [{msm : probes}]
            else:
                prov_msm_probe['Valve'].append({msm : probes})

        if result["dst_addr"] == "185.60.112.157":
            if 'Blizzard' not in prov_msm_probe:
                prov_msm_probe['Blizzard'] = [{msm : probes}]
            else:
                prov_msm_probe['Blizzard'].append({msm : probes})

        if result["dst_addr"] == "5.200.20.245":
            if 'Ubisoft' not in prov_msm_probe:
                prov_msm_probe['Ubisoft'] = [{msm : probes}]
            else:
                prov_msm_probe['Ubisoft'].append({msm : probes})


    # msm_and_probes = { k:v for k,v in msm_probes.items() if v }

    with open(args.validpingprobes, 'w', encoding='utf-8') as f:
        json.dump(prov_msm_probe, f, ensure_ascii=False)
