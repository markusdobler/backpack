import os

# grabs the folder where the script runs
basedir = os.path.abspath(os.path.dirname(__file__))
BASEDIR = basedir

SECRET_KEY = file(os.path.join(basedir,'secret-key.txt')).read().strip()

#MAIL_SUPPRESS_SEND = True
MAIL_DEFAULT_RECIPIENTS = ['backpack@markusdobler.de']
MAIL_SERVER = "phoenix.uberspace.de"
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = "mado-backpack@phoenix.uberspace.de"
MAIL_PASSWORD = "ZEsq8UCATBk9u59u"
MAIL_DEFAULT_SENDER = ("Backpack Bot", "mado-backpack@phoenix.uberspace.de")

EXPECTED_TIMEDELTA = {
    'crashpi1.par2protect': 9,
}
