#!/usr/bin/env python

# Copyright 2012 David Fendrich

# This file is part of Selfspy

# Selfspy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Selfspy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Selfspy.  If not, see <http://www.gnu.org/licenses/>.

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

import config as cfg

from selfspy import check_password
from selfspy.password_dialog import get_password
from selfspy.period import Period

from selfspy import models

import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)

ACTIVE_SECONDS = 180
PERIOD_LOOKUP = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days', 'w': 'weeks'}
ACTIVITY_ACTIONS = {'active', 'periods', 'pactive', 'tactive', 'ratios'}
SUMMARY_ACTIONS = ACTIVITY_ACTIONS.union({'pkeys', 'tkeys', 'key_freqs', 'clicks', 'ratios'})

PROCESS_ACTIONS = {'pkeys', 'pactive'}
WINDOW_ACTIONS = {'tkeys', 'tactive'}

BUTTON_MAP = [('button1', 'left'),
              ('button2', 'middle'),
              ('button3', 'right'),
              ('button4', 'up'),
              ('button5', 'down')]


def pretty_seconds(secs):
    secs = int(secs)
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

    return outs


def make_time_string(dates, clock):
    now = datetime.datetime.now()
    now2 = datetime.datetime.now()

    if dates is None:
        dates = []

    if isinstance(dates, list) and len(dates) > 0:
        if type(dates[0]) is str:
            datesstr = " ".join(dates)
        else:
            print '%s is of uncompatible type list of %s.' % (
                dates[0], str(type(dates[0])))
    elif isinstance(dates, basestring):
        datesstr = dates
    else:
        datesstr = now.strftime('%Y %m %d')
    dates = datesstr.split()  # any whitespace

    if len(dates) > 3:
        print 'Max three arguments to date', dates
        sys.exit(1)

    try:
        dates = [int(d) for d in dates]
        if len(dates) == 3:
            now = now.replace(year=dates[0])
        if len(dates) >= 2:
            now = now.replace(month=dates[-2])
        if len(dates) >= 1:
            now = now.replace(day=dates[-1])

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


def make_period(q, period, who, start, prop):
    if isinstance(period, list) and len(period)>0:
        if type(period[0]) is str:
            periodstr = "".join(period)
        else:
            print '%s is of uncompatible type list of %s.' % (who, str(type(period[0])))
    elif isinstance(period, basestring):
        periodstr = period.translate(None, " \t")
    else:
        print '%s is of uncompatible type %s.' % (who, str(type(period)))
        sys.exit(1)
    pmatch = re.match("(\d+)(["+"".join(PERIOD_LOOKUP.keys())+"]?)", periodstr)
    if pmatch==None:
        print '%s has an unrecognizable format: %s' % (who, periodstr)
        sys.exit(1)
    period = [pmatch.group(1)]+([pmatch.group(2)] if pmatch.group(2) else [])

    d = {}
    val = int(period[0])
    if len(period) == 1:
        d['hours'] = val
    else:
        if period[1] not in PERIOD_LOOKUP:
            print '--limit unit "%s" not one of %s' % (period[1], PERIOD_LOOKUP.keys())
            sys.exit(1)
        d[PERIOD_LOOKUP[period[1]]] = val

    if start:
        return q.filter(prop <= start + datetime.timedelta(**d))
    else:
        start = datetime.datetime.now() - datetime.timedelta(**d)
        return q.filter(prop >= start), start


def create_times(row):
    current_time = time.mktime(row.created_at.timetuple())
    abs_times = [current_time]
    for t in row.load_timings():
        current_time -= t
        abs_times.append(current_time)
    abs_times.reverse()
    return abs_times


