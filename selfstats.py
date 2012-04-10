#!/usr/bin/env python

import os
import sys
import re
import datetime
import time

import argparse
import ConfigParser

from collections import Counter

from Crypto.Cipher import Blowfish
import hashlib

from selfspy import DATA_DIR, DBNAME
from password_dialog import get_password
import check_password
from period import Period

import models

"""
    print summaries
      periods
      
      ratios
        also summarize mouse_movement ratios
        maybe list all ratios with one switch
--
    argument groups

    warn for bad regexp, PERIOD_LOOKUP and int() fail
    warn on different activity_cutoffs

    prettier printing for table?

    test
      arg groups
      pprint
      summaries
      activity
      process ID bug
      config file
--
    maybe have a general sortby argument for processes and titles, instead of just keys
    refactor sorting in summary
"""

ACTIVE_SECONDS = 180
PERIOD_LOOKUP = {'s' : 'seconds', 'm' : 'minutes', 'h' : 'hours', 'd' : 'days', 'w' : 'weeks'}
ACTIVITY_ACTIONS = {'active', 'periods', 'pactive', 'tactive', 'karatio'}
SUMMARY_ACTIONS = ACTIVITY_ACTIONS.union({'pkeys', 'tkeys', 'key_freqs', 'clicks', 'karatio', 'kcratio'})

BUTTON_MAP = [('button1','left'), ('button2','middle'), ('button3','right'), ('button4','up'), ('button5','down')]

def pretty_seconds(secs):
    secs = int(secs)
    starts = secs
    active = False
    outs = ''
    days = secs / (3600 * 24)
    if days:
        active = True
        outs += '%d days, ' % days
    secs -= days * (3600 * 24)

    hours = secs / 3600
    if hours:
        active = True
    if active:
        outs += '%dh ' % hours
    secs -= hours * 3600

    
    minutes = secs / 60
    if minutes:
        active = True
    if active:
        outs += '%dm ' % minutes
    secs -= minutes * 60

    outs += '%ds' % secs
    #if active:
    #    outs +=  ' (%d seconds total)' % starts
        
    return outs
    

def make_time_string(dates, clock):
    now = datetime.datetime.now()
    now2 = datetime.datetime.now()

    if dates is None: dates = []

    if len(dates) > 3:
        print 'Max three arguments to date', dates
        sys.exit(1)

    try:
        dates = [int(d) for d in dates]
        if len(dates) == 3: now = now.replace(year=dates[0])
        if len(dates) >= 2: now = now.replace(month=dates[-2])
        if len(dates) >= 1: now = now.replace(day=dates[-1])

        if len(dates) == 2:
            if now > now2:
                now = now.replace(year=now.year - 1)
    
        if len(dates) == 1:
            if now > now2:
                m = now.month - 1
                if m:
                    now = now.replace(month=m)
                else:
                    now = now.replace(year=now.year - 1, month=12)
    except ValueError:
        print 'Malformed date', dates
        sys.exit(1)

    if clock:
        try:
            hour, minute = [int(v) for v in clock.split(':')]
        except ValueError:
            print 'Malformed clock', clock
            sys.exit(1)
        
        now = now.replace(hour=hour, minute=minute, second=0)

        if now > now2:
            now -= datetime.timedelta(days=1)

    return now.strftime('%Y-%m-%d %H:%M'), now

def make_period(q, start, period):
    if len(period) < 1 or len(period) > 2:
        print '--limit needs one or two arguments, not %d' % len(period), period
        sys.exit(1)

    d = {}
    val = int(period[0])
    if len(period) == 1:
        d['hours'] = val
    else:
        d[PERIOD_LOOKUP[period[1]]] = val
    
    q = q.filter(models.Keys.started <= start + datetime.timedelta(**d))

    return q

def create_times(row):
    current_time = time.mktime(row.created_at.timetuple())
    abs_times = [current_time]
    for t in row.timings:
        current_time += 1
        abs_times.append(current_time)
    return abs_times

