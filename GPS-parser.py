#!/usr/bin/env python3

import argparse
import os
import codecs
import datetime

# TODO check checksums

def parse_GSA(frame):
    return {'time': None}

def parse_GGA(frame):
    if frame[6] != '0':
        data = {}
        data['time'] = datetime.time(int(frame[1][0:2]), int(frame[1][2:4]), int(frame[1][4:6]))

        data['latitude'] = int(frame[2][0:2])+float(frame[2][2:])/60 if frame[2] is not '' else None
        if frame[3] == 'S':
            data['latitude'] *= -1
        data['longitude'] = int(frame[4][0:3])+float(frame[4][3:])/60 if frame[4] is not '' else None
        if frame[5] == 'W':
            data['longitude'] *= -1

        data['quality'] = 'GPS' if frame[6] == '1' else 'DGPS'
        data['satellites'] = int(frame[7])

        return data

    return None

def parse_RMC(frame):
    return {'time': None}

def parse_raw(file_path):
    initialized = False
    frame_count = 0
    with codecs.open(file_path, 'r', 'iso-8859-1') as raw_file:
        for line in raw_file:
            if not initialized:
                initialized = True
                continue

            frame_data = line.split()

            date = frame_data[2].split('/')
            time = frame_data[3].split(':')
            time[2] = time[2].split('.')
            timestamp = datetime.datetime(int(date[2]), int(date[0]), int(date[1]),
                int(time[0]), int(time[1]), int(time[2][0]), int(time[2][1]))

            frame = frame_data[5].split(',')
            if frame == "Sent:":
                frame = frame_data[6]
                sent = True
            else:
                sent = False

            print("Timestamp: "+timestamp.isoformat())

            if not sent:
                if frame[0] == '$GPGSA':
                    parsed_frame = parse_GSA(frame)
                    if parsed_frame is not None:
                        frame_count += 1
                elif frame[0] == '$GPGGA':
                    parsed_frame = parse_GGA(frame)
                    if parsed_frame is not None:
                        frame_count += 1
                        print(frame)
                        print(parsed_frame['satellites'])
                elif frame[0] == '$GPRMC':
                    parsed_frame = parse_RMC(frame)
                    if parsed_frame is not None:
                        frame_count += 1

    print("Total frames: %d" % frame_count)


parser = argparse.ArgumentParser(description='Process OpenStratos GPS data')
parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                   help='the file containing GPS data')
parser.add_argument('--raw', dest='raw', action='store_true', help='provide the raw GPS frames')

args = parser.parse_args()

if args.raw:
    path = os.path.join(os.path.dirname(__file__), args.file[0])
    parse_raw(path)
else:
    path = os.path.join(os.path.dirname(__file__), args.file[0])
    parse(path)
