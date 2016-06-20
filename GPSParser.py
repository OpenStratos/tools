#!/usr/bin/env python3

import argparse
import os
import codecs
import datetime
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, num2date
import numpy as np
import simplekml

def parse_GSA(frame):
    if len(frame) == 18 and (frame[2] == '2' or frame[2] == '3'):
        data = {}
        data['mode'] = '2D' if frame[2] == '2' else '3D'
        data['pdop'] = float(frame[15]) if frame[15] != '' else None
        data['hdop'] = float(frame[16]) if frame[16] != '' else None
        data['vdop'] = float(frame[17][:-3]) if frame[17][:-3] != '' else None

        return data

    elif len(frame) == 18 and frame[2] == '1':
        return False
    else:
        return None

def parse_GGA(frame):
    if len(frame) == 15 and (frame[6] == '1' or frame[6] == '2'):
        data = {}
        data['time'] = datetime.time(int(frame[1][:2]), int(frame[1][2:4]), int(frame[1][4:6]))

        data['latitude'] = int(frame[2][0:2])+float(frame[2][2:])/60
        if frame[3] == 'S':
            data['latitude'] *= -1
        data['longitude'] = int(frame[4][0:3])+float(frame[4][3:])/60
        if frame[5] == 'W':
            data['longitude'] *= -1

        data['quality'] = 'GPS' if frame[6] == '1' else 'DGPS'
        data['satellites'] = int(frame[7])
        data['hdop'] = float(frame[8])
        data['altitude'] = float(frame[9])
        data['geo_height'] = float(frame[11])

        return data

    elif len(frame) == 15 and frame[6] == '0':
        return False
    else:
        return None

def parse_RMC(frame):
    if len(frame) == 13 and frame[2] == 'A':
        data = {}
        data['timestamp'] = datetime.datetime(int(frame[9][4:6])+2000, int(frame[9][2:4]), int(frame[9][:2]),
            int(frame[1][:2]), int(frame[1][2:4]), int(frame[1][4:6]))

        data['latitude'] = int(frame[3][0:2])+float(frame[3][2:])/60
        if frame[4] == 'S':
            data['latitude'] *= -1
        data['longitude'] = int(frame[5][0:3])+float(frame[5][3:])/60
        if frame[6] == 'W':
            data['longitude'] *= -1

        data['speed'] = float(frame[7])*463/900
        data['course'] = float(frame[8])
        data['mag_var'] = float(frame[10]) if frame[10] != '' else None
        if frame[11] == 'W':
            data['mag_var'] *= -1

        return data

    elif len(frame) == 13 and frame[2] == 'V':
        return False
    else:
        return None

