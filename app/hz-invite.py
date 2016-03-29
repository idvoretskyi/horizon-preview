from flask import Flask, request, jsonify, redirect
import logging, json, requests
from requests.auth import HTTPBasicAuth
import os, sys

app = Flask(__name__)

form = 'horizon-developer-preview'
key = 'WUFOO_KEY'
if key not in os.environ:
    print("Wufoo key not set (%s)" % key)
    sys.exit(1)

@app.before_first_request
def setup_logging():
    if not app.debug:
         # In production mode, log errors to sys.stderr
        app.logger.addHandler(logging.StreamHandler(stream=sys.stdout))
        app.logger.setLevel(logging.INFO)

@app.route("/invite", methods=['POST'])
def horizon():
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        'Field1': request.form['github'],
        'Field2': request.form['email']
    }
    auth = HTTPBasicAuth(os.environ[key], 'wufoo')
    req = requests.post('https://rethinkdb.wufoo.com/api/v3/forms/%s/entries.json' % form, data=data, auth=auth)
    if req.status_code is 201:
        return redirect('/thanks')
    if req.status_code is 200:
        response = json.loads(req.text)
        if response['Success'] is 0:
            app.logger.error("Data: %s\nResponse: %s" %(data,response))
            return redirect('/error')
    app.logger.error("Data: %s\nResponse: %s" %(data,req.text))
    return redirect('/error')

if __name__ == '__main__':
    app.run()
