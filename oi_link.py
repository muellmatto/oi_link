#!/usr/bin/env python3

from configparser import ConfigParser
from os.path import realpath, dirname, join
from functools import wraps
from random import choices
from string import ascii_letters
from sys import exit

from flask import Flask, request, redirect, render_template_string, session, url_for


OI_LINK = Flask(__name__)

oi_links = {}

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
    OI_LINK.secret_key = oi_link_config['OI_LINK']['SECRET']
except:
    print('please check configfile: ', oi_link_config_path)
    exit(1)


# -----------------------------------------------------
# oi_link functions
# -----------------------------------------------------

def generate_link():
    global oi_links
    link = "".join(choices(ascii_letters, k=3))
    while link in oi_links:
        link = "".join(choices(ascii_letters, k=3))
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
        print(oi_submit)
        global oi_links
        oi_link = generate_link()
        oi_links[oi_link] = oi_submit
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
                    <textarea style="width: 100%;" name="oi_link_content" form="oi_form">text or link here</textarea>
                </form>
                <a href="/logout">logout</a>
            </body>
        </html>
    '''


@OI_LINK.route('/<oi_link>')
def unpack_oi_link(oi_link):
    try:
        global oi_links
        oi_link = oi_links[oi_link]
        print(oi_link)
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
                                readonly>
                            {{ oi_link_content|escape }}
                        </textarea>
                    </body>
                </html>
                '''
            return render_template_string(template, oi_link_content=oi_link_content)
    except:
        return redirect('/')


if __name__ == '__main__':
    OI_LINK.run(debug=True, port=oi_link_port)
