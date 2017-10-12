from flask import Flask

import sys
if sys.version_info[0] < 3:
    reload(sys)
sys.setdefaultencoding('utf8')

def create_app(config_object_name='config'):
    app = Flask(__name__)
    app.config.from_object(config_object_name)

    from routes import blueprints
    for bp in blueprints:
        app.register_blueprint(bp)

    return app
