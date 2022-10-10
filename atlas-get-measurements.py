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


def getMyMeasurementIDs(key):
    BASE_URL = "https://atlas.ripe.net/api/v2/measurements/my/?key="
    url = BASE_URL+str(key)
    resp = requests.get(url)
    data = resp.json()

    if 'count' in data:
        count = data['count']
        msms = data['results']
        while data['next'] is not None:
            url = data['next']
            resp = requests.get(url)
            data = resp.json()
            msms.extend(data['results'])
        if count != len(msms):
            print("Measurement count: %s, Measurement collected: %s"
                  % (count, len(msms)))
        return msms
    else:
        print("No measurement available for key!!!")
        return None


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
            description='Get list of measurements using API key',
            usage='%(prog)s [-k key]')

    argParser.add_argument('-k', dest='key',
                           help='Country code in lower case', type=str,
                           default='xxxxxx-xxxxxx-xxxxxxxx-xxxxxxxxxx')

    argParser.add_argument('-p', dest='pingmsmfile',
                           help='''File where ping measurement ids
                                    are written to''',
                           default='/scratch/measurements/ping/ping.json')

    argParser.add_argument('-t', dest='tracemsmfile',
                           help='File for savig traceroute msm ids',
                           default=
                           '/scratch/measurements/traceroute/trace.json')

    argParser.add_argument('-s', dest='step',
                           help='Get ping measurements by step',
                           type=int)

    argParser.add_argument('-d', dest='dest_addr',
                           help='Get measurements by destination addr',
                           type=str)

    args = argParser.parse_args()

    msms = getMyMeasurementIDs(args.key)

    ping = []
    trace = []

    for msm in msms:
        if msm['type'] == 'ping':
            ping.append(msm['id'])

        if msm['type'] == 'traceroute':
            trace.append(msm['id'])

    if (args.step is None) or (args.dest_addr is None):
        if len(ping) != 0:
            with open(args.pingmsmfile, 'w', encoding='utf-8') as f:
                json.dump(ping, f, ensure_ascii=False, indent=4)

        if len(trace) != 0:
            with open(args.tracemsmfile, 'w', encoding='utf-8') as f:
                json.dump(trace, f, ensure_ascii=False, indent=4)

    if args.step:
        sorted_ping_msms = []
        for msm in msms:
            if msm['type'] == 'ping':

                results = getResults(msm['id'])
                if len(results) == 0:
                    continue

                result = results[0]
                if (result['step'] == args.step) or (result['step'] == (args.step - 1)):
                    sorted_ping_msms.append(msm['id'])

        if len(sorted_ping_msms) != 0:
            with open(args.pingmsmfile, 'w', encoding='utf-8') as f:
                json.dump(sorted_ping_msms, f, ensure_ascii=False, indent=4)
