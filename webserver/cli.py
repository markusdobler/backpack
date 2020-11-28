#!/usr/bin/env python

import click
from backpack import create_app, support, routes
from flask import render_template
import humanize
from itertools import groupby

app = create_app('config')

@app.cli.command()
@click.option('--to', '-t', multiple=True)
def mail(to):
    "Send a status email"
    recipients = list(to) or app.config['MAIL_DEFAULT_RECIPIENTS']
    with routes.Data() as data:
        pass
    status = routes.status_list(data)
    status.sort(key=lambda d: d['timestamp'])
    
    subject = "Backpack status: " + ", ".join("%ix %s" % (len(list(g)), k) for k, g in groupby(d['code'] for d in status) )
    body = render_template("mail.txt", status=status)
    #print recipients, repr(subject)
    #print body
    #return
    support.send_mail(subject, body, recipients)
