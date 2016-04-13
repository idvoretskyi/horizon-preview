from flask import Flask, request, jsonify, redirect, render_template, session, url_for, flash
from flask_oauthlib.client import OAuth
from flask.ext import assets
from webassets.filter import get_filter
import logging, json, requests
from requests.auth import HTTPBasicAuth
from glob2 import glob
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os, sys, time, base64

# GitHub settings
github = {
    'user': 'mglukhovsky',
    'key': 'cbda7ec5e14870e8196e147e4117e0b9e046d6aa',
    'org': 'rethinkdb',
    'team': 'codesigners',
    # this will be fetched based on the team name upon the first request if not provided
    'team_id': None
}

# Slack settings
slack = {
    'team': 'rethinkdb',
    # channel to track user invites
    'primary_channel': 'horizon',
    'default_channels': ['general', 'random', 'horizon'],
    'token': 'xoxp-11753639537-11747093652-11873098723-58c5ecea1e',
    # these will  be fetched based on default_channels upon the first request if not provided
    #  * should be a dict where the key is the channel name, the value the ID
    'default_channel_ids': None
}

# Gmail settings
email = {
    'from': 'mike@rethinkdb.com',
    'subject': 'Horizon invite',
    'message': ''',thanks for joining the Horizon developer preview!

Horizon is a realtime, open-source backend built on top of RethinkDB. For people building apps with React, Angular, or any other realtime front-end framework, Horizon is a complete, self-hosted and extensible backend with a simple client-side JavaScript API.

We're actively building Horizon -- it's early, but to get started:
  * I've added you to a private GitHub repo for early access (https://github.com/rethinkdb/horizon).
  * Can't see the repo? You can check the status of your invite on GitHub: https://github.com/rethinkdb
  * I've also invited you to #horizon on Slack so you can directly chat with the team and other Horizon users.

We're really excited about Horizon and we think it'll make dramatic impact on app development. If you have ideas to share, let me know (or open an issue on GitHub.)

- Michael

---

Stay tuned for updates: https://horizon.io
Follow on Twitter: @horizonjs
''',
    'message_html':
    '''<html>
    <head></head>
    <body>, thanks for joining the Horizon developer preview!
        <p>
            Horizon is a realtime, open-source backend built on top of
            RethinkDB. For people building apps with React, Angular, or any
            other realtime front-end framework, Horizon is a complete,
            self-hosted and extensible backend with a simple client-side
            JavaScript API.
        </p>
        <p>We're actively building Horizon -- it's early, but to get started:</p>
        <ul>
            <li>
I've added you to a private GitHub repo for early access
(<a href="https://github.com/rethinkdb/horizon">github.com/rethinkdb/horizon</a>s).
            </li>
            <li>
                Can't see the repo? You can
                <a href="https://github.com/rethinkdb">check the status</a> of
                your invite on GitHub.
            </li>
            <li>
                I've also invited you to #horizon on Slack so you can directly
                chat with the team and other Horizon users.
            </li>
        </ul>
        <p>
            We're really excited about Horizon and we think it'll make dramatic
            impact on app development. If you have ideas to share, let me know
            (or open an issue on GitHub.)
        </p>
        <p></p>
        <p>- Michael</p>
        <p>---</p>
        <p>
            Stay tuned for updates: <a href="https://horizon.io">horizon.io</a>.
        </p>
        <p>
            Follow on Twitter: <a href="https://twitter.com/horizonjs">@horizonjs</a>
        </p>
    </body>
</html>'''
}

# Wufoo settings
form = 'horizon-developer-preview'
#key = 'WUFOO_KEY'
#if key not in os.environ:
#    print("Wufoo key not set (%s)" % key)
#    sys.exit(1)
wufoo_key = '0XJN-NFD3-WAHO-03UV'

app = Flask(__name__)
app.debug=True
env = assets.Environment(app)
app.secret_key = '123kwqoidmk23j1oed8suj'
env.config['SASS_USE_SCSS'] = True