class Selfstats:
    def __init__(self, db_name, args):
        self.args = args
        self.session_maker = models.initialize(db_name)

        self.check_needs()
    
    def do(self):
        if self.need_summary:
            self.calc_summary()
            self.show_summary()
        else:
            self.show_rows()

    def check_needs(self):
        print self.args
        self.need_text = False
        self.need_activity = False
        self.need_timings = False
        self.need_keys = False
        self.need_summary = False

        if self.args['body'] is not None: self.need_text = True
        if self.args['showtext']: self.need_text = True
        cutoff = [self.args[k] for k in ACTIVITY_ACTIONS if self.args[k]]
        if cutoff:
            self.need_activity = cutoff[0]
            self.need_timings = True
        if self.args['key_freqs']: self.need_keys = True

        if any(self.args[k] for k in SUMMARY_ACTIONS): self.need_summary = True

    def maybe_reg_filter(self, q, name, names, table, source_prop, target_prop):
        if self.args[name] is not None:
            ids = []
            try:
                reg = re.compile(self.args[name])
            except re.error, e:
                print 'Error in regular expression', str(e)
                sys.exit(1)

            for x in self.session.query(table).all():
                if reg.search(x.__getattribute__(source_prop)):
                    ids.append(x.id)
            print len(ids), '%s matched' % names, ids
            if ids:
                q = q.filter(target_prop.in_(ids))
            else:
                return q, False
        return q, True

    def filter_prop(self, prop):
        self.session = self.session_maker()

        q = self.session.query(prop).order_by(prop.id)

        if self.args['date'] or self.args['clock']:
            s, start = make_time_string(self.args['date'], self.args['clock'])
            print s
            q = q.filter(prop.created_at >= s)
            if self.args['limit'] is not None:
                q = make_period(q, start, self.args['limit'])
        elif self.args['id'] is not None:
            q = q.filter(prop.id >= self.args['id'])
            if self.args['limit'] is not None:
                q = q.filter(prop.id < self.args['id'] + int(self.args['limit'][0]))

        q, found = self.maybe_reg_filter(q, 'process', 'process(es)', models.Process, 'name', prop.process_id)
        if not found: return None

        q, found = self.maybe_reg_filter(q, 'title', 'title(s)', models.Window, 'title', prop.window_id)
        if not found: return None

        return q

    def filter_keys(self):
        q = self.filter_prop(models.Keys)
        if q is None: return

        if self.args['min_keys'] is not None:
            q = q.filter(Keys.nrkeys >= self.args['min_keys'])
        
        if self.args['body']:
            bodrex = re.compile(self.args['body'])
            for x in q.all():
                body = x.decrypt_text()
                if bodrex.search(body):
                    yield x
        else:
            for x in q.all():
                yield x
        
    def filter_clicks(self):
        q = self.filter_prop(models.Click)
        if q is None: return

        for x in q.all():
            yield x

    def show_rows(self):
        fkeys = self.filter_keys()
        for row in fkeys:
            print row.id, row.started, (row.created_at - row.started).total_seconds(), row.process.name, row.window.title, row.nrkeys, row.process_id, 
            if self.args['showtext']:
                print row.decrypt_text()
            else:
                print
        print len(fkeys), 'rows'

    def calc_summary(self):
        def updict(d1, d2, activity_times, sub=None):
            if sub is not None:
                if sub not in d1:
                    d1[sub] = {}
                d1 = d1[sub]

            for key,val in d2.items():
                if key not in d1:
                    d1[key] = 0
                d1[key] += val
                
            if self.need_activity:
                if 'activity' not in d1:
                    d1['activity'] = Period()
                d1['activity'].extend(activity_times)

        sumd = {}
        processes = {}
        windows = {}
        timings = []
        keys = Counter()
        for row in self.filter_keys():
            d = {'nr':1, 'keystrokes':row.nrkeys}

            if self.need_activity:
                timings = create_times(row)
            updict(processes, d, timings, sub=row.process.name)
            updict(windows, d, timings, sub=row.window.title)
            updict(sumd, d, timings)

            if self.args['key_freqs']:
                keys.update(row.decrypt_keys())

        for click in self.filter_clicks():
            d = {'noscroll_clicks' : click.button not in [4,5],
                 'clicks' : 1,
                 'button%d'%click.button : 1,
                 'mousings' : click.nrmoves}
            timings = [time.mktime(row.created_at.timetuple())]
            updict(processes, d, timings, sub=row.process.name)
            updict(windows, d, timings, sub=row.window.title)
            updict(sumd, d, timings)
        
        self.processes = processes
        self.windows = windows
        self.summary = sumd
        if self.args['key_freqs']:
            self.summary['key_freqs'] = keys


    def show_summary(self):
        print '%d keystrokes in %d key sequences,' % (self.summary['keystrokes'], self.summary['nr']),
        print '%d clicks (%d excluding scroll),' % (self.summary['clicks'], self.summary['noscroll_clicks']),
        print '%d mouse movements' % (self.summary['mousings'])
        print

        if self.need_activity:
            act = self.summary['activity'].calc_total(self.need_activity)
            print 'Total time active:', 
            print pretty_seconds(act)
            print

        if self.args['clicks']:
            print 'Mouse clicks:'
            for key,name in BUTTON_MAP:
                print self.summary.get(key, 0), name
            print

        if self.args['key_freqs']:
            print 'Key frequencies:'
            for key,val in self.summary['key_freqs'].most_common():
                print key, val
            print

        if self.args['pkeys']:
            print 'Processes sorted by keystrokes:'
            pdata = self.processes.items()
            pdata.sort(key=lambda x:x[1]['keystrokes'], reverse=True)
            for name, data in pdata:
                print name, data['keystrokes']
            print

        if self.args['tkeys']:
            print 'Window titles sorted by keystrokes:'
            wdata = self.windows.items()
            wdata.sort(key=lambda x:x[1]['keystrokes'], reverse=True)
            for name, data in wdata:
                print name, data['keystrokes']
            print

        if self.args['pactive']:
            print 'Processes sorted by activity (in seconds):'
            for p in self.processes.values():
                p['active_time'] = int(p['activity'].calc_total(self.need_activity))
            pdata = self.processes.items()
            pdata.sort(key=lambda x:x[1]['active_time'], reverse=True)
            for name, data in pdata:
                print '%s, %s' % (name, pretty_seconds(data['active_time']))
            print

        if self.args['tactive']:
            print 'Window titles sorted by activity (in seconds):'
            for w in self.windows.values():
                w['active_time'] = int(w['activity'].calc_total(self.need_activity))
            wdata = self.windows.items()
            wdata.sort(key=lambda x:x[1]['active_time'], reverse=True)
            for name, data in wdata:
                print '%s, %s' % (name, pretty_seconds(data['active_time']))
            print
        


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
        defaults = dict(config.items('Defaults') + config.items("Selfstats"))

    parser = argparse.ArgumentParser(description="""Calculate statistics on selfspy data. Per default it will show non-text information that matches the filter. Adding '-s' means also show text. Adding any of the summary options will show those summaries over the given filter instead of the listing. Multiple summary options can be given to print several summaries over the same filter. If you give arguments that need to access text / keystrokes, you will be asked for the decryption password.""", epilog="""See the README file or http://github.com/gurgeh/selfspy for examples.""", parents=[conf_parser])
    parser.set_defaults(**defaults)
    parser.add_argument('-p', '--password', help='Decryption password. Only needed if selfstats needs to access text / keystrokes data. If your database in not encrypted, specify -p="" here. If you don\'t specify a password in the command line arguments or in a config file, and the statistics you ask for require a password, a dialog will pop up asking for the password. If you give your password on the command line, remember that it will most likely be stored in plain text in your shell history.')
    parser.add_argument('-d', '--data-dir', help='Data directory for selfspy, where the database is stored. Remember that Selfspy must have read/write access. Default is %s' % DATA_DIR, default=DATA_DIR)

    parser.add_argument('-D', '--date', nargs='+', help='Which date to start the listing or summarizing from. If only one argument is given (--date 13) it is interpreted as the closest date in the past on that day. If two arguments are given (--date 03 13) it is interpreted as the closest date in the past on that month and that day, in that order. If three arguments are given (--date 2012 03 13) it is interpreted as YYYY MM DD')
    parser.add_argument('-C', '--clock', type=str, help='Time to start the listing or summarizing from. Given in 24 hour format as --clock 13:25. If no --date is given, interpret the time as today if that results in sometimes in the past, otherwise as yesterday.')

    parser.add_argument('-i', '--id', type=int, help='Which row ID to start the listing or summarizing from. If --date and/or --clock is give, this option is ignored.')

    parser.add_argument('-l', '--limit', help='--limit <period> [<unit>]. If the start is given in --date/--clock, the limit is a time period given by <unit>. <unit> is either "s" (seconds), "m" (minutes), "h" (hours), "d" (days) or "w" (weeks). If no unit is given, it is assumed to be hours. If the start is given with --id, limit has no unit and means that the maximum row ID is --id + --limit.', nargs='+', type=str)

    parser.add_argument('-m', '--min-keys', type=int, metavar='nr', help='Only allow entries with at least <nr> keystrokes')

    parser.add_argument('-T', '--title', type=str, metavar='regexp', help='Only allow entries where a search for this <regexp> in the title matches something.')
    parser.add_argument('-P', '--process', type=str, metavar='regexp', help='Only allow entries where a search for this <regexp> in the process matches something.')
    parser.add_argument('-B', '--body', type=str, metavar='regexp', help='Only allow entries where a search for this <regexp> in the body matches something. Do not use this filter when summarizing ratios or activity, as it has no effect on mouse clicks. Requires password.')

    parser.add_argument('-s', '--showtext', action='store_true', help='Also show the text column. This switch is ignored if at least one of the summary options are used. Requires password.')

    parser.add_argument('--kcratio', action='store_true', help='Summarize the ratio between keystrokes and clicks (not scroll up or down) in the given period.')
    parser.add_argument('--karatio', action='store_true', help='Summarize the ratio between keystrokes and time active in the given period.')

    parser.add_argument('--clicks', action='store_true', help='Summarize number of mouse button clicks for all buttons.')

    parser.add_argument('--key-freqs', action='store_true', help='Summarize a table of absolute and relative number of keystrokes for each used key during the time period. Requires password.')

    parser.add_argument('--active', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='Summarize total time spent active during the period. The optional argument gives how many seconds after each mouse click (including scroll up or down) or keystroke that you are considered active. Default is %d' % ACTIVE_SECONDS)
    parser.add_argument('--periods', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List active time periods. Optional argument works same as for --active')

    parser.add_argument('--pactive', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List processes, sorted by time spent active in them. Optional argument works same as for --active')
    parser.add_argument('--tactive', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List window titles, sorted by time spent active in them. Optional argument works same as for --active')

    parser.add_argument('--pkeys', action='store_true', help='List processes sorted by number of keystrokes.')
    parser.add_argument('--tkeys', action='store_true', help='List window titles sorted by number of keystrokes.')

    return parser.parse_args()

if __name__ == '__main__':
    args = vars(parse_config())

    args['data_dir'] = os.path.expanduser(args['data_dir'])

    ss = Selfstats(os.path.join(args['data_dir'], DBNAME), args)

    if ss.need_text or ss.need_keys:
        if args['password'] is None:
            args['password'] = get_password()

        if args['password'] == "":
            models.ENCRYPTER = None
        else:
            models.ENCRYPTER = Blowfish.new(hashlib.md5(args['password']).digest())

        if not check_password.check(args['data_dir'], models.ENCRYPTER, read_only=True):
            print 'Password failed'
            sys.exit(1)

    ss.do()