def parse_raw(file_path):
    initialized = False
    frame_count = 0
    satellites = {'time': [], 'sat': []}
    position = []
    altitude = {'time': [], 'alt': []}
    pdop = {'time': [], 'pdop': []}
    hdop = {'time': [], 'hdop': []}
    vdop = {'time': [], 'vdop': []}
    h_speed = {'time': [], 'speed': []}
    v_speed = {'time': [], 'speed': []}
    fix = {'time': [], 'fix': []}

    last_altitude = 0
    last_v_timestamp = 0
    with codecs.open(file_path, 'r', 'iso-8859-1') as raw_file:
        for line in raw_file:
            if not initialized:
                initialized = True
                continue

            frame_data = line.split()
            if (len(frame_data) < 2):
                continue

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

            if not sent:
                if 'GSA' in frame[0]:
                    try:
                        parsed_frame = parse_GSA(frame)
                    except ValueError:
                        continue

                    if parsed_frame is not None:
                        frame_count += 1
                        if parsed_frame is False:
                            fix['time'].append(timestamp)
                            fix['fix'].append(False)
                        else:
                            fix['time'].append(timestamp)
                            fix['fix'].append(True)

                            if parsed_frame['pdop'] is not None:
                                pdop['time'].append(timestamp)
                                pdop['pdop'].append(parsed_frame['pdop'])

                            if parsed_frame['hdop'] is not None:
                                hdop['time'].append(timestamp)
                                hdop['hdop'].append(parsed_frame['hdop'])

                            if parsed_frame['vdop'] is not None:
                                vdop['time'].append(timestamp)
                                vdop['vdop'].append(parsed_frame['vdop'])
                elif 'GGA' in frame[0]:
                    try:
                        parsed_frame = parse_GGA(frame)
                    except ValueError:
                        continue
                    if parsed_frame is not None:
                        frame_count += 1
                        if parsed_frame is False:
                            fix['time'].append(timestamp)
                            fix['fix'].append(False)
                        else:
                            fix['time'].append(timestamp)
                            fix['fix'].append(True)

                            satellites['time'].append(timestamp)
                            satellites['sat'].append(parsed_frame['satellites'])

                            if last_altitude != 0:
                                position.append((parsed_frame['longitude'], parsed_frame['latitude'], last_altitude))

                            altitude['time'].append(timestamp)
                            altitude['alt'].append(parsed_frame['altitude'])

                            if (last_altitude != 0):
                                v_speed['time'].append(timestamp)
                                v_speed['speed'].append((parsed_frame['altitude']-last_altitude)/
                                    (timestamp-last_v_timestamp).total_seconds())
                            last_altitude = parsed_frame['altitude']
                            last_v_timestamp = timestamp
                elif 'RMC' in frame[0]:
                    try:
                        parsed_frame = parse_RMC(frame)
                    except ValueError:
                        continue
                    if parsed_frame is not None:
                        frame_count += 1
                        if parsed_frame is False:
                            fix['time'].append(timestamp)
                            fix['fix'].append(False)
                        else:
                            fix['time'].append(timestamp)
                            fix['fix'].append(True)

                            if last_altitude != 0:
                                position.append((parsed_frame['longitude'], parsed_frame['latitude'], last_altitude))

                            h_speed['time'].append(timestamp)
                            h_speed['speed'].append(parsed_frame['speed'])

    matplotlib.rcParams.update({'font.size': 50})
    fig, ax1 = plt.subplots()
    fig.suptitle('Satellites and precision', fontsize=70)
    fig.set_figheight(30)
    fig.set_figwidth(max(len(satellites['time'])/50, 100))
    satellite_line = ax1.plot(satellites['time'], satellites['sat'], 'k-', linewidth=8.0, label='Satellites')
    ax1.set_xlabel('Time', fontsize=70)
    ax1.set_ylabel('Satellites', fontsize=70)
    ax1.set_ylim((0, max(satellites['sat'])+2))

    ax2 = ax1.twinx()
    pdop_line = ax2.plot(pdop['time'], pdop['pdop'], 'r-', linewidth=5.0, label='PDOP')
    hdop_line = ax2.plot(pdop['time'], hdop['hdop'], 'g-', linewidth=5.0, label='HDOP')
    vdop_line = ax2.plot(pdop['time'], vdop['vdop'], 'b-', linewidth=5.0, label='VDOP')
    ax2.set_ylabel('DOP', fontsize=70)
    ax2.set_ylim((0, max(max(pdop['pdop']), max(hdop['hdop']), max(vdop['vdop']))+2))

    lines = satellite_line + pdop_line + hdop_line + vdop_line
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels)

    # plt.xticks(np.arange(min(satellites['time']), max(satellites['time']), datetime.timedelta(seconds=600)))

    plt.savefig('satellites_precision.svg')

    plt.figure(figsize=(max(len(altitude['time'])/40, 100), max(max(altitude['alt'])*1.1/250, 100)))
    plt.title('Altitude above sea level', fontsize=200)
    plt.xlabel('Time', fontsize=150)
    plt.ylabel('Altitude (m)', fontsize=150)
    plt.plot(altitude['time'], altitude['alt'], 'k-', linewidth=10.0)
    plt.ylim((0, max(altitude['alt'])*1.1))

    plt.savefig('altitude.svg')

    matplotlib.rcParams.update({'font.size': 25})
    plt.figure(figsize=(max(len(h_speed['time'])/150, 75), max(max(h_speed['speed'])*1.1/20, 20)))
    plt.title('Horizontal speed', fontsize=100)
    plt.xlabel('Time', fontsize=75)
    plt.ylabel('Speed (m/s)', fontsize=75)
    plt.plot(h_speed['time'], h_speed['speed'], 'k-')
    plt.ylim((0, max(h_speed['speed'])*1.1))

    plt.savefig('h_speed.svg')

    matplotlib.rcParams.update({'font.size': 75})
    plt.figure(figsize=(max(len(v_speed['time'])/40, 75),
        max(max(v_speed['speed'])*1.1/5 + abs(min(v_speed['speed']))*1.1/5, 20)))
    plt.title('Vertical speed', fontsize=100)
    plt.xlabel('Time', fontsize=75)
    plt.ylabel('Speed (m/s)', fontsize=75)
    plt.plot(v_speed['time'], v_speed['speed'], 'k-')
    plt.ylim(min(v_speed['speed'])*1.1, max(v_speed['speed'])*1.1)

    plt.savefig('v_speed.svg')

    matplotlib.rcParams.update({'font.size': 75})
    plt.figure(figsize=(max(len(fix['time'])/40, 75), 20))
    plt.title('Fix', fontsize=100)
    plt.xlabel('Time', fontsize=75)
    plt.ylabel('Fix', fontsize=75)
    plt.plot(fix['time'], fix['fix'], 'k-')

    plt.savefig('fix.svg')

    kml = simplekml.Kml()
    ls = kml.newlinestring(name="Flight Path", description="Flight path for OpenStratos.", coords=position)
    ls.extrude = 1
    ls.tessellate = 1
    ls.altitudemode = simplekml.AltitudeMode.absolute
    ls.style.linestyle.width = 4
    ls.style.linestyle.color = "7f00ffff"
    ls.polystyle.color = "7f00ff00"
    kml.save("OpenStratos.kml")

    print("Total frames: %d" % frame_count)
    print("Max. altitude: %f m" % max(altitude['alt']))
    print("Max. horizontal speed: %f m/s" % max(h_speed['speed']))
    print("Max. vertical speed: %f m/s" % max(v_speed['speed']))

parser = argparse.ArgumentParser(description='Process OpenStratos GPS data')
parser.add_argument('file', metavar='FILE', type=str, nargs=1,
                   help='the file containing GPS data')

args = parser.parse_args()
path = os.path.join(os.path.dirname(__file__), args.file[0])
parse_raw(path)
