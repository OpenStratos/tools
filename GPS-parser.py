#!/usr/bin/env python3

import argparse
import os
import codecs
import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import date2num, num2date
import numpy as np
import simplekml

def parse_GSA(frame):
    if frame[1] != '1':
        data = {}
        data['mode'] = '2D' if frame[2] == '2' else '3D'
        data['pdop'] = float(frame[15]) if frame[15] != '' else None
        data['hdop'] = float(frame[16]) if frame[16] != '' else None
        data['vdop'] = float(frame[17][:-3]) if frame[17][:-3] != '' else None

        return data

    return None

def parse_GGA(frame):
    if frame[6] != '0':
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

    return None

def parse_RMC(frame):
    if frame[2] == 'A':
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

    last_altitude = 0
    last_v_timestamp = 0
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

            if not sent:
                if frame[0] == '$GPGSA':
                    parsed_frame = parse_GSA(frame)
                    if parsed_frame is not None:
                        frame_count += 1

                        if parsed_frame['pdop'] is not None:
                            pdop['time'].append(timestamp)
                            pdop['pdop'].append(parsed_frame['pdop'])

                        if parsed_frame['hdop'] is not None:
                            hdop['time'].append(timestamp)
                            hdop['hdop'].append(parsed_frame['hdop'])

                        if parsed_frame['vdop'] is not None:
                            vdop['time'].append(timestamp)
                            vdop['vdop'].append(parsed_frame['vdop'])
                elif frame[0] == '$GPGGA':
                    parsed_frame = parse_GGA(frame)
                    if parsed_frame is not None:
                        frame_count += 1

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
                elif frame[0] == '$GPRMC':
                    parsed_frame = parse_RMC(frame)
                    if parsed_frame is not None:
                        frame_count += 1

                        if last_altitude != 0:
                            position.append((parsed_frame['longitude'], parsed_frame['latitude'], last_altitude))

                        h_speed['time'].append(timestamp)
                        h_speed['speed'].append(parsed_frame['speed'])

    fig, ax1 = plt.subplots()
    fig.suptitle('Satellites and precision', fontsize=20)
    fig.set_figheight(8)
    fig.set_figwidth(len(satellites['time'])/30)
    satellite_line = ax1.plot(satellites['time'], satellites['sat'], 'k-', label='Satellites')
    ax1.set_xlabel('Time', fontsize=15)
    ax1.set_ylabel('Satellites', fontsize=15)
    ax1.set_ylim((0, max(satellites['sat'])+2))

    ax2 = ax1.twinx()
    pdop_line = ax2.plot(pdop['time'], pdop['pdop'], 'r-', label='PDOP')
    hdop_line = ax2.plot(pdop['time'], hdop['hdop'], 'g-', label='HDOP')
    vdop_line = ax2.plot(pdop['time'], vdop['vdop'], 'b-', label='VDOP')
    ax2.set_ylabel('DOP', fontsize=15)
    ax2.set_ylim((0, max(max(pdop['pdop']), max(hdop['hdop']), max(vdop['vdop']))+2))

    lines = satellite_line + pdop_line + hdop_line + vdop_line
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels)

    # plt.xticks(np.arange(min(satellites['time']), max(satellites['time']), datetime.timedelta(seconds=60)))

    plt.savefig('satellites_precision.svg')

    plt.figure(figsize=(len(altitude['time'])/40, max(altitude['alt'])*1.1/5))
    plt.title('Altitude above sea level', fontsize=20)
    plt.xlabel('Time', fontsize=15)
    plt.ylabel('Altitude (m)', fontsize=15)
    plt.plot(altitude['time'], altitude['alt'], 'k-')
    plt.ylim((0, max(altitude['alt'])*1.1))

    plt.savefig('altitude.svg')

    plt.figure(figsize=(len(h_speed['time'])/40, max(max(h_speed['speed'])*1.1/5, 5)))
    plt.title('Horizontal speed', fontsize=20)
    plt.xlabel('Time', fontsize=15)
    plt.ylabel('Speed (m/s)', fontsize=15)
    plt.plot(h_speed['time'], h_speed['speed'], 'k-')
    plt.ylim((0, max(h_speed['speed'])*1.1))

    plt.savefig('h_speed.svg')

    plt.figure(figsize=(len(v_speed['time'])/40,
        max(max(v_speed['speed'])*1.1/5 + abs(min(v_speed['speed']))*1.1/5, 5)))
    plt.title('Vertical speed', fontsize=20)
    plt.xlabel('Time', fontsize=15)
    plt.ylabel('Speed (m/s)', fontsize=15)
    plt.plot(v_speed['time'], v_speed['speed'], 'k-')
    plt.ylim(min(v_speed['speed'])*1.1, max(v_speed['speed'])*1.1)

    plt.savefig('v_speed.svg')

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
