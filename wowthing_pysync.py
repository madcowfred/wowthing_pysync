#!/usr/bin/env python

import datetime
import os
import requests
import sys
import time
import ConfigParser


OPTIONS = ['username', 'password', 'wowpath', 'interval']
UPLOAD_URI = 'https://www.wowthing.org/api/upload/'


def main():
    # Make sure the config file exists
    config_file = os.path.join(os.path.dirname(__file__), 'sync.conf')
    if not os.path.exists(config_file):
        error('config file does not exist: %s' % config_file)

    # Try to load config file
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    # Sanity check on variables
    for option in OPTIONS:
        try:
            blah = config.get('sync', option)
        except:
            error('config file "%s" option is missing!' % option)

        if not blah:
            error('config file "%s" option is blank!' % option)

    # Make sure the WoW path exists
    wtf_path = os.path.join(config.get('sync', 'wowpath'), 'WTF', 'Account')
    if not os.path.isdir(wtf_path):
        error('path does not exist or is not a directory: %s' % wtf_path)

    # I guess we can get started now
    loop(config, wtf_path)

def error(message):
    print 'ERROR: %s' % (message)
    sys.exit(1)

def log(message):
    print '%s  %s' % (datetime.datetime.now(), message)

def loop(config, wtf_path):
    last_mtime = {}

    # Find all account paths
    for filename in os.listdir(wtf_path):
        if filename == 'SavedVariables':
            continue

        filepath = os.path.join(wtf_path, filename, 'SavedVariables', 'WoWthing_Collector.lua')
        if os.path.exists(filepath):
            last_mtime[filepath] = os.path.getmtime(filepath)

    log('wowthing_pysync started')

    # Loop forever and upload files if data changes
    interval = int(config.get('sync', 'interval'))
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'wowthing_pysync',
    })

    while True:
        for filepath, old_mtime in last_mtime.items():
            new_mtime = os.path.getmtime(filepath)
            if new_mtime > old_mtime:
                last_mtime[filepath] = new_mtime
                upload(config, filepath, session)

        time.sleep(interval)

def upload(config, filepath, session):
    log('uploading %s' % filepath)

    data = dict(username=config.get('sync', 'username'), password=config.get('sync', 'password'))
    files = dict(lua_file=open(filepath, 'rb'))

    r = session.post(UPLOAD_URI, data, files=files)
    if r.status_code == requests.codes.ok:
        log('upload complete')
    else:
        error('upload failed: %s %r' % (r.status_code, r.content))


if __name__ == '__main__':
    main()
