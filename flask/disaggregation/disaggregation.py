# -*- coding: utf-8 -*-
"""
    disaggregation: showing the data
    ~~~~~~~~

    A micro application written with Flask and sqlite3.

    :copyright: © 2010 by the disaggregation team.
    :license: Open Source, see LICENSE for more details.
"""

import time
from sqlite3 import dbapi2 as sqlite3
from hashlib import md5
from datetime import datetime
from flask import Flask, request, jsonify, session, url_for, redirect, \
     render_template, abort, g, flash, _app_ctx_stack     
from werkzeug import check_password_hash, generate_password_hash

# on activation of the webserver, check for internet and send the local ip to the server for easy redirect on your phone.
try:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    
    import requests
    r=requests.get('https://beacon.makethemetersmarter.com?ip='+ip)
    print("Beacon updated https://beacon.makethemetersmarter.com?ip="+ip)
except:
    print("Beacon not updated")

# configuration
DATABASE = '../../../data/disaggregation.db'
PER_PAGE = 100
DEBUG = True
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'

# create our little application :)
app = Flask('Disaggregation')
app.config.from_object(__name__)
app.config.from_envvar('disaggregation_SETTINGS', silent=True)


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sqlite3.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sqlite3.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def init_db():
    """Initializes the database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def query_db(query, args=(), one=False):
    """Queries the database and returns a list of dictionaries."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def get_user_id(username):
    """Convenience method to look up the id for a username."""
    rv = query_db('select user_id from user where username = ?',
                  [username], one=True)
    return rv[0] if rv else None

def get_device_id(devicename):
    """Convenience method to look up the id for a username."""
    rv = query_db('select device_id from devices where name = ?',
                  [devicename], one=True)
    return rv[0] if rv else None


def format_datetime(timestamp):
    """Format a timestamp for display."""
    return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d @ %H:%M')


def gravatar_url(email, size=80):
    """Return the gravatar image for the given email address."""
    return 'https://www.gravatar.com/avatar/%s?d=identicon&s=%d' % \
        (md5(email.strip().lower().encode('utf-8')).hexdigest(), size)


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = query_db('select * from user where user_id = ?',
                          [session['user_id']], one=True)


@app.route('/')
def timeline():
    """Shows a users timeline or if no user is logged in it will
    redirect to the public device list.  This timeline shows the user's
    device list as well as all the messages of followed users.
    """
    if not g.user:
        return redirect(url_for('public_timeline'))
    return render_template('live_data.html', messages=query_db('''
        select message.*, user.* from message, user
        where message.author_id = user.user_id and (
            user.user_id = ? or
            user.user_id in (select whom_id from follower
                                    where who_id = ?))
        order by message.pub_date desc limit ?''',
        [session['user_id'], session['user_id'], PER_PAGE]))


@app.route('/public')
def public_timeline():
    """Displays the latest messages of all users."""
    return render_template('timeline.html', 
        messages=query_db('''select message.*, user.* from message, user
        where message.author_id = user.user_id order by message.pub_date desc limit ?''', [PER_PAGE]),
        devices=query_db('''select *,count(*) as 'num',avg(power),
sum((strftime(\'%s\', first_datetime)-strftime(\'%s\', last_datetime))) as 'seconds',
round(sum((strftime(\'%s\', first_datetime)-strftime(\'%s\', last_datetime)))/3600*power/1000,2)  as 'kWh',
min(first_datetime) as 'first_datetime',max(first_datetime) as 'last_start', max(last_datetime) as 'last_datetime' FROM devices GROUP BY name ORDER BY last_datetime limit ?''', [PER_PAGE]),
        device_types=query_db('''select * from device_types limit ?''', [PER_PAGE]),
        loads=reversed(query_db('''select * from loads order by date desc limit ?''', [1000]))
        )
@app.route('/devices')
def show_devices():
    """Displays the devices of all users."""
    return render_template('devices.html', messages=query_db('''
        select devices.*, user.* from devices, user
        where devices.author_id = user.user_id
        order by devices.last_seen_datetime desc limit ?''', [PER_PAGE]))

@app.route('/load_live_data')
def load_live_data():
    """load live data from the db"""
    loadsonly = query_db('''select * from loads order by date desc limit 1080''') # 1080 = 3600 sec * 3 hours / 1 log per 10 sec = 3hours
    loads = []
    production = []
    timestamps = []
    for load in loadsonly:
        timestamps.append(load['date'])
        try:
            loads.append(load['demand_power_L1']+load['demand_power_L2']+load['demand_power_L3'])
            production.append(load['supply_power_L1']+load['supply_power_L2']+load['supply_power_L3'])
        except:
            loads.append(load['demand_power'])
            production.append(load['supply_power'])

    power = loads[0]
    # app.logger.debug(loadsonly.keys())
    # return power
    return jsonify(result=power,timestamps=list(reversed(timestamps)),data=list(reversed(loads)),production=list(reversed(production)))

