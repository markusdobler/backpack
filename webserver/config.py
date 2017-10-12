import os

# grabs the folder where the script runs
basedir = os.path.abspath(os.path.dirname(__file__))
BASEDIR = basedir

SECRET_KEY = file(os.path.join(basedir,'secret-key.txt')).read().strip()

EXPECTED_TIMEDELTA = {
    'crashpi1.par2protect': 9,
}
