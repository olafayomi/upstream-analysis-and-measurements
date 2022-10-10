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
import argparse
import json
from pathlib import Path

if __name__ == "__main__":

    argParser = argparse.ArgumentParser(
            description='Rewrite JSON files in readable format',
            usage='%(prog)s [-i inputfile -o outputfile')

    argParser.add_argument('-i', dest='inputfile',
                           help='''Input JSON file''',
                           default='/scratch/measurements/aspath/aspath.json')

    argParser.add_argument('-o', dest='outputfile',
                           help='''Output JSON file''',
                           default='/scratch/measurements/aspath/read-aspath.json')

    args = argParser.parse_args()
    inputf = Path(args.inputfile)

    if inputf.is_file() is False:
        print("%s does not exist!!!" % args.inputfile)
        sys.exit(-1)

    with open(args.inputfile, 'r') as inputjson:
        ijson = json.load(inputjson) 

    with open(args.outputfile, 'w', encoding='utf-8') as f:
        json.dump(ijson, f, ensure_ascii=False, indent=2)
        
