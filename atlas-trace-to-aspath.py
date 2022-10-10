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
from pprint import pprint
from pathlib import Path
from ipwhois.experimental import bulk_lookup_rdap
from ipwhois import IPWhois
from collections import OrderedDict
from itertools import repeat

caida_prefix2as = "https://publicdata.caida.org/datasets/routing/routeviews-prefix2as/2022/09/routeviews-rv2-20220917-1200.pfx2as.gz"
                       

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
                           default='/scratch/measurements/traceroute/trace.json')

    argParser.add_argument('-p', dest='pingmsmfile',
                           help='''List of valid probes to resolve
                                their traceroutes to AS paths''',
                           default='/scratch/probe-list/ping-measurements/valid-probes.json')

    argParser.add_argument('-o', dest='aspaths',
                           help='AS path of valid probes',
                           default='/scratch/measurements/aspath/aspath.json')

    argParser.add_argument('-i', dest='ip2asn',
                           help='IP to ASN mapping of IP address',
                           default='/scratch/measurements/ip2asn/ip2asn.json')

    argParser.add_argument('-r', dest='readip2asn',
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

    
    validtraceresults = []
    prov_msm_probes = {}

    for msm in trace_msms:
        results = getResults(msm) 
        target = getMsmTarget(msm)

        if target == "162.254.197.36":

            if 'Valve' not provider_probes_trace:
                prov_msm_probes['Valve'] = []
            prbs_by_msm = {} 
            


    for msm in trace_msms:
        results = getResults(msm)
        for res in results:
            if res['prb_id'] in validprobes:
                validtraceresults.append(res)

    # pprint(validtraceresults)
    ipHopAddresses = set()
    # Get all valid IP addresses from trace
    for trace in validtraceresults:
        hops = trace['result']
        for hop in hops:
            try:
                hop_ip_addr = hop['result'][0]['from']
            except KeyError:
                continue

            try:
                hopAddr = ipaddress.ip_address(hop_ip_addr)
            except ValueError:
                continue

            if hopAddr.is_global:
                ipHopAddresses.add(hop_ip_addr)

    # pprint(ipHopAddresses)
    print("There are %s IP addresses to resolve" % len(ipHopAddresses))
    ipm.enable_provider(ipm_prov, "-f "+caida_prefix2as)

    ip_to_asn = {}
    for addr in ipHopAddresses:
        if ipm.lookup(addr):
            (res,) = ipm.lookup(addr)
            if res.get('asns'):
                # print("IP: %s ASN: %s" % (addr, res.get('asns')[-1]))
                ip_to_asn[addr] = res.get('asns')[-1]
            # pprint(res)

    resolvedIpHopAddresses = set(ip_to_asn.keys())
    unresolvedIps = ipHopAddresses.symmetric_difference(resolvedIpHopAddresses)
    # pprint(unresolvedIps)

    if args.readip2asn:
        with open(args.ip2asn, 'w', encoding='utf-8') as f:
            json.dump(ip_to_asn, f, ensure_ascii=False)
    else:
        # reconcile
        with open(args.ip2asn, 'r') as f:
            ip2asnjson = json.load(f)
            ip2asn_ips = set(ip2asnjson.keys())
            add_ips = ip2asn_ips.symmetric_difference(resolvedIpHopAddresses)
            for ip in add_ips:
                ip_to_asn[ip] = ip2asnjson[ip]
                try:
                    unresolvedIps.remove(ip)
                except KeyError:
                    continue
            pprint(unresolvedIps)

    if ipm.lookup(validtraceresults[0]['dst_addr']):
        (res,) = ipm.lookup(validtraceresults[0]['dst_addr'])
        if res.get('asns'):
            dstAsn = res.get('asns')[-1]
    else:
        whoisQ = IPWhois(validtraceresults[0]['dst_addr'])
        result = whoisQ.lookup_rdap(depth=1)
        dstAsn = result["asn"]

    aspath2prb = {}

    print("Number of valid traces: %s" % len(validtraceresults))
    for trace in validtraceresults:
        hops = trace['result']
        prb_info = getProbeInfo(trace['prb_id'])
        prb_asn = prb_info["asn_v4"]
        aspath = []
        aspath.append(prb_asn)
        for hop in hops:
            try:
                hop_addr = hop['result'][0]['from']
            except KeyError:
                path = 'hop-'+str(hop['hop'])
                aspath.append(path)
                continue

            try:
                hopAddr = ipaddress.ip_address(hop_addr)
            except ValueError:
                path = 'hop-'+str(hop['hop'])
                aspath.append(path)
                continue

            if hop['hop'] == 1:
                if hopAddr.is_private:
                    aspath.append(prb_asn)
                else:
                    if hop_addr not in unresolvedIps:
                        aspath.append(ip_to_asn[hop_addr])
                    else:
                        aspath.append(prb_asn)

            if hopAddr.is_global:
                if hop_addr not in unresolvedIps:
                    aspath.append(ip_to_asn[hop_addr])
                else:
                    path = 'hop-'+str(hop['hop'])
                    aspath.append(path)

            else:
                path = 'hop-'+str(hop['hop'])
                aspath.append(path)
        aspath_uniq = list(OrderedDict(zip(aspath, repeat(None))))
        aspath2prb[trace['prb_id']] = aspath_uniq
        print("Completed resolving for trace number: %s" % validtraceresults.index(trace))

    # unresolvedprobepaths = {}
    # resolvedaspath = {}
    unviableprobes = {}
    viableprobes = {}
    for prb_id, aspath in aspath2prb.items():
        i = 0
        for asn in aspath:
            if isinstance(asn, int):
                i += 1

        if i > 3:
            viableprobes[prb_id] = aspath
        else:
            unviableprobes[prb_id] = aspath

    # unresolvedprbs = set(unresolvedprobepaths.keys())
    # allprbs = set(aspath2prb.keys())
    # resolvedprbs = allprbs.symmetric_difference(unresolvedprbs)
    # for prb_id, aspath in aspath2prb.items():
    #    if prb_id in resolvedprbs:
    #        resolvedaspath[prb_id] = aspath

    # pprint(unviableprobes)
    pprint(viableprobes)
    print("Number of unviableprobes: %s, Number of viableprobes: %s" % (len(unviableprobes), len(viableprobes)))
    print("Total of aspath2prb: %s" % (len(aspath2prb)))

    if len(viableprobes) != 0:
        with open(args.aspaths, 'w', encoding='utf-8') as f:
            json.dump(viableprobes, f, ensure_ascii=False)

    # asn_result, asn_stat = bulk_lookup_rdap(addresses=list(ipHopAddresses))
    # ip_to_asn = {}

    # for ip, values in asn_result.items():
    #    asn = values["asn"]
    #    if asn.is_digit():
    #        ip_to_asn[ip] = int(asn)

    # resolvedIpHopAddresses = set(ip_to_asn.keys())
    # unresolvedIps = ipHopAddresses.symmetric_difference(resolvedIpHopAddresses)
