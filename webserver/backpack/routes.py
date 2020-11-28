from flask import Blueprint, current_app, render_template, flash, request
import threading
from datetime import datetime
import jsondate as json
import humanize
from contextlib import contextmanager
import support

bp = Blueprint('bp', __name__, static_folder='static')
blueprints = [bp]
data_lock = threading.RLock()

@contextmanager
def Data():
    fname = current_app.config["BASEDIR"] + "/data.json"
    def init_data():
        try:
            return Data.data
        except:
            try:
                return  json.load(file(fname))
            except:
                return {}
    def persist_data(data):
        json.dump(data, file(fname, "w"))
    with data_lock:
        data = init_data()
        Data.data = data
        Data.hash = hash(repr(data))
        yield data
        if hash(repr(data)) == Data.hash:
            return
        persist_data(data)

def status_list(data):
    status = []
    now = datetime.now()
    for (tag, timestamp) in data['success'].items():
        host, job = tag.split(".", 1)
        timedelta = now - timestamp
        expected_interval_days = current_app.config['EXPECTED_TIMEDELTA'].get(tag, 2)
        overdue_factor = timedelta.total_seconds() / (expected_interval_days * 24. * 60 * 60)
        status_code = ("ok" if overdue_factor < 1
                        else "delayed" if overdue_factor < 4
                        else "broken")
        timedelta_human = humanize.naturaltime(timedelta)
        status.append(dict(timestamp=timestamp, tag=tag, host=host, job=job, timedelta_human=timedelta_human, code=status_code, expected_interval_days=expected_interval_days, overdue_factor=overdue_factor))
    return status

def status_by_host(data):
    l = status_list(data)
    status = {}
    for item in l:
        host = item['host']
        if host not in status:
            status[host] = []
        status[host].append(item)
    return status

def now():
    return datetime.now()

@bp.route('/log/success/<label>')
def log_success(label):
    with Data() as data:
        data.setdefault('success',{})[label] = now()
        return "ok"

@bp.route('/log/port/<host>/<int:port>')
def log_port(host, port):
    with Data() as data:
	data.setdefault('port',{})[host] = port
        return "ok"

@bp.route('/log/stats/<host>')
def log_stats(host):
    with Data() as data:
        flash(dir(request.args))
        flash(data)
        data.setdefault('stats',{})[host] = request.args.to_dict()
    return "ok"

@bp.route('/get/port/<host>')
def get_port(host):
    with Data() as data:
        return "%s" % data['port'].get(host, 'n/a')

@bp.route('/')
def index():
    with Data() as data:
        return render_template("index.html", status=status_by_host(data), stats=data['stats'])
