#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Usage:
#
# cat translator/DictionaryEst.gf | replace-with-d.py -l estonian/DictEstAbs.gf
#

import sys
import re
import argparse
from collections import *

def read_lexicon(fn):
    h = {}
    with open(fn, 'r') as f:
        for raw_line in f:
            line = raw_line.strip()
            if ' : ' in line:
                val = re.sub(r' :.*', '', line)
                h[val] = val
                # We make another key by removing underscores
                # ... does not change anything
                #h[re.sub(r'_', '', val)] = val
    return h


def modify_line(h, line):
    m = re.match(r'(lin .* = )mk(.*) "(.*)" ;', line)
    if m:
        entry = re.sub(r' ', '_', m.group(3)) + '_' + m.group(2)
        if entry in h:
            return m.group(1) + 'D.' + entry + ' ;'
        if "'" + entry + "'" in h:
            return m.group(1) + 'D.\'' + entry + '\' ;'
    return line

def get_args():
    p = argparse.ArgumentParser(description='Replaces 1-arg opers with lexicon entries')
    p.add_argument('-l', '--lexicon', type=str, action='store', required=True)
    p.add_argument('-v', '--version', action='version', version='%(prog)s v0.0.1')
    return p.parse_args()

def main():
    args = get_args()
    h = read_lexicon(args.lexicon)
    for raw_line in sys.stdin:
        line = raw_line.strip()
        print(modify_line(h, line))

if __name__ == "__main__":
    main()
