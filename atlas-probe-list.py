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
import ipaddress
import csv
from pprint import pprint

BASE_PROBE_URL = "https://atlas.ripe.net/api/v2/probes/?country_code="
PROBE_PARAMS = "&status=1"


def getProbes(isocode):
    url = BASE_PROBE_URL+str(isocode)+PROBE_PARAMS
    resp = requests.get(url)
    data = resp.json()

    if 'count' in data:
        probes = data['results']
        while data['next'] is not None:
            url = data['next']
            resp = requests.get(url)
            data = resp.json()
            probes.extend(data['results'])

        return probes
    else:
        return None


if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Get list of probes by country',
            usage='%(prog)s [-c country_code]')

    argParser.add_argument('-c', dest='country_code',
                           help='ISO country code', type=str,
                           default=None)

    argParser.add_argument('-i', dest='eu_countries_csv',
                           help='CSV file of EU countries',
                           default='/scratch/eu_member_states.csv')

    argParser.add_argument('-o', dest='probelistname',
                           help='Filename of probe list to write',
                           type=str, default=None)

    args = argParser.parse_args()

    if args.country_code is not None:

        assert args.probelistname is not None

        probes = getProbes(args.country_code)

        if probes is None:
            print("No probes found for %s" % args.country_code)
            sys.exit(0)

        probe_id = []
        for probe in probes:
            probe_id.append(str(probe['id']))

        print("Number of probes in country: %s" % len(probe_id))\

        if len(probe_id) > 300:
            n = 300
            for i in range(0, len(probe_id)+1, n):
                probe_list_out = ",".join(probe_id[i:i+n])
                filename = args.probelistname+'-'+str(i+1)
                with open(filename, "w") as text:
                    text.write(probe_list_out)
        else:
            probe_list_out = ",".join(probe_id)
            filename = args.probelistname
            with open(args.probelistname, "w") as text:
                text.write(probe_list_out)
    else:
        with open(args.eu_countries_csv, 'r') as iso_eu_csv:
            eu_countries = csv.reader(iso_eu_csv)
            for country in eu_countries:
                country_probes = getProbes(country[3])

                if country_probes is None:
                    print("No probes found for %s" % country[1])
                    continue

                probe_id = []
                for probe in country_probes:
                    probe_id.append(str(probe['id']))

                if len(probe_id) > 300:
                    n = 300
                    for i in range(0, len(probe_id)+1, n):
                        probe_list_out = ",".join(probe_id[i:i+n])
                        filename = '/scratch/probe-list/'+country[1]+'-probes-'+str(i+1)
                        with open(filename, "w") as text:
                            text.write(probe_list_out)
                else:
                    probe_list_out = ",".join(probe_id)
                    filename = '/scratch/probe-list/'+country[1]+'-probes'
                    with open(filename, "w") as text:
                        text.write(probe_list_out)
