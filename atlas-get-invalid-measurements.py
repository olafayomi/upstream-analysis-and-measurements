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
            description='Get list of empty or invalid measurements',
            usage='%(prog)s [-p pingmsmfile -o invalid-ping-msms.json]')

    argParser.add_argument('-p', dest='pingmsmfile',
                           help='''File where all ping measurement ids
                                are written''',
                           type=str,
                           default='/scratch/measurements/ping/ping.json')

    argParser.add_argument('-o', dest='invalidmsms',
                           help='''File to write invalid/empty msm ids''',
                           type=str,
                           default='/scratch/measurements/invalid-msms.json')

    args = argParser.parse_args()
    path = Path(args.pingmsmfile)

    if path.is_file() is False:
        print("%s does not exist!!!" % args.pingmsmfile)
        sys.exit(-1)

    with open(args.pingmsmfile, 'r') as msmjson:
        msms = json.load(msmjson)

    invalid_msms = []
    for msm in msms:
        results = getResults(msm)

        if len(results) == 0:
            print("Measurement %s is invalid" % msm)
            invalid_msms.append(msm)

    with open(args.invalidmsms, 'w', encoding='utf-8') as f:
        json.dump(invalid_msms, f, ensure_ascii=False)