class Selfstats:
    def __init__(self, db_name, args):
        self.args = args
        self.session_maker = models.initialize(db_name)
        self.inmouse = False

        self.check_needs()

    def do(self):
        if self.need_summary:
            self.calc_summary()
            self.show_summary()
        else:
            self.show_rows()

    def check_needs(self):
        self.need_text = False
        self.need_activity = False
        self.need_timings = False
        self.need_keys = False
        self.need_humanreadable = False
        self.need_summary = False
        self.need_process = any(self.args[k] for k in PROCESS_ACTIONS)
        self.need_window = any(self.args[k] for k in WINDOW_ACTIONS)

        if self.args['body'] is not None:
            self.need_text = True
        if self.args['showtext']:
            self.need_text = True
        cutoff = [self.args[k] for k in ACTIVITY_ACTIONS if self.args[k]]
        if cutoff:
            if any(c != cutoff[0] for c in cutoff):
                print 'You must give the same time argument to the different parameters in the --active family, when you use several in the same query.'
                sys.exit(1)
            self.need_activity = cutoff[0]
            self.need_timings = True
        if self.args['key_freqs']:
            self.need_keys = True
        if self.args['human_readable']:
            self.need_humanreadable = True

        if any(self.args[k] for k in SUMMARY_ACTIONS):
            self.need_summary = True

    def maybe_reg_filter(self, q, name, names, table, source_prop, target_prop):
        if self.args[name] is not None:
            ids = []
            try:
                reg = re.compile(self.args[name], re.I)
            except re.error, e:
                print 'Error in regular expression', str(e)
                sys.exit(1)

            for x in self.session.query(table).all():
                if reg.search(x.__getattribute__(source_prop)):
                    ids.append(x.id)
            if not self.inmouse:
                print '%d %s matched' % (len(ids), names)
            if ids:
                q = q.filter(target_prop.in_(ids))
            else:
                return q, False
        return q, True

    def filter_prop(self, prop, startprop):
        self.session = self.session_maker()

        q = self.session.query(prop).order_by(prop.id)

        if self.args['date'] or self.args['clock']:
            s, start = make_time_string(self.args['date'], self.args['clock'])
            q = q.filter(prop.created_at >= s)
            if self.args['limit'] is not None:
                q = make_period(q, self.args['limit'], '--limit', start, startprop)
        elif self.args['id'] is not None:
            q = q.filter(prop.id >= self.args['id'])
            if self.args['limit'] is not None:
                q = q.filter(prop.id < self.args['id'] + int(self.args['limit'][0]))
        elif self.args['back'] is not None:
            q, start = make_period(q, self.args['back'], '--back', None, startprop)
            if self.args['limit'] is not None:
                q = make_period(q, self.args['limit'], '--limit', start, startprop)

        q, found = self.maybe_reg_filter(q, 'process', 'process(es)', models.Process, 'name', prop.process_id)
        if not found:
            return None

        q, found = self.maybe_reg_filter(q, 'title', 'title(s)', models.Window, 'title', prop.window_id)
        if not found:
            return None

        return q

    def filter_keys(self):
        q = self.filter_prop(models.Keys, models.Keys.started)
        if q is None:
            return

        if self.args['min_keys'] is not None:
            q = q.filter(models.Keys.nrkeys >= self.args['min_keys'])

        if self.args['body']:
            try:
                bodrex = re.compile(self.args['body'], re.I)
            except re.error, e:
                print 'Error in regular expression', str(e)
                sys.exit(1)
            for x in q.all():
                if(self.need_humanreadable):
                    body = x.decrypt_humanreadable()
                else:
                    body = x.decrypt_text()
                if bodrex.search(body):
                    yield x
        else:
            for x in q:
                yield x

    def filter_clicks(self):
        self.inmouse = True
        q = self.filter_prop(models.Click, models.Click.created_at)
        if q is None:
            return

        for x in q:
            yield x

    def show_rows(self):
        fkeys = self.filter_keys()
        rows = 0
        print '<RowID> <Starting date and time> <Duration> <Process> <Window title> <Number of keys pressed>',
        if self.args['showtext'] and self.need_humanreadable:
            print '<Decrypted Human Readable text>'
        elif self.args['showtext']:
            print '<Decrypted text>'
        else:
            print

        for row in fkeys:
            rows += 1
            print row.id, row.started, pretty_seconds((row.created_at - row.started).total_seconds()), row.process.name, '"%s"' % row.window.title, row.nrkeys,
            if self.args['showtext']:
                if self.need_humanreadable:
                    print row.decrypt_humanreadable().decode('utf8')
                else:
                    print row.decrypt_text().decode('utf8')
            else:
                print
        print rows, 'rows'

    def calc_summary(self):
        def updict(d1, d2, activity_times, sub=None):
            if sub is not None:
                if sub not in d1:
                    d1[sub] = {}
                d1 = d1[sub]

            for key, val in d2.items():
                if key not in d1:
                    d1[key] = 0
                d1[key] += val

            if self.need_activity:
                if 'activity' not in d1:
                    d1['activity'] = Period(self.need_activity, time.time())
                d1['activity'].extend(activity_times)

        sumd = {}
        processes = {}
        windows = {}
        timings = []
        keys = Counter()
        for row in self.filter_keys():
            d = {'nr': 1,
                 'keystrokes': len(row.load_timings())}

            if self.need_activity:
                timings = create_times(row)
            if self.need_process:
                updict(processes, d, timings, sub=row.process.name)
            if self.need_window:
                updict(windows, d, timings, sub=row.window.title)
            updict(sumd, d, timings)

            if self.args['key_freqs']:
                keys.update(row.decrypt_keys())

        for click in self.filter_clicks():
            d = {'noscroll_clicks': click.button not in [4, 5],
                 'clicks': 1,
                 'button%d' % click.button: 1,
                 'mousings': click.nrmoves}
            if self.need_activity:
                timings = [time.mktime(click.created_at.timetuple())]
            if self.need_process:
                updict(processes, d, timings, sub=click.process.name)
            if self.need_window:
                updict(windows, d, timings, sub=click.window.title)
            updict(sumd, d, timings)

        self.processes = processes
        self.windows = windows
        self.summary = sumd
        if self.args['key_freqs']:
            self.summary['key_freqs'] = keys

    def show_summary(self):
        print '%d keystrokes in %d key sequences,' % (self.summary.get('keystrokes', 0), self.summary.get('nr', 0)),
        print '%d clicks (%d excluding scroll),' % (self.summary.get('clicks', 0), self.summary.get('noscroll_clicks', 0)),
        print '%d mouse movements' % (self.summary.get('mousings', 0))
        print

        if self.need_activity:
            act = self.summary.get('activity')

            if act:
                act = act.calc_total()
            else:
                act = 0
            print 'Total time active:',
            print pretty_seconds(act)
            print

        if self.args['clicks']:
            print 'Mouse clicks:'
            for key, name in BUTTON_MAP:
                print self.summary.get(key, 0), name
            print

        if self.args['key_freqs']:
            print 'Key frequencies:'
            for key, val in self.summary['key_freqs'].most_common():
                print key, val
            print

        if self.args['pkeys']:
            print 'Processes sorted by keystrokes:'
            pdata = self.processes.items()
            pdata.sort(key=lambda x: x[1].get('keystrokes', 0), reverse=True)
            for name, data in pdata:
                print name, data.get('keystrokes', 0)
            print

        if self.args['tkeys']:
            print 'Window titles sorted by keystrokes:'
            wdata = self.windows.items()
            wdata.sort(key=lambda x: x[1].get('keystrokes', 0), reverse=True)
            for name, data in wdata:
                print name, data.get('keystrokes', 0)
            print

        if self.args['pactive']:
            print 'Processes sorted by activity:'
            for p in self.processes.values():
                p['active_time'] = int(p['activity'].calc_total())
            pdata = self.processes.items()
            pdata.sort(key=lambda x: x[1]['active_time'], reverse=True)
            for name, data in pdata:
                print '%s, %s' % (name, pretty_seconds(data['active_time']))
            print

        if self.args['tactive']:
            print 'Window titles sorted by activity:'
            for w in self.windows.values():
                w['active_time'] = int(w['activity'].calc_total())
            wdata = self.windows.items()
            wdata.sort(key=lambda x: x[1]['active_time'], reverse=True)
            for name, data in wdata:
                print '%s, %s' % (name, pretty_seconds(data['active_time']))
            print

        if self.args['periods']:
            if 'activity' in self.summary:
                print 'Active periods:'
                for t1, t2 in self.summary['activity'].times:
                    d1 = datetime.datetime.fromtimestamp(t1).replace(microsecond=0)
                    d2 = datetime.datetime.fromtimestamp(t2).replace(microsecond=0)
                    print '%s - %s' % (d1.isoformat(' '), str(d2.time()).split('.')[0])
            else:
                print 'No active periods.'
            print

        if self.args['ratios']:
            def tryget(prop):
                return float(max(1, self.summary.get(prop, 1)))

            mousings = tryget('mousings')
            clicks = tryget('clicks')
            keys = tryget('keystrokes')
            print 'Keys / Clicks: %.1f' % (keys / clicks)
            print 'Active seconds / Keys: %.1f' % (act / keys)
            print
            print 'Mouse movements / Keys: %.1f' % (mousings / keys)
            print 'Mouse movements / Clicks: %.1f' % (mousings / clicks)
            print


