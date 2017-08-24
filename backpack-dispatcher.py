#!/usr/bin/env python

import os
BACKPACK_DOTDIR = os.path.join(os.path.expanduser('~'), ".backpack")
LOGFILE = os.path.join(BACKPACK_DOTDIR, "log", "backpack.log")
DATEFMT = "%Y-%m-%d %H:%M:%S"
SUCCESS_URL = 'https://mado.phoenix.uberspace.de/backpack/log/success/%s'


import logging, subprocess, json, urllib2
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from trbs_pid import PidFile, PidFileError


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

class SkipExecution(Exception):
    pass


def success_timestamp_file(jobname):
    return os.path.join(BACKPACK_DOTDIR, "status", "success.%s" % jobname)

def time_since_last_successful_run(jobname):
    from os.path import getmtime
    try:
        seconds_since_epoch = getmtime(success_timestamp_file(jobname))
    except:
        return None
    return datetime.now() - datetime.fromtimestamp(seconds_since_epoch)


def check_ping(hostname):
    import socket
    ClientSocket = socket.socket()
    try:
        ClientSocket.connect((hostname, 22))
    except socket.error:
        raise SkipExecution("Could not ping host %r" % hostname)

def check_hour_is_between(start, end):
    "can also wrap around midnight, e.g. start=22, end=4"
    now = datetime.now()
    in_daytime_interval = start <= now.hour < end
    in_interval_before_midnight =  end < start <= now.hour
    in_interval_after_midnight = now.hour < end < start
    if not any([in_daytime_interval, in_interval_before_midnight,
               in_interval_after_midnight]):
        raise SkipExecution("Time is not between %i:00 and %i:00" % (start, end))

def check_not_since(time_since_success, duration, time_unit):
    if time_since_success is None:
        # could not determine last success -> not recently successful
        return
    if time_since_success < timedelta(**{time_unit: duration}):
        raise SkipExecution("Backup less than %i %s ago" % (duration, time_unit))


class Job(object):
    def __init__(self, name, command, condition=('and',())):
        self.name = name
        self.command = command
        self.condition = condition
        self.time_since_last_success = time_since_last_successful_run(self.name)

    def check_condition(self):
        try:
            PidFile(self.name).check()
        except PidFileError:
            raise SkipExecution("Job already running.")
        self._check_condition(self.condition)

    def _check_condition(self, condition):
        def check_any(*conditions):
            log = []
            for c in conditions:
                try:
                    self._check_condition(c)
                    return
                except SkipExecution as ex:
                    log.append(str(ex))
            raise SkipExecution("All failed: %r" % log)

        cmd, args = condition[0], condition[1:]
        function = {
            "and": lambda *conditions: [self._check_condition(c) for c in conditions],
            "or": check_any,
            "ping": check_ping,
            "hour_is_between": check_hour_is_between,
            "not_since": lambda d, t: check_not_since(self.time_since_last_success, d, t),
        }[cmd]
        function(*args)

    def run_command(self):
        with PidFile(self.name) as pid:
            subprocess.check_output(self.command)

    def __enter__(self, path=LOGFILE):
        self.logger = logging.getLogger(self.name)
        handler = RotatingFileHandler(path, maxBytes=5000, backupCount=5)
        format_string = '%(levelname).1s %(asctime)s: ' + self.name.replace('%','%%') + ' %(message)s'
        handler.setFormatter(logging.Formatter(format_string, datefmt=DATEFMT))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)
        self.logger.info("start")
        return self

    def __exit__(self, ex_type, ex, traceback):
        if ex is None:
            touch(success_timestamp_file(self.name))
            self.logger.info("success")
            urllib2.urlopen(SUCCESS_URL % self.name, timeout=10)
        elif isinstance(ex, SkipExecution):
            self.logger.warn("skip: %s" % ex)
        else:
            self.logger.error("fail: %s" % ex)
        return True # do not throw exception again -> only gets logged, further jobs in loop get processed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-condition-check', action='store_true')
    parser.add_argument('--config-file', default=os.path.join(BACKPACK_DOTDIR, "conf", "conf.json"))
    args = parser.parse_args()

    jobs = json.load(file(args.config_file))

    for job_config in jobs:
        with Job(**job_config) as job:
            if not args.skip_condition_check:
                job.check_condition()
            job.run_command()
