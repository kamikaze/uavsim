#!/usr/bin/env python3
import os
import subprocess
import sys
from multiprocessing import Process

from pkg_resources import resource_filename


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)

    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def start_fgfs():
    options = {
        'fg-aircraft': '{}/.fgfs/Aircraft'.format(os.path.expanduser('~')),
        'aircraft': 'SU-37',
        'airport': 'EVRA',
        'callsign': 'kamikaze',
        'timeofday': 'noon',
        'telnet': 'x,x,1000,localhost,5901,x',
        'geometry': '1280x720',
        'generic': 'socket,out,10000,,5500,udp,uav_out',
        # 'generic': 'socket,in,10000,,5501,udp,uav_in',
    }
    cmd = ['fgfs', '--enable-real-weather-fetch', '--enable-horizon-effect']

    if which('optirun'):
        cmd.insert(0, 'optirun')

    cmd.extend('--{}={}'.format(k, v) for k, v in options.items())

    subprocess.run(cmd)


def start_sim_adapter():
    options = {
        'telnet-host': '127.0.0.1',
        'telnet-port': 5901,
    }
    cmd = [sys.executable, '-m', 'uavsim.sim_adapter']
    cmd.extend('--{}={}'.format(k, v) for k, v in options.items())

    subprocess.run(cmd)


def start_uav_adapter():
    options = {'serial': '/dev/ttyACM0'}
    cmd = [sys.executable, '-m', 'uavsim.uav_adapter']
    cmd.extend('--{}={}'.format(k, v) for k, v in options.items())

    subprocess.run(cmd)


def start_statistics_adapter():
    options = {'output-dir': '/tmp'}
    cmd = [sys.executable, '-m', 'uavsim.statistics_adapter']
    cmd.extend('--{}={}'.format(k, v) for k, v in options.items())

    subprocess.run(cmd)


def start_map():
    cmd = [sys.executable, '-m', 'uavsim.map']
    subprocess.run(cmd)


def stop_crossbar():
    subprocess.run(['crossbar', 'stop'])


def start_crossbar():
    options = {
        'cbdir': resource_filename('uavsim.resources', 'crossbar'),
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
    # functions = (start_crossbar, start_fgfs, start_sim_adapter, start_uav_adapter, start_statistics_adapter, start_map,)
    functions = (start_crossbar, start_fgfs, start_sim_adapter, start_uav_adapter, start_statistics_adapter,)

    exit_codes = [p.join() for p in list(map(run_process, functions))]
