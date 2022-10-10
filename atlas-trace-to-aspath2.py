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


import sys
import requests
import argparse
import json
import ipaddress
import _pyipmeta
import csv
import pytricia
from pprint import pprint
from pathlib import Path
from ipwhois.experimental import bulk_lookup_rdap
from ipwhois import IPWhois
from collections import OrderedDict, Counter
from itertools import repeat

caida_prefix2as = "https://publicdata.caida.org/datasets/routing/routeviews-prefix2as/2022/09/routeviews-rv2-20220920-1200.pfx2as.gz"


def getResults(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    mresp = requests.get(url)
    data = mresp.json()
    res_url = data['result']
    res_data = requests.get(res_url)
    results = res_data.json()
    return results


def getProbeInfo(probe_id):
    url = "https://atlas.ripe.net/api/v2/probes/"+str(probe_id)+"/"
    resp = requests.get(url)
    data = resp.json()
    return data


def getMsmTarget(measurement_id):
    base_url = "https://atlas.ripe.net/api/v2/measurements/"
    url = base_url+str(measurement_id)+"/"
    resp = requests.get(url)
    data = resp.json()
    target = data["target_ip"]
    return target


if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Get AS paths from traceroute of valid probes',
            usage='%(prog)s [-t tracemsm -p pingmsm -o output')

    argParser.add_argument('-t', dest='tracemsmfile',
                           help='''File to read traceroute measurments from''',
                           default='/scratch/measurements/traceroute/trace-measurements-for-filtered-probes.json')

    argParser.add_argument('-p', dest='pingmsmfile',
                           help='''List of valid probes to resolve
                                their traceroutes to AS paths''',
                           default='/scratch/probe-list/ping-measurements/valid-probes.json')

    argParser.add_argument('-o', dest='aspaths',
                           help='AS path of valid probes',
                           default='/scratch/measurements/aspath/aspath.json')

    argParser.add_argument('-i', dest='ip2asn',
                           help='IP to ASN mapping of IP address',
                           default='/scratch/measurements/ip2asn/traceip2asn.json')

    argParser.add_argument('-w', dest='writeip2asn',
                           help='Write to ip2asn file',
                           action='store_true',
                           default=False)

    args = argParser.parse_args()
    tracepath = Path(args.tracemsmfile)
    pingpath = Path(args.pingmsmfile)
    ipm = _pyipmeta.IpMeta()
    ipm_prov = ipm.get_provider_by_name("pfx2as")

    if tracepath.is_file() is False:
        print("%s does not exist!!!" % args.tracemsmfile)
        sys.exit(-1)

    if pingpath.is_file() is False:
        print("%s does not exist!!!" % args.pingmsmfile)
        sys.exit(-1)

    with open(args.pingmsmfile, 'r') as pingjson:
        validpingprobes = json.load(pingjson)
        validprobes = []
        for pingmsm, probes in validpingprobes.items():
            validprobes.extend(probes)

    with open(args.tracemsmfile, 'r') as tracejson:
        trace_msms = json.load(tracejson)

    prov_msm_probes = {}
    Valve_prob_msm = {}
    Blizzard_prb_msm = {}
    Ubisoft_prb_msm = {}

    for msm in trace_msms:
        print("Get results for %s" %msm)
        results = getResults(msm)
        target = getMsmTarget(msm)

        if target == "162.254.197.36":

            for result in results:
                if result["prb_id"] in Valve_prob_msm:
                    Valve_prob_msm[result["prb_id"]].append(result)
                else:
                    Valve_prob_msm[result["prb_id"]] = [result]

        if target == "185.60.112.157":
            for result in results:
                if result["prb_id"] in Blizzard_prb_msm:
                    Blizzard_prb_msm[result["prb_id"]].append(result)
                else:
                    Blizzard_prb_msm[result["prb_id"]] = [result]

        if target == "5.200.20.245":

            for result in results:
                if result["prb_id"] in Ubisoft_prb_msm:
                    Ubisoft_prb_msm[result["prb_id"]].append(result)
                else:
                    Ubisoft_prb_msm[result["prb_id"]] = [result]

    prov_msm_probes['Valve'] = []
    prov_msm_probes['Blizzard'] = []
    prov_msm_probes['Ubisoft'] = []

    for prb, prb_msms in Valve_prob_msm.items():
        prov_msm_probes['Valve'].append({prb: prb_msms})

    for prb, prb_msms in Blizzard_prb_msm.items():
        prov_msm_probes['Blizzard'].append({prb: prb_msms})

    for prb, prb_msms in Ubisoft_prb_msm.items():
        prov_msm_probes['Ubisoft'].append({prb: prb_msms})

    for server, prbs in prov_msm_probes.items():
        print("Measurements to %s" % server)
        for prb in prbs:
            for prb_id, msms in prb.items():
                if len(msms) < 2:
                    msm_id = msms[0]['msm_id']
                    print("      Probe %s has one trace result to %s server msm: %s"
                          % (prb_id, server, msm_id))

                if len(msms) > 2:
                    print("      Probe %s has %s trace results to %s server"
                          % (prb_id, len(msms), server))

        print("Total number of probes to %s: %s\n" % (server, len(prbs)))

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

    for server, prbs in prov_msm_probes_u.items():
        # print("Measurements in %s in unique set" % server)
        if len(prbs) != len(prov_msm_probes[server]):
            print("Total number of unique probes to %s: %s\n"
                  % (server, len(prbs)))
            sys.exit(-1)

    prov_msm_probes = prov_msm_probes_u

    IpAddresses = set()
    for server, prbs in prov_msm_probes.items():
        for prb in prbs:
            for prb_id, msms in prb.items():
                for msm in msms:
                    hops = msm['result']
                    for hop in hops:
                        # print("Hop: %s" % hop)
                        try:
                            pkts_per_hop = hop['result']
                        except KeyError:
                            continue

                        for pkt in pkts_per_hop:
                            #print("Packet details: %s" % pkt)
                            try:
                                hop_ip_addr = pkt['from']
                            except KeyError:
                                continue

                            try:
                                hopAddr = ipaddress.ip_address(hop_ip_addr)
                            except ValueError:
                                continue

                            if hopAddr.is_global:
                                IpAddresses.add(hop_ip_addr)

    print("There are %s IP addresses to resolve" % len(IpAddresses))
    ipm.enable_provider(ipm_prov, "-f "+caida_prefix2as)

    ip_to_asn = {}
    for addr in IpAddresses:
        if ipm.lookup(addr):
            (res,) = ipm.lookup(addr)
            if res.get('asns'):
                ip_to_asn[addr] = res.get('asns')[-1]

    resolvedIpHopAddresses = set(ip_to_asn.keys())
    unresolvedIps = IpAddresses.symmetric_difference(resolvedIpHopAddresses)

    print("Unresolved IP addresses")
    pprint(unresolvedIps)
    pyt = pytricia.PyTricia(128)
    with open('/scratch/ip2as.pfx2as', 'r') as f:
        prefix2as_file = csv.reader(f, delimiter=' ')
        for prefix2as in prefix2as_file:
            pyt.insert(prefix2as[0], prefix2as[1])

    
    print("Number of unresolved IP addresses before using prefix2as: %s" % len(unresolvedIps))
    unresolvedIP_list = list(unresolvedIps)
    for ip in unresolvedIP_list:
        asn = pyt.get(ip)
        if asn is not None:
            if asn.isdigit(): 
                ip_to_asn[ip] = int(asn)
                unresolvedIps.remove(ip)

    print("Number of unresolved IP addresses after using prefix2as: %s" % len(unresolvedIps))

    #asn_result, asn_stat = bulk_lookup_rdap(addresses=list(unresolvedIps))

    #for ip, values in asn_result.items():
    #    asn = values["asn"]
    #    if isinstance(asn, str):
    #        try:
    #            int_asn = int(asn)
    #        except ValueError:
    #            continue
    #        ip_to_asn[ip] = int_asn

    #    if isinstance(asn, int):
    #        ip_to_asn[ip] = asn

    if args.writeip2asn:
        with open(args.ip2asn, 'w', encoding='utf-8') as f:
            json.dump(ip_to_asn, f, ensure_ascii=False)
    else:
        with open(args.ip2asn, 'r') as f:
            ip2asnjson = json.load(f)
            ip2asn_ips = set(ip2asnjson.keys())
            add_ips = ip2asn_ips.symmetric_difference(resolvedIpHopAddresses)
            #for ip in add_ips:
            #    ip_to_asn[ip] = ip2asnjson[ip]
            #    try:
            #        unresolvedIps.remove(ip)
            #    except KeyError:
            #        continue
            #pprint(unresolvedIps)
            print("Unresolved IP addresses after  queries: %s"
                  % len(unresolvedIps))
            for ip, asn in ip2asnjson.items():
                if ip not in ip_to_asn:
                    ip_to_asn[ip] = ip2asnjson[ip]

    aspath2prb = {}
    asns = set()

    for server, prbs in prov_msm_probes.items():
        print("Resolving AS paths for trace from probes to %s" % server)
        prb_aspaths = []
        for prb in prbs:
            (prb_id, msms), = prb.items()
            prb_info = getProbeInfo(prb_id)
            prb_asn = prb_info["asn_v4"]
            asns.add(prb_asn)
            aspaths = []
            for msm in msms:
                aspath = []
                aspath.append(prb_asn)
                hops = msm['result']
                for hop in hops:
                    try:
                        pkts_per_hop = hop['result']
                    except KeyError:
                        if hop['hop'] == 1:
                            aspath.append(prb_asn)
                        else:
                            path = 'hop-'+str(hop['hop'])
                            aspath.append(path)
                        continue

                    hop_ip_addrs = set()
                    for pkt in pkts_per_hop:
                        try:
                            hop_ip_addrs.add(pkt['from'])
                        except KeyError:
                            continue

                    for hop_ip_addr in hop_ip_addrs:
                        try:
                            hopAddr = ipaddress.ip_address(hop_ip_addr)
                        except ValueError:
                            path = 'hop-'+str(hop['hop'])
                            aspath.append(path)
                            continue

                        if hop['hop'] == 1:
                            if hopAddr.is_private:
                                aspath.append(prb_asn)
                            else:
                                if hop_ip_addr not in unresolvedIps:
                                    aspath.append(ip_to_asn[hop_ip_addr])
                                    asns.add(ip_to_asn[hop_ip_addr])
                                else:
                                    aspath.append(prb_asn)

                        if hopAddr.is_global:
                            if hop_ip_addr not in unresolvedIps:
                                aspath.append(ip_to_asn[hop_ip_addr])
                                asns.add(ip_to_asn[hop_ip_addr])
                            else:
                                path = 'hop-'+str(hop['hop'])
                                aspath.append(path)
                        else:
                            path = 'hop-'+str(hop['hop'])
                            aspath.append(path)
                aspath_uniq = list(OrderedDict(zip(aspath, repeat(None))))
                aspaths.append(aspath_uniq)
            prb_aspaths.append({prb_id: aspaths})
        aspath2prb[server] = prb_aspaths

    print("There are approximately: %s ASNs extracted from IP addresses in all trace msm"
          % len(asns))

    aspath2prb_valid = {}
    aspath2prb_invalid = {}

    for server, prbs in aspath2prb.items():
        print("%s AS path vetting" % server)
        prb_aspaths_valid = []
        prb_aspaths_invalid = []

        for prb in prbs:
            (prb_id, aspaths), = prb.items()
            valid = []
            invalid = []
            if len(aspaths) < 2:
                i = 0
                for asn in aspaths[0]:
                    if isinstance(asn, int):
                        i += 1

                if i > 3:
                    valid.append(aspaths[0])
                else:
                    invalid.append(aspaths[0])

                if len(invalid) != 0:
                    prb_aspaths_invalid.append({prb_id: invalid})

                if len(valid) != 0:
                    prb_aspaths_valid.append({prb_id: valid})
            else:
                if len(aspaths) > 2:
                    print("Probe %s has %s AS paths resolved to %s"
                          % (prb_id, len(aspaths), server))

                #if Counter(aspaths[0]) != Counter(aspaths[1]):
                #    print("Different AS paths observed for probe %s to %s"
                #          % (prb_id, server))
                #    print("     Path 1: %s" % aspaths[0])
                #    print("     Path 2: %s" % aspaths[1])
                #    print("\n")

                for aspath in aspaths:
                    i = 0
                    for asn in aspath:
                        if isinstance(asn, int):
                            i += 1

                    if i > 3:
                        valid.append(aspath)
                    else:
                        invalid.append(aspath)

                if len(invalid) != 0:
                    prb_aspaths_invalid.append({prb_id: invalid})

                if len(valid) != 0:
                    prb_aspaths_valid.append({prb_id: valid})
        aspath2prb_valid[server] = prb_aspaths_valid
        aspath2prb_invalid[server] = prb_aspaths_invalid

    for server, prbs in aspath2prb_valid.items():
        print("There are %s valid AS paths from probes to %s"
              % (len(prbs), server))
        for prb in prbs[:10]:
            (prb_id, aspaths), = prb.items()
            print("    Probe %s to %s via valid AS paths: %s"
                  % (prb_id, server, aspaths))
        print("\n")

    for server, prbs in aspath2prb_invalid.items():
        print("There are %s invalid AS paths from probes to %s"
              % (len(prbs), server))
        for prb in prbs[:10]:
            (prb_id, aspaths), = prb.items()
            print("    Probe %s to %s AS paths: %s"
                  % (prb_id, server, aspaths))
        print("\n")

    base_path = "/scratch/measurements/aspath"
    allaspaths = base_path+"/aspath-for-trace-msms-to-blizzard-server.json"
    with open(allaspaths, 'w', encoding='utf-8') as f:
        json.dump(aspath2prb, f, ensure_ascii=False, indent=4)

    validaspaths = base_path+"/valid-aspaths-to-blizzard-server.json"
    with open(validaspaths, 'w', encoding='utf-8') as f:
        json.dump(aspath2prb_valid, f, ensure_ascii=False, indent=4)

    invalidaspaths = base_path+"/invalid-aspaths-to-blizzard-server.json"
    with open(invalidaspaths, 'w', encoding='utf-8') as f:
        json.dump(aspath2prb_invalid, f, ensure_ascii=False, indent=4)