@app.route('/load_disaggregated_data')
def load_disaggregated_data():
    """load disaggregated data from the db"""
    devices=query_db('''select *,count(*) as 'num',avg(power),
    sum((strftime(\'%s\', first_datetime)-strftime(\'%s\', last_datetime))) as 'seconds',
    round(sum((strftime(\'%s\', first_datetime)-strftime(\'%s\', last_datetime)))/3600*power/1000,2)  as 'kWh',
    first_datetime,last_datetime from devices group by name order by kWh desc limit 100''')
    
    names = []
    kWhs = []
    for device in devices:
        names.append(device['name'])
        kWhs.append(device['kWh'])
        
    devices=query_db('''select first_datetime,last_datetime from devices order by first_datetime''')
        
    start = devices[0]['first_datetime']
    stop = devices[len(devices)-1]['last_datetime']
    return jsonify(names=names,kWh=kWhs,start=start,stop=stop)




@app.route('/<devicename>')
def device_timeline(devicename):
    """Display's a devicename energy consumption and occurance."""
    profile_user = query_db('select * from devices where name = ?',
                            [devicename], one=True)
    if profile_user is None:
        abort(404)
    followed = False
    if g.user:
        followed = query_db('''select 1 from follower where
            follower.who_id = ? and follower.whom_id = ?''',
            [session['user_id'], profile_user['user_id']],
            one=True) is not None
    return render_template('timeline.html', messages=query_db('''
            select message.*, user.* from message, user where
            user.user_id = message.author_id and user.user_id = ?
            order by message.pub_date desc limit ?''',
            [profile_user['user_id'], PER_PAGE]), followed=followed,
            profile_user=profile_user)


@app.route('/change/<devicename>', methods=['GET','POST'])
def follow_device(devicename):
    """change the device name and add typ."""
    # if not g.user:
    #     abort(401)
    # whom_id = get_user_id(devicename)
    # if whom_id is None:
    #     abort(404)
    # flash("UPDATE devices SET name = '?' and type = '?' WHERE name = '?'")
    
    while True:
        try:
            db = get_db()
            db.execute("UPDATE `devices` SET `name`='%s', `type`='%s' WHERE `name` = '%s'" % (request.form['name'],request.form['device_type'],devicename))
            db.commit()
            break
        except:
            flash("UPDATE `devices` SET `name`='%s', `type`='%s' WHERE `name` = '%s'" % (request.form['name'],request.form['device_type'],devicename))
    
    flash('Device name updated from "%s" to "%s"' % (devicename,request.form['name']))
    # flash('Device type updated to "%s"' % request.form['device_type'])
    # flash('Device name updated ' % 
    return redirect(url_for('timeline', devicename=request.form['name']))


@app.route('/confirm/<devicename>')
def confirm(devicename):
    """Removes the current user as follower of the given user."""
    if not g.user:
        whom_id = 0 #get_user_id(devicename)
    db = get_db()
    db.execute("UPDATE `devices` SET `confirm_datetime`='%s' WHERE `name` = '%s'" % (time.strftime("%Y-%m-%d %H:%M:%S"),devicename))
    db.commit()
    flash('You confirmed "%s".' % devicename)
    return redirect(url_for('timeline'))

@app.route('/cancel/<devicename>')
def cancel(devicename):
    """Removes the current user as follower of the given user."""
    if not g.user:
        whom_id = 0 #get_user_id(devicename)
    db = get_db()
    db.execute("UPDATE `devices` SET `confirm_datetime`='NULL' WHERE `name` = '%s'" % devicename)
    db.commit()
    flash('You unconfirmed "%s".' % devicename)
    return redirect(url_for('timeline'))

@app.route('/monitor/<devicename>')
def monitor(devicename):
    """Removes the current user as follower of the given user."""
    if not g.user:
        whom_id = 0 #get_user_id(devicename)
    db = get_db()
    db.execute("INSERT INTO `device_monitoring` (`user_id`,`device_id`,`trigger`) VALUES ('%s','%s,'test');" % (whom_id,get_device_id(devicename)))
    db.commit()
    flash('You are monitoring "%s".' % devicename)
    return redirect(url_for('timeline'))


@app.route('/add_message', methods=['POST'])
def add_message():
    """Registers a new message for the user."""
    if 'user_id' not in session:
        abort(401)
    if request.form['text']:
        db = get_db()
        db.execute('''insert into message (author_id, text, pub_date)
          values (?, ?, ?)''', (session['user_id'], request.form['text'],
                                int(time.time())))
        db.commit()
        flash('Your message was recorded')
    return redirect(url_for('timeline'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('timeline'))
    error = None
    if request.method == 'POST':
        user = query_db('''select * from user where username = ?''', [request.form['username']], one=True)
        # if user is None:
        #     error = 'Invalid username'
        # elif not check_password_hash(user['pw_hash'],
        #                              request.form['password']):
        #     error = 'Invalid password'
        # else:
        #     flash('You were logged in')
        session['user_id'] = user['user_id']
        return redirect(url_for('timeline'))
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    error = None
    if g.user:
        return redirect(url_for('timeline'))
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user_id(request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            db = get_db()
            db.execute('''insert into user (
              username, email, pw_hash) values (?, ?, ?)''',
              [request.form['username'], request.form['email'],
               generate_password_hash(request.form['password'])])
            db.commit()
            flash('You were successfully registered and can login now')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('public_timeline'))


# add some filters to jinja
app.jinja_env.filters['datetimeformat'] = format_datetime
app.jinja_env.filters['gravatar'] = gravatar_url

if __name__ == '__main__':
      app.run(debug=True, host='0.0.0.0')
