#!/usr/bin/env python

import os
BACKPACK_DOTDIR = os.path.join(os.path.expanduser('~'), ".backpack")
LOGFILE = os.path.join(BACKPACK_DOTDIR, "backpack.log")
DATEFMT = "%Y-%m-%d %H:%M:%S"
SUCCESS_URL = 'https://mado.phoenix.uberspace.de/backpack/log/success/%s'


import logging, subprocess, json, urllib2
from contextlib import contextmanager
from datetime import datetime, timedelta


def setup_logging(path=LOGFILE):
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler(path, maxBytes=5000, backupCount=5)
    handler.setFormatter(logging.Formatter('%(levelname).1s %(asctime)s: %(message)s', datefmt=DATEFMT))
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.DEBUG)


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

class SkipExecution(Exception):
    pass


@contextmanager
def logged_call(jobname):
    try:
        logging.info("%s start" % jobname)
        yield
        touch(success_timestamp_file(jobname))
        logging.info("%s success" % jobname)
        try:
            urllib2.urlopen(SUCCESS_URL % jobname, timeout=10)
        except:
            pass
    except SkipExecution as ex:
        logging.warn("%s skip: %s" % (jobname, ex))
    except Exception as ex:
        logging.error("%s fail: %s" % (jobname, ex))
        raise


def success_timestamp_file(jobname):
    return os.path.join(BACKPACK_DOTDIR, "success.%s" % jobname)

def time_since_last_successful_run(jobname):
    from os.path import getmtime
    try:
        seconds_since_epoch = getmtime(success_timestamp_file(jobname))
    except:
        return None
    return datetime.now() - datetime.fromtimestamp(seconds_since_epoch)


def run_command(command):
    subprocess.check_output(command)

def check_condition(jobname, condition):
    time_since_last_success = time_since_last_successful_run(jobname)

    def ping(hostname):
        import socket
        ClientSocket = socket.socket()
        try:
            ClientSocket.connect((hostname, 22))
        except socket.error:
            raise SkipExecution("Could not ping host %r" % hostname)

    def not_since(duration, time_unit):
        if time_since_last_success is None:
            # could not determine last success -> not recently successful
            return
        if time_since_last_success < timedelta(**{time_unit: duration}):
            raise SkipExecution("Backup less than %i %s ago" % (duration, time_unit))


    def hour_is_between(start, end):
        "can also wrap around midnight, e.g. start=22, end=4"
        now = datetime.now()
        in_daytime_interval = start <= now.hour < end
        in_interval_before_midnight =  end < start <= now.hour
        in_interval_after_midnight = now.hour < end < start
        if not any([in_daytime_interval, in_interval_before_midnight,
                   in_interval_after_midnight]):
            raise SkipExecution("Time is not between %i:00 and %i:00" % (start, end))

    def check_any(*conditions):
        log = []
        for c in conditions:
            try:
                check_condition(jobname, c)
                return
            except SkipExecution as ex:
                log.append(str(ex))
        raise SkipExecution("All failed: %r" % log)

    def check_all(*conditions):
        for c in conditions:
            check_condition(jobname, c)

    cmd, args = condition[0], condition[1:]
    print cmd, args
    function = {
        "and": check_all,
        "or": check_any,
        "ping": ping,
        "hour_is_between": hour_is_between,
        "not_since": not_since,
    }[cmd]

    function(*args)

if __name__ == "__main__":
    setup_logging()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-condition-check', action='store_true')
    parser.add_argument('--config-file', default=os.path.join(BACKPACK_DOTDIR, "conf.json"))
    args = parser.parse_args()

    jobs = json.load(file(args.config_file))

    for job in jobs:
        with logged_call(job['name']):
            if not args.skip_condition_check:
                check_condition(job['name'], job.get('condition', ["and"]))
            run_command(job['command'])
