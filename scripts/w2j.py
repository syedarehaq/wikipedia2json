#!/usr/bin/env python3
from wiki2json import Wiki2Json
import fileinput

w2j = Wiki2Json()
for line in fileinput.input():
    w2j.parse_line(line)

## mishuk edit for debugging
# from wiki2json import Wiki2Json
# import fileinput
# w2j = Wiki2Json()
# with open("./filter-01_even_smaller.xml") as f:
# 	for line in f:
# 		w2j.parse_line(line)