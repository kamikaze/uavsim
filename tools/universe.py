#!/usr/bin/env python3
import os
import subprocess
from multiprocessing import Process


def start_fgfs():
    options = {
        'fg-aircraft': '{}/.fgfs/Aircraft'.format(os.path.expanduser('~')),
        'aircraft': 'SU-37',
        'airport': 'EVRA',
        'callsign': 'kamikaze',
        'timeofday': 'noon',
        'telnet': 'x,x,1000,localhost,5901,x',
        'geometry': '1280x720',
    }
    cmd = ['optirun', 'fgfs', '--enable-real-weather-fetch', '--enable-horizon-effect']
    cmd.extend('--{}={}'.format(k, v) for k, v in options.items())

    subprocess.run(cmd)


def start_sim_adapter():
    options = {
        'telnet-host': '127.0.0.1',
        'telnet-port': 5901
    }
    cmd = ['python', '{}/sim_adapter.py'.format(os.path.dirname(os.path.realpath(__file__)))]
    cmd.extend('--{}={}'.format(k, v) for k, v in options.items())

    subprocess.run(cmd)


def start_uav_adapter():
    options = {'serial': '/dev/ttyACM0'}
    cmd = ['python', '{}/uav_adapter.py'.format(os.path.dirname(os.path.realpath(__file__)))]
    cmd.extend('--{}={}'.format(k, v) for k, v in options.items())

    subprocess.run(cmd)


def stop_crossbar():
    subprocess.run(['crossbar', 'stop'])


def start_crossbar():
    options = {
        'cbdir': '{}/.crossbar'.format(os.path.dirname(os.path.realpath(__file__))),
        'loglevel': 'info',
        'logformat': 'syslogd',
        'logdir': '/tmp',
    }
    cmd = ['crossbar', 'start']

    for k, v in options.items():
        cmd.append('--{}'.format(k))
        cmd.append(v)

    subprocess.run(cmd)


def run_process(fn):
    p = Process(target=fn)
    p.start()

    return p


if __name__ == '__main__':
    functions = [start_crossbar, start_fgfs, start_sim_adapter, start_uav_adapter]

    exit_codes = [p.join() for p in list(map(run_process, functions))]
