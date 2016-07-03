#!/usr/bin/env python3

import argparse
import os
import codecs
import datetime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, num2date

gsm = {'time': [], 'bat': []}
main = {'time': [], 'bat': []}

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

            if "GSM" in data[5]:
                gsm["time"].append(timestamp)
                gsm["bat"].append(float(data[6])*100)
            elif "Main" in data[5]:
                bat = float(data[6])
                if bat < -1:
                    bat = 0
                main["time"].append(timestamp)
                main["bat"].append(float(data[6])*100)

    matplotlib.rcParams.update({'font.size': 100})
    plt.figure(figsize=(max(len(gsm['time'])/2, 200), 110))
    plt.title('Battery consumption', fontsize=200)
    plt.xlabel('Time', fontsize=150)
    plt.ylabel('Battery (%)', fontsize=150)
    plt.plot(gsm['time'], gsm['bat'], 'g-', linewidth=10.0)
    plt.plot(main['time'], main['bat'], 'b-', linewidth=10.0)
    plt.ylim((0, 110))

    plt.savefig('battery.svg')

parser = argparse.ArgumentParser(description='Process OpenStratos battery data')
parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                   help='the file containing battery data')

args = parser.parse_args()
path = os.path.join(os.path.dirname(__file__), args.file[0])
parse_raw(path)
