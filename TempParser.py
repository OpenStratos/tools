#!/usr/bin/env python3

import argparse
import os
import codecs
import datetime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, num2date

cpu = {'time': [], 'temp': []}
gpu = {'time': [], 'temp': []}

def parse_raw(file_path):
    with codecs.open(file_path, 'r', 'iso-8859-1') as temp_file:
        for line in temp_file:
            data = line.split()
            if (len(data) < 9):
                continue

            date = data[2].split('/')
            time = data[3].split(':')
            time[2] = time[2].split('.')
            timestamp = datetime.datetime(int(date[2]), int(date[0]), int(date[1]),
                int(time[0]), int(time[1]), int(time[2][0]), int(time[2][1]))

            cpu["time"].append(timestamp)
            cpu["temp"].append(float(data[6]))

            gpu["time"].append(timestamp)
            gpu["temp"].append(float(data[8]))

    matplotlib.rcParams.update({'font.size': 100})
    plt.figure(figsize=(len(cpu['time'])/2, 110))
    plt.title('Temperature', fontsize=200)
    plt.xlabel('Time', fontsize=150)
    plt.ylabel('Temperature (°C)', fontsize=150)
    plt.plot(cpu['time'], cpu['temp'], 'g-', linewidth=10.0)
    plt.plot(gpu['time'], gpu['temp'], 'b-', linewidth=10.0)
    plt.ylim((0, 110))

    plt.savefig('temperature.svg')

parser = argparse.ArgumentParser(description='Process OpenStratos temperature data')
parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                   help='the file containing temperature data')

args = parser.parse_args()
path = os.path.join(os.path.dirname(__file__), args.file[0])
parse_raw(path)