# Prepare asset bundles
project_path = os.path.dirname(os.path.abspath(__file__))
env.load_path = [
    os.path.join(project_path, 'js'),
    os.path.join(project_path, 'sass'),
]
env.url_expire = True

env.register(
    'js_all',
    assets.Bundle(
        'app.js',
        filters=get_filter('babel', presets='react'),
        output='gen/packed.js'
    )
)

env.register(
    'css_all',
    assets.Bundle(
        'main.scss',
        filters=get_filter('sass', load_paths=[os.path.join(project_path, 'sass')]),
        depends='**/*.scss',     # Make sure to rebuild whenever *any* SASS file in the load path changes
        output='gen/css_all.css'
    )
)

# Set up logging
@app.before_first_request
def setup_logging():
    if not app.debug:
         # In production mode, log errors to sys.stderr
        app.logger.addHandler(logging.StreamHandler(stream=sys.stdout))
        app.logger.setLevel(logging.INFO)

# Set up OAuth
oauth = OAuth(app)

gmail_auth = oauth.remote_app('gmail',
    # google id
    consumer_key='927426530576-37dk1ckt6b0af1aukqvc9km29hp29u5b.apps.googleusercontent.com',
    # secret
    consumer_secret='wcgUs7UJGUgOM6opsf0Gn1bx',
    request_token_params = {
        # google scope
        'scope': [
            #'https://www.googleapis.com/auth/email',
            #'https://www.googleapis.com/auth/profile',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/gmail.compose'
        ]
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@app.route('/login')
def login_gmail():
    print 'logging in with gmail'
    return gmail_auth.authorize(callback=url_for('authorized_gmail', _external=True))

@app.route('/login/authorized')
def authorized_gmail():
    response = gmail_auth.authorized_response()
    if response is None:
        flash('Gmail login failed: not authorized.')
        return redirect(url_for('index'))
    session['gmail_token'] = (response['access_token'],)
    user = gmail_auth.get('userinfo')
    session['user_email'] = user.data['email']
    return redirect(url_for('index'))

@gmail_auth.tokengetter
def get_gmail_oauth_token():
    return session.get('gmail_token')

# Main views and API calls
@app.route('/')
def index():
    # login with google if no token
    if not 'gmail_token' in session:
        return redirect(url_for('login_gmail'))
    return render_template('app.html')

@app.route('/users')
def users():
    # Basename for our form
    basename = 'https://rethinkdb.wufoo.com/api/v3/forms/%s/' % form
    # Form API key
    auth = HTTPBasicAuth(wufoo_key, 'wufoo')
    # Pagination
    page_size = 100

    # Get the number of entries
    req = requests.get(basename + 'entries/count.json', auth=auth)
    count = json.loads(req.text)['EntryCount']

    # Page through all entries and fetch data
    users = []
    pages = int(count)/page_size
    for i in range(0,pages+1):
        paging = { 'pageSize': page_size, 'pageStart': i*page_size}
        req = requests.get(basename + 'entries.json', params=paging, auth=auth)
        response = json.loads(req.text)
        users += response['Entries']

    users = map(lambda u: {
        'github': u['Field1'],
        'email': u['Field2'],
        'dateCreated': u['DateCreated']
    }, users)
    users = sorted(users, key=lambda k: k['dateCreated'], reverse=True)
    return jsonify({'users': users})

@app.route('/invites/github', methods=['GET', 'POST'])
def invites_github():
    # Basename for our form
    basename = 'https://api.github.com/'
    # Pagination
    page_size = 100
    # GitHub API key
    auth = HTTPBasicAuth(github['user'], github['key'])

    # The first time this request is made, get the team's ID from GitHub
    if github['team_id'] is None:
        req = requests.get(basename + ('orgs/%s/teams' % github['org']), auth=auth)
        response = json.loads(req.text)
        found_team = False
        for team in response:
            if team['name'] == github['team']:
                found_team = True
                github['team_id'] = team['id']
        if not found_team:
            return 'GitHub team not found.'

    # Add a user to the organization
    if request.method == 'POST':
        print request.json
        username = request.json['user']
        req = requests.put(basename + ('teams/%s/memberships/%s' % (github['team_id'], username)), auth=auth)
        print req.text
        if req.status_code is 200:
            return req.text
        else: return 400
    # Get the list of users on the team
    else:
        users = []
        page = 1
        url = basename + ('teams/%s/members' % github['team_id'])
        # Paginate throught the GitHub API and collect team members
        while True:
            print "Pulling page %d of users from %s -- %s" % (page, github['team'], url)
            req = requests.get(url, params={'per_page': page_size}, auth=auth)
            response = json.loads(req.text)
            users += response
            # Break if no link header was returned, or if we're out of pages
            if not req.links or not 'next' in req.links: break
            page += 1
            url = req.links['next']['url']

        return jsonify({'users': map(lambda u: u['login'].lower(), users)})

@app.route('/invites/slack', methods=['GET', 'POST'])
def invites_slack():
    # Basename for our form
    basename = 'https://%s.slack.com/api/' % slack['team']
    # Pagination
    page_size = 100

    if slack['default_channel_ids'] is None:
        slack['default_channel_ids'] = {}
        # Get the list of channels on this team
        req = requests.get(basename + 'channels.list', params = {
            'token': slack['token']
        })
        response = json.loads(req.text)
        # Try to find the IDs of the requested default channels
        for channel in slack['default_channels']:
            try:
                match = next(c for c in response['channels'] if c['name'] == channel)
                slack['default_channel_ids'][channel] = match['id']
            except StopIteration as e:
                print 'Channel not found: %s' % channel

        print "Found default channels: %s" % str(slack['default_channel_ids'])

    # Add a user to the organization
    if request.method == 'POST':
        req = requests.post(basename + 'users.admin.invite',
            params = {'t': int(time.time())},
            data = {
                'email': request.json['user'],
                'channels': ','.join(slack['default_channel_ids'].values()),
                'token': slack['token'],
                'set_active': True,
                '_attempts': 1
            }
        )
        print req.text
        return req.text

    # Get the list of users on the team
    else:
        # Fetch the list of users on the primary channel
        req = requests.get(basename + 'channels.info', params = {
            'channel': slack['default_channel_ids'][slack['primary_channel']],
            'token': slack['token']
        })
        channel = json.loads(req.text)['channel']

        # Get the user details for all users on this team
        req = requests.get(basename + 'users.list', params = {'token': slack['token']})
        users = json.loads(req.text)['members']

        # Match the user IDs to user information
        users_in_channel = []
        for user_id in channel['members']:
            try:
                match = next(u for u in users if u['id'] == user_id)
                users_in_channel.append({
                    'name': match['profile']['real_name'],
                    'email': match['profile']['email']
                })
            except StopIteration as e:
                print 'User not found: %s' % user_id

        return jsonify({'users': users_in_channel})

@app.route('/invites/email', methods=['POST'])
def invites_email():
    msg = MIMEMultipart()
    msg['Subject'] = email['subject']
    msg['From'] = email['from']
    msg['To'] = request.json['user']
    msg.attach(MIMEText(email['message_html'], 'html'))

    url = 'https://www.googleapis.com/gmail/v1/users/mike@rethinkdb.com/drafts'
    data={'message': {'raw': base64.urlsafe_b64encode(msg.as_string())}}
    req = gmail_auth.post(url=url, data=data, format='json')
    print req.data
    if 'error' in req.data and req.data['error']['code'] == 401:
        print('Failed to connect to Google.')
        return redirect(url_for('login_gmail'))
    print req.data
    return jsonify(req.data)

if __name__ == '__main__':
    app.run()
