#!/usr/bin/env python

import os
import sys
import time

import argparse
import ConfigParser

import daemon
import lockfile
import signal
import grp
import pwd

import hashlib
from Crypto.Cipher import Blowfish

from activity_store import ActivityStore
from password_dialog import get_password
import check_password

"""

Todo:
  put weekly mail in cron

  try rebooting with .xinitrc

  try all queries from README
  copy Pages to README

  tag release in github

--
  test keymap switch

---Later
  code documentation, unittests, pychecker ;)
  replay key and mouse for process and time interval (maybe store as macro)
  word search
  calculate personal keymap

"""

DATA_DIR = '~/.selfspy'
DBNAME = 'selfspy.sqlite'
LOCK_FILE = 'selfspy.pid'

def parse_config():
    conf_parser = argparse.ArgumentParser(description=__doc__, add_help=False,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)
    conf_parser.add_argument("-c", "--config",
                             help="Config file with defaults. Command line parameters will override those given in the config file. The config file must start with a \"[Defaults]\" section, followed by [argument]=[value] on each line.", metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()

    defaults = {}
    if args.config:
        config = ConfigParser.SafeConfigParser()
        config.read([args.config])
        defaults = dict(config.items('Defaults'))

    parser = argparse.ArgumentParser(description='Monitor your computer activities and store them in an encrypted database for later analysis or disaster recovery.', parents=[conf_parser])
    parser.set_defaults(**defaults)
    parser.add_argument('-p', '--password', help='Encryption password. If you want to keep your database unencrypted, specify -p "" here. If you don\'t specify a password in the command line arguments or in a config file, a dialog will pop up, asking for the password. The most secure is to not use either command line or config file but instead type it in on startup.')
    parser.add_argument('-d', '--data-dir', help='Data directory for selfspy, where the database is stored. Remember that Selfspy must have read/write access. Default is %s' % DATA_DIR, default=DATA_DIR)

    parser.add_argument('-n', '--no-text', action='store_true', help='Do not store what you type. This will make your database smaller and less sensitive to security breaches. Process name, window titles, window geometry, mouse clicks, number of keys pressed and key timings will still be stored, but not the actual letters. Key timings are stored to enable activity calculation in selfstats.py. If this switch is used, you will never be asked for password.')

    return parser.parse_args()

if __name__ == '__main__':
    args = vars(parse_config())

    args['data_dir'] = os.path.expanduser(args['data_dir'])

    try:
        os.makedirs(args['data_dir'])
    except OSError:
        pass

    lockname = os.path.join(args['data_dir'], LOCK_FILE)
    lock = lockfile.FileLock(lockname)
    if lock.is_locked():
        print '%s is locked! I am probably already running.' % lockname
        print 'If you can find no selfspy process running, it is a stale lock and you can safely remove it.'
        print 'Shutting down.'
        sys.exit(1)

    context = daemon.DaemonContext(
        working_directory=args['data_dir'],
        pidfile=lock,
        stderr=sys.stderr
    )

    context.signal_map = {
        signal.SIGTERM: 'terminate',
        signal.SIGHUP: 'terminate'
    }


    if args['no_text']:
        args['password'] = ""
    
    if args['password'] is None:
        args['password'] = get_password()

    if args['password'] == "":
        encrypter = None
    else:
        encrypter = Blowfish.new(hashlib.md5(args['password']).digest())

    if not check_password.check(args['data_dir'], encrypter):
        print 'Password failed'
        sys.exit(1)

    with context:    
        astore = ActivityStore(os.path.join(args['data_dir'], DBNAME), encrypter, store_text=(not args['no_text']))
                        
        try:
            astore.run()
        except SystemExit:
            astore.close()
