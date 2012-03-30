#!/usr/bin/env python

import os
import sys

import argparse
import ConfigParser

from Crypto.Cipher import Blowfish
import hashlib

from selfspy import DATA_DIR, DBNAME
from password_dialog import get_password
import check_password

"""
    add database fields to allow more of the summaries without a password
    note in the help which commands require password

    add decryption and unpacking (and packing) to models.py
    add lazy iterator to models.py

    add filter to models.py

    do_filter

--
    check_need_text
    check_is_summary
    get password

    print listing

    calc summary
    print summary
"""
class Selfstats:
    def __init__(self, args):
        self.args = args

        self.check_need_text()
        if self.need_text:
            pass #get password
        self.do_filter()

        if self.check_is_summary():
            self.calc_summary()
            self.show_summary()
        else:
            self.show_rows()

    def do_filter(self):
        pass

    def show_rows(self):
      #tabulate data
        for row in rows:
            if text:
                pass
            else:
                pass

    def calc_summary(self):
        sumd = {}
        for row in rows:
            pass


    def show_summary(self):
        pass

    def check_need_text(self):
        self.need_text = True

    def check_is_summary(self):
        self.is_summary = True

def parse_config():
    conf_parser = argparse.ArgumentParser(description=__doc__, add_help=False,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)

    conf_parser.add_argument("-c", "--config",
                             help="""Config file with defaults. Command line parameters will override those given in the config file. Options to selfspy goes in the "[Defaults]" section, followed by [argument]=[value] on each line. Options specific to selfstats should be in the "[Selfstats]" section, though "password" and "data-dir" are still read from "[Defaults]".""", metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()

    defaults = {}
    if args.config:
        config = ConfigParser.SafeConfigParser()
        config.read([args.config])
        defaults = dict(config.items('Defaults'))

    parser = argparse.ArgumentParser(description="""Calculate statistics on selfspy data. Per default it will show non-text information that matches the filter. Adding '-s' means also show text. Adding any of the summary options will show those summaries over the given filter instead of the listing. Multiple summary options can be given to print several summaries over the same filter. If you give arguments that need to access text / keystrokes, you will be asked for the decryption password.""", epilog="""See the README file or http://github.com/gurgeh/selfspy for examples.""", parents=[conf_parser])
    parser.set_defaults(**defaults)
    parser.add_argument('-p', '--password', help='Decryption password. Only needed if selfstats needs to access text / keystrokes data. If your database in not encrypted, specify -p="" here. If you don\'t specify a password in the command line arguments or in a config file, and the statistics you ask for require a password, a dialog will pop up asking for the password. If you give your password on the command line, remember that it will most likely be stored in plain text in your shell history.')
    parser.add_argument('-d', '--data-dir', help='Data directory for selfspy, where the database is stored. Remember that Selfspy must have read/write access. Default is %s' % DATA_DIR, default=DATA_DIR)

    parser.add_argument('-a', '--date', nargs='+', help='Which date to start the listing or summarizing from. If only one argument is given (--date 13) it is interpreted as the closest date in the past on that day. If two arguments are given (--date 03 13) it is interpreted as the closest date in the past on that month and that day, in that order. If three arguments are given (--date 2012 03 13) it is interpreted as YYYY MM DD')
    parser.add_argument('-c', '--clock', type=str, help='Time to start the listing or summarizing from. Given in 24 hour format as --clock 13:25. If no --date is given, interpret the time as today if that results in sometimes in the past, otherwise as yesterday.')

    parser.add_argument('-i', '--id', type=int, help='Which row ID to start the listing or summarizing from. If --date and/or --clock is give, this option is ignored.')

    parser.add_argument('-p', '--period', help='--period <limit> [<unit>]. If no unit is given, period limits the number of rows in the result to <limit>. Otherwise the limit is a time period given by <unit>. <unit> is either "s" (seconds), "m" (minutes), "h" (hours), "d" (days) or "w" (weeks)', nargs='+', type=str)

    parser.add_argument('-m', '--min-keys', type=int, metavar='nr', help='Only allow entries with at least <nr> keystrokes')

    parser.add_argument('-T', '--title', type=str, metavar='regexp', help='Only allow entries where the title matches this <regexp>')
    parser.add_argument('-P', '--process', type=str, metavar='regexp', help='Only allow entries where the process name matches this <regexp>')
    parser.add_argument('-B', '--body', type=str, metavar='regexp', help='Only allow entries where the body matches this <regexp>')

    parser.add_argument('-s', '--showtext', nargs=0, help='Also show the text column. This switch is ignored if at lesat one of the summary options are used.')

    parser.add_argument('--kcratio', nargs=0, help='Summarize the ratio between keystrokes and clicks (not scroll up or down) in the given period.')
    parser.add_argument('--karatio', nargs=0, help='Summarize the ratio between keystrokes and time active in the given period.')

    parser.add_argument('--keystrokes', nargs=0, help='Summarize number of keystrokes')
    parser.add_argument('--clicks', nargs=0, help='Summarize number of mouse button clicks for all buttons.')

    parser.add_argument('--key-freqs', nargs=0, help='Summarize a table of absolute and relative number of keystrokes for each used key during the time period.')

    parser.add_argument('--active', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='Summarize total time spent active during the period. The optional argument gives how many seconds after each mouse click (including scroll up or down) or keystroke that you are considered active. Default is %d' % ACTIVE_SECONDS)
    parser.add_argument('--periods', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List active time periods. Optional argument works same as for --active')

    parser.add_argument('--pactive', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List processes, sorted by time spent active in them. Optional argument works same as for --active')
    parser.add_argument('--tactive', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List window titles, sorted by time spent active in them. Optional argument works same as for --active')

    parser.add_argument('--pkeys', nargs=0, help='List processes sorted by number of keystrokes.')
    parser.add_argument('--tkeys', nargs=0, help='List window titles sorted by number of keystrokes.')

    return parser.parse_args()

if __name__ == '__main__':
    args = vars(parse_config())

    args['data_dir'] = os.path.expanduser(args['data_dir'])

    if need_decryption(args):
        if args['password'] is None:
            args['password'] = get_password()

        if args['password'] == "":
            decrypter = None
        else:
            decrypter = Blowfish.new(hashlib.md5(args['password']).digest())

        if not check_password.check(args['data_dir'], decrypter):
            print 'Password failed'
            sys.exit(1)



