import time
import os
import sys
from datetime import datetime
NOW = datetime.now
import struct


import daemon
import lockfile
import signal

import Xlib.error

import hook_manager
import models
from models import Process, Window, Geometry, Click, Keys

SKIP_SET = {'Shift_L', 'Shift_R'}

HOME_DIR = '/var/lib/selfspy'
DBNAME = 'selfspy.sqlite'
LOCK_FILE = '/var/run/selfspy/selfspy.pid'

"""
Todo:
  argparse

  set password
  choose HOME_DIR
  choose LOCK_FILE
-
  change name to selfspy 
-
  proper logging
- 
  make unthreaded
--
  optional crypto on Keys.text and Keys.timings
  timings in json
  compress text and timings (check size difference on existing db)
  ask for pw in tk, if not command line
--
  simple utility for reading and stats
--
  README
-
  test map switch
  general testing
  no printing
-


---Later
  documentation, unittests, pychecker ;)
  replay key and mouse for process and time interval (maybe store as macro)
  word search

"""


#Mouse buttons: left button: 1, middle: 2, right: 3, scroll up: 4, down:5


class Spook:
    def __init__(self):
        self.session_maker = None
        self.session = None

        self.nrmoves = 0
        self.latestx = 0
        self.latesty = 0
        self.lastspecial = None
        self.specials_in_row = 0

        self.curtext = u""
        self.timings = []
        
        self.started = NOW()
        self.cur_class = None
        self.cur_window = None
        self.cur_name = None
        self.cur_process_id = None
        self.cur_win_id = None

    def run(self):
        self.hm = hook_manager.HookManager()
        self.log_cur_window()
        self.hm.key_hook = self.got_key
        self.hm.mouse_button_hook = self.got_mouse_click
        self.hm.mouse_move_hook = self.got_mouse_move

        self.hm.start()

    def close(self):
        self.hm.cancel()

    def store_window(self):
        cur_window = self.session.query(Window).filter_by(title=self.cur_name.decode('latin1'), process_id=self.cur_process_id).scalar()
        if cur_window is None:
            cur_window = Window(self.cur_name.decode('latin1'), self.cur_process_id)
            self.session.add(cur_window)
            self.session.commit()

        self.cur_win_id = cur_window.id

    def maybe_end_specials(self):
        if self.specials_in_row == 1:
            self.curtext += '>'
        elif self.specials_in_row > 1:
            self.curtext += 'x%d>' % self.specials_in_row
        self.specials_in_row = 0
        self.lastspecial = None

    def store_click(self, button, press):
        if press:
            print 'mouse', button, self.nrmoves
        self.session.add(Click(button, press, self.latestx, self.latesty, self.nrmoves, self.cur_win_id, self.cur_geo_id))
        self.session.commit()
        self.nrmoves = 0

    def store_keys(self):
        if self.timings:
            self.maybe_end_specials()
            print 'keys', len(self.timings)

            self.session.add(Keys(self.curtext, self.timings, self.started, self.cur_win_id, self.cur_geo_id))
            self.session.commit()

            self.started = NOW()
            self.curtext = u""
            self.timings = []

    def get_cur_window(self):
        i = 0
        while True:
            try:
                cur_window = self.hm.the_display.get_input_focus().focus
                cur_class = None
                cur_name = None
                while cur_class is None and cur_class is None:
                    if type(cur_window) is int:
                        print 'int?'
                        return None, None, None
            
                    cur_name = cur_window.get_wm_name()
                    cur_class = cur_window.get_wm_class()
                    if cur_class is None:
                        cur_window = cur_window.query_tree().parent
            except Xlib.error.BadWindow:
                print 'Badwin'
                i += 1
                if i >= 10:
                    print 'Really bad win..'
                    return None, None, None
                continue
            break
        return cur_class[1], cur_window, cur_name
        

    def check_geometry(self):
        geo = self.cur_window.get_geometry()
        cur_geo = self.session.query(Geometry).filter_by(xpos=geo.x, ypos=geo.y, width=geo.width, height=geo.height).scalar()
        if cur_geo is None:
            cur_geo = Geometry(geo)
            self.session.add(cur_geo)
            self.session.commit()
        self.cur_geo_id = cur_geo.id

    def log_cur_window(self):
        cur_class, cur_window, cur_name = self.get_cur_window()
        if cur_class is None: return

        self.session = self.session_maker()

        if cur_class != self.cur_class:
            self.cur_class = cur_class
            proc_name = self.cur_class.decode('latin1')
            cur_process = self.session.query(Process).filter_by(name=proc_name).scalar()
            if cur_process is None:
                cur_process = Process(proc_name)
                self.session.add(cur_process)
                self.session.commit()
            
            self.cur_process_id = cur_process.id
            

        if cur_window != self.cur_window or cur_name != self.cur_name:
            self.cur_window = cur_window
            self.cur_name = cur_name
            self.store_keys()
            self.store_window()

        self.check_geometry()

    def got_key(self, keycode, state, s, press):
        self.log_cur_window()
        if press:
            if s not in SKIP_SET and not (s[0] == '[' and s[-1] == ']'):
                if len(s) == 1:
                    self.maybe_end_specials()
                    self.curtext += s
                else:
                    if self.lastspecial != s:
                        self.maybe_end_specials()
                        self.curtext += '<[%s]' % s
                        self.specials_in_row = 1
                    else:
                        self.specials_in_row += 1
                    self.lastspecial = s
            if self.specials_in_row < 2:
                self.timings.append((s, time.time()))

    def got_mouse_click(self, button, press):
        self.log_cur_window()
        self.store_click(button, press)
        if not (press or button in [4,5]):
            self.store_keys()

    def got_mouse_move(self, x, y):
        self.nrmoves += 1
        self.latestx = x
        self.latesty = y

if __name__ == '__main__':
    spook = Spook()

    lock = lockfile.FileLock(LOCK_FILE)
    if lock.is_locked():
        print '%s is locked! I am probably already running.' % LOCK_FILE #log!
        print 'If you can find no selfspy process running, it is a stale lock and you can safely remove it.'
        print 'Shutting down.'
        sys.exit()

    context = daemon.DaemonContext(
        working_directory=HOME_DIR,
        pidfile=lock,
        stdout = sys.stdout,
        stderr = sys.stderr
    )

    context.signal_map = {
        signal.SIGTERM: 'terminate',
        signal.SIGHUP: 'terminate'
    }
    
    try:
        with context:
            spook.session_maker = models.initialize(os.path.join(HOME_DIR, DBNAME))
            spook.run()
            while True:
                time.sleep(1000000000)
    except SystemExit:
        spook.close()