def parse_config():
    conf_parser = argparse.ArgumentParser(description=__doc__, add_help=False,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)

    conf_parser.add_argument("-c", "--config",
                             help="""Config file with defaults. Command line parameters will override those given in the config file. Options to selfspy goes in the "[Defaults]" section, followed by [argument]=[value] on each line. Options specific to selfstats should be in the "[Selfstats]" section, though "password" and "data-dir" are still read from "[Defaults]".""", metavar="FILE")
    args, remaining_argv = conf_parser.parse_known_args()

    defaults = {}
    if args.config:
        if not os.path.exists(args.config):
            raise  EnvironmentError("Config file %s doesn't exist." % args.config)
        config = ConfigParser.SafeConfigParser()
        config.read([args.config])
        defaults = dict(config.items('Defaults') + config.items("Selfstats"))

    parser = argparse.ArgumentParser(description="""Calculate statistics on selfspy data. Per default it will show non-text information that matches the filter. Adding '-s' means also show text. Adding any of the summary options will show those summaries over the given filter instead of the listing. Multiple summary options can be given to print several summaries over the same filter. If you give arguments that need to access text / keystrokes, you will be asked for the decryption password.""", epilog="""See the README file or http://gurgeh.github.com/selfspy for examples.""", parents=[conf_parser])
    parser.set_defaults(**defaults)
    parser.add_argument('-p', '--password', help='Decryption password. Only needed if selfstats needs to access text / keystrokes data. If your database in not encrypted, specify -p="" here. If you don\'t specify a password in the command line arguments or in a config file, and the statistics you ask for require a password, a dialog will pop up asking for the password. If you give your password on the command line, remember that it will most likely be stored in plain text in your shell history.')
    parser.add_argument('-d', '--data-dir', help='Data directory for selfspy, where the database is stored. Remember that Selfspy must have read/write access. Default is %s' % cfg.DATA_DIR, default=cfg.DATA_DIR)

    parser.add_argument('-s', '--showtext', action='store_true', help='Also show the text column. This switch is ignored if at least one of the summary options are used. Requires password.')

    parser.add_argument('-D', '--date', nargs='+', help='Which date to start the listing or summarizing from. If only one argument is given (--date 13) it is interpreted as the closest date in the past on that day. If two arguments are given (--date 03 13) it is interpreted as the closest date in the past on that month and that day, in that order. If three arguments are given (--date 2012 03 13) it is interpreted as YYYY MM DD')
    parser.add_argument('-C', '--clock', type=str, help='Time to start the listing or summarizing from. Given in 24 hour format as --clock 13:25. If no --date is given, interpret the time as today if that results in sometimes in the past, otherwise as yesterday.')

    parser.add_argument('-i', '--id', type=int, help='Which row ID to start the listing or summarizing from. If --date and/or --clock is given, this option is ignored.')

    parser.add_argument('-b', '--back', nargs='+', type=str, help='--back <period> [<unit>] Start the listing or summary this much back in time. Use this as an alternative to --date, --clock and --id. If any of those are given, this option is ignored. <unit> is either "s" (seconds), "m" (minutes), "h" (hours), "d" (days) or "w" (weeks). If no unit is given, it is assumed to be hours.')

    parser.add_argument('-l', '--limit', help='--limit <period> [<unit>]. If the start is given in --date/--clock, the limit is a time period given by <unit>. <unit> is either "s" (seconds), "m" (minutes), "h" (hours), "d" (days) or "w" (weeks). If no unit is given, it is assumed to be hours. If the start is given with --id, limit has no unit and means that the maximum row ID is --id + --limit.', nargs='+', type=str)

    parser.add_argument('-m', '--min-keys', type=int, metavar='nr', help='Only allow entries with at least <nr> keystrokes')

    parser.add_argument('-T', '--title', type=str, metavar='regexp', help='Only allow entries where a search for this <regexp> in the window title matches something. All regular expressions are case insensitive.')
    parser.add_argument('-P', '--process', type=str, metavar='regexp', help='Only allow entries where a search for this <regexp> in the process matches something.')
    parser.add_argument('-B', '--body', type=str, metavar='regexp', help='Only allow entries where a search for this <regexp> in the body matches something. Do not use this filter when summarizing ratios or activity, as it has no effect on mouse clicks. Requires password.')

    parser.add_argument('--clicks', action='store_true', help='Summarize number of mouse button clicks for all buttons.')

    parser.add_argument('--key-freqs', action='store_true', help='Summarize a table of absolute and relative number of keystrokes for each used key during the time period. Requires password.')

    parser.add_argument('--human-readable', action='store_true', help='This modifies the --body entry and honors backspace.')
    parser.add_argument('--active', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='Summarize total time spent active during the period. The optional argument gives how many seconds after each mouse click (including scroll up or down) or keystroke that you are considered active. Default is %d.' % ACTIVE_SECONDS)

    parser.add_argument('--ratios', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='Summarize the ratio between different metrics in the given period. "Clicks" will not include up or down scrolling. The optional argument is the "seconds" cutoff for calculating active use, like --active.')

    parser.add_argument('--periods', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List active time periods. Optional argument works same as for --active.')

    parser.add_argument('--pactive', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List processes, sorted by time spent active in them. Optional argument works same as for --active.')
    parser.add_argument('--tactive', type=int, metavar='seconds', nargs='?', const=ACTIVE_SECONDS, help='List window titles, sorted by time spent active in them. Optional argument works same as for --active.')

    parser.add_argument('--pkeys', action='store_true', help='List processes sorted by number of keystrokes.')
    parser.add_argument('--tkeys', action='store_true', help='List window titles sorted by number of keystrokes.')

    return parser.parse_args()


def make_encrypter(password):
    if password == "":
        encrypter = None
    else:
        encrypter = Blowfish.new(hashlib.md5(password).digest())
    return encrypter


def main():
    try:
        args = vars(parse_config())
    except EnvironmentError as e:
        print str(e)
        sys.exit(1)

    args['data_dir'] = os.path.expanduser(args['data_dir'])

    def check_with_encrypter(password):
        encrypter = make_encrypter(password)
        return check_password.check(args['data_dir'], encrypter, read_only=True)

    ss = Selfstats(os.path.join(args['data_dir'], cfg.DBNAME), args)

    if ss.need_text or ss.need_keys:
        if args['password'] is None:
            args['password'] = get_password(verify=check_with_encrypter)

        models.ENCRYPTER = make_encrypter(args['password'])

        if not check_password.check(args['data_dir'], models.ENCRYPTER, read_only=True):
            print 'Password failed'
            sys.exit(1)

    ss.do()


if __name__ == '__main__':
    main()
