#!/usr/bin/env python3

import argparse
import os
import codecs
import datetime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, num2date

ram = {'time': [], 'ram': []}

def parse_raw(file_path):
    initialized = False
    with codecs.open(file_path, 'r', 'iso-8859-1') as temp_file:
        for line in temp_file:
            if not initialized:
                initialized = True
                continue
            data = line.split()

            date = data[2].split('/')
            time = data[3].split(':')
            time[2] = time[2].split('.')
            timestamp = datetime.datetime(int(date[2]), int(date[0]), int(date[1]),
                int(time[0]), int(time[1]), int(time[2][0]), int(time[2][1]))

            ram["time"].append(timestamp)
            ram["ram"].append(float(data[5])*100)

    matplotlib.rcParams.update({'font.size': 100})
    plt.figure(figsize=(max(len(ram['time'])/2, 200), 110))
    plt.title('RAM consumption', fontsize=200)
    plt.xlabel('Time', fontsize=150)
    plt.ylabel('RAM consumption (%)', fontsize=150)
    plt.plot(ram['time'], ram['ram'], 'k-', linewidth=10.0)
    plt.ylim((0, 110))

    plt.savefig('ram.svg')

parser = argparse.ArgumentParser(description='Process OpenStratos RAM consumption data')
parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                   help='the file containing RAM consumption data')

args = parser.parse_args()
path = os.path.join(os.path.dirname(__file__), args.file[0])
parse_raw(path)
