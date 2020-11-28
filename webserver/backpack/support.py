from flask_mail import Mail, Message
from threading import Thread
from flask import current_app

mail = Mail()
def send_mail(subject, body, recipients=None, cc=None, sender=None):
    if cc is None:
        cc = current_app.config.get('MAIL_DEFAULT_CC',())
    msg = Message(subject, sender=sender, recipients=recipients, cc=cc)
    msg.body = body

    if current_app.config.get('MAIL_SUPPRESS_SEND'):
        current_app.logger.info("\n    ".join(("Skip sending message:\n"+msg.as_string()).split("\n")))
        return
    try:
        mail.send(msg)
    except:
        current_app.logger.error("failed to send message")
        current_app.logger.error(msg)
        raise

