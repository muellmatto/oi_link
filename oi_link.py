#!/usr/bin/env python3.6

from configparser import ConfigParser
from functools import wraps
from json import dumps as to_json, loads as from_json
from os.path import realpath, dirname, join
from random import choices
from string import ascii_letters, ascii_lowercase
from sys import exit

from flask import abort, Flask, request, redirect, render_template_string, session, url_for
from redis import Redis

OI_LINK = Flask(__name__)


# -----------------------------------------------------
# read config 
# -----------------------------------------------------

try:
    oi_link_config = ConfigParser()
    oi_link_path = dirname(realpath(__file__))
    oi_link_config_path = join(oi_link_path, 'oi_link.conf')
    oi_link_config.read(oi_link_config_path)
    username = oi_link_config['OI_LINK']['user']
    password = oi_link_config['OI_LINK']['password']
    oi_link_port = int(oi_link_config['OI_LINK']['port'])
    oi_link_expire_seconds = int(oi_link_config['OI_LINK']['expire_seconds'])
    OI_LINK.secret_key = oi_link_config['OI_LINK']['secret']
    redis_db_number = int(oi_link_config['REDIS']['database'])
    if oi_link_config['REDIS']['unixsocket'].upper() == 'TRUE':
        socket_path = oi_link_config['REDIS']['SOCKETFILE']
    else:
        socket_path = None
        from redis import Redis
    oi_links = Redis(charset="utf-8", decode_responses=True ,db=redis_db_number, unix_socket_path=socket_path)
    oi_links.get(None) # Test connection
except Exception as e:
    print(e)
    print('please check configfile: ', oi_link_config_path)
    exit(1)


# -----------------------------------------------------
# oi_link functions
# -----------------------------------------------------

def generate_link():
    global oi_links
    # link = "".join(choices(ascii_letters, k=3))
    link = "".join(choices(ascii_lowercase, k=2))
    while link in oi_links:
        # link = "".join(choices(ascii_letters, k=3))
        link = "".join(choices(ascii_lowercase, k=2))
    oi_links[link] = None
    return link


def oi_link_session(wrapped):
    @wraps(wrapped)
    def oi_link_request(*args, **kwargs):
        if 'username' in session:
            return wrapped(*args, **kwargs)
        else:
            return 'You are not logged in <br><a href="' + url_for('login') + '">login</a>'
    return oi_link_request


# -----------------------------------------------------
# flask routes
# -----------------------------------------------------

@OI_LINK.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == username and request.form['password'] == password:
            session.permanent = True
            session['username'] = username
        return redirect(url_for('home'))
    return '''
        <!DOCTYPE html>
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body>
                <form action="" method="post">
                    <p><input type=text name=username>
                    <p><input type=password name=password>
                    <p><input type=submit value=Login>
                </form>
            </body>
        </html>
    '''


@OI_LINK.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))


@OI_LINK.route('/', methods = ['POST', 'GET'])
@oi_link_session
def home():
    if request.method == 'POST': 
        oi_submit = dict(request.form)
        global oi_links
        oi_link = generate_link()
        oi_links[oi_link] = to_json(oi_submit)
        if oi_link_expire_seconds > 0:
            oi_links.expire(name=oi_link, time=oi_link_expire_seconds)
        if oi_submit['oi_link_type'][0] == 'short_link':
            return '''
                <!DOCTYPE html>
                <html>
                    <body><a href="''' + request.url_root + oi_link + '">' + request.url_root + oi_link + '''</a>
                    </body>
                </html>
            '''
        return redirect(oi_link)
    return '''
        <!DOCTYPE html>
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body>
                <form action="" method="post" id="oi_form">
                    <p><input type=submit value=LINK></p>
                    <p><input type=radio name=oi_link_type value=paste_link checked>PASTE LINK</p>
                    <p><input type=radio name=oi_link_type value=short_link>SHORT LINK</p>
                    <textarea style="width: 100%; height: calc(100vh - 10rem); min-height: 15rem;" name="oi_link_content" form="oi_form">text or link here</textarea>
                </form>
                <a href="/logout">logout</a>
            </body>
        </html>
    '''


@OI_LINK.route('/<oi_link>')
def unpack_oi_link(oi_link):
    try:
        global oi_links
        oi_link = from_json(oi_links[oi_link])
        oi_link_type = oi_link['oi_link_type'][0]
        oi_link_content = oi_link['oi_link_content'][0]
        if oi_link_type == 'short_link':
            if oi_link_content.startswith('https://') or oi_link_content.startswith('http://'):
                return redirect(oi_link_content)
            else:
                return redirect('http://' + oi_link_content)
        else:
            template = '''
                <!DOCTYPE html>
                <html>
                    <head>
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    </head>
                    <body>
                        <textarea style="
                                width: 100%;
                                height: calc(100vh - 3rem);
                                "
                                readonly>{{ oi_link_content|escape }}</textarea>
                    </body>
                </html>
                '''
            return render_template_string(template, oi_link_content=oi_link_content)
    except:
        return abort(404)


if __name__ == '__main__':
    OI_LINK.run(debug=True, port=oi_link_port)
