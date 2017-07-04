#!/usr/bin/env python


# todo:
# $HOME/.bup-cron-wrapper/conf contains json dict of jobs
#   [ {name=shannon.bup, skip_cond={...}, command=...}, ... ]
# $HOME/.bup-cron-wrapper/${jobname}.success contains timestamp of last success per job
# loop over jobs:
#     - log
#     - check skip conditions
#     - register at server
#     - run command
#     - register exit status at server
#     - update last_success


import logging, subprocess
from contextlib import contextmanager
from datetime import datetime, timedelta


LOGFILE = "/home/sfoo/.bup-cron-wrapper.log"
DATEFMT = "%Y-%m-%d %H:%M:%S"

def setup_logging(path=LOGFILE):
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler(path, maxBytes=5000, backupCount=5)
    handler.setFormatter(logging.Formatter('%(levelname).1s %(asctime)s: %(message)s', datefmt=DATEFMT))
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.DEBUG)

import os
def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

class SkipExecution(Exception):
    pass

@contextmanager
def logged_call():
    setup_logging()
    try:
        logging.info("start")
        yield
    except SkipExecution as ex:
        logging.warn("skip: %s" % ex)
    except Exception as ex:
        logging.error("fail: %s" % ex)
        raise
    else:
        touch("%s.success" % LOGFILE)
        logging.info("success")



def time_since_last_successful_run():
    from os.path import getmtime
    try:
        seconds_since_epoch = getmtime("%s.success" % LOGFILE)
    except:
        return None
    print seconds_since_epoch
    print datetime.now() - datetime.fromtimestamp(seconds_since_epoch)
    return datetime.now() - datetime.fromtimestamp(seconds_since_epoch)


def is_crashpi1_reachable():
    import socket
    ClientSocket = socket.socket()
    try:
        ClientSocket.connect(("crashpi1", 22))
        return True
    except socket.error:
        return False

def run_backup():
    try:
        subprocess.check_output("/home/sfoo/wip/bup-cron/bup-cron")
    except:
        raise

def check_schedule():
    time_since_last_success = time_since_last_successful_run()
    is_preferred_backup_time = 2 < datetime.now().hour < 7

    if time_since_last_success:
        if time_since_last_success < timedelta(hours=20):
            raise SkipExecution("last backup < 20h ago")
        if not is_preferred_backup_time and (time_since_last_success < timedelta(hours=40)):
            raise SkipExecution("last backup < 40h ago and not preferred backup time")

    if not is_crashpi1_reachable():
        SkipExecution("crashpi1 not reachable")

    # if pid locked and process still active:
        # SkipExecution

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-schedule-check', action='store_true')
    args = parser.parse_args()


    with logged_call():
        if not args.skip_schedule_check:
            check_schedule()
        run_backup()
