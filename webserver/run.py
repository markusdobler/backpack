#!/usr/bin/env python


from backpack import create_app
app = create_app('config')

@app.before_request
def flash_testing_warning():
    from flask import flash, request
    if request.endpoint != "static":
        flash("{}: {}".format(request.url, request.form), "info")

app.run(debug=True, host="0.0.0.0", port=5001)
