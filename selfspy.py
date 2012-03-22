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

from activity_store import ActivityStore

DATA_DIR = '/var/lib/selfspy'
DBNAME = 'selfspy.sqlite'
LOCK_FILE = '/var/run/selfspy/selfspy.pid'

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
    parser.add_argument('-p', '--password', help='Encryption password. If you want to keep your database unencrypted, specify -p "" here. If you don\'t specify a password in the command line arguments or (preferable) in a config file, a dialog will pop up, asking for the password each time this program is run. Usually when X starts.')
    parser.add_argument('-d', '--data-dir', help='Data directory for selfspy, where the database is stored. Remember that Selfspy must have read/write access. Default is %s' % DATA_DIR, default=DATA_DIR)
    parser.add_argument('-l', '--lock-file', help='Lock file. Default is %s' % LOCK_FILE, default=LOCK_FILE)
    parser.add_argument('-u', '--uid', help='User ID to switch process to on daemon start. You can specify either name or number. Default is to keep process uid.', default=os.getuid())
    parser.add_argument('-g', '--gid', help='Group ID to switch process to on daemon start. You can specify either name or number. Default is to keep process gid.', default=os.getgid())

    return parser.parse_args()

if __name__ == '__main__':
    args = vars(parse_config())
    try:
        args['gid'] = int(args['gid'])
    except ValueError:
        args['gid'] = grp.getgrnam(args['gid'])
    try:
        args['uid'] = int(args['uid'])
    except ValueError:
        args['uid'] = pwd.getpwnam(args['uid']).pw_gid
    print args

    lock = lockfile.FileLock(args['lock_file'])
    if lock.is_locked():
        print '%s is locked! I am probably already running.' % args['lock_file']
        print 'If you can find no selfspy process running, it is a stale lock and you can safely remove it.'
        print 'Shutting down.'
        sys.exit()

    context = daemon.DaemonContext(
        working_directory=args['data_dir'],
        pidfile=lock,
        stdout=sys.stdout,
        stderr=sys.stderr,
        uid=args['uid'],
        gid=args['gid']
    )

    context.signal_map = {
        signal.SIGTERM: 'terminate',
        signal.SIGHUP: 'terminate'
    }
    
    try:
        with context:
            astore = ActivityStore(os.path.join(args['data_dir'], DBNAME))
            astore.run()
            while True:
                time.sleep(1000000000)
    except SystemExit:
        astore.close()
