import time
from datetime import datetime
NOW = datetime.now

import Xlib.error
import sqlalchemy

import sniff_x
import models
from models import Process, Window, Geometry, Click, Keys

SKIP_SET = {'Shift_L', 'Shift_R'}

#Mouse buttons: left button: 1, middle: 2, right: 3, scroll up: 4, down:5

class KeyPress:
    def __init__(self, key, time, is_repeat):
        self.key = key
        self.time = time
        self.is_repeat = is_repeat

class ActivityStore:
    def __init__(self, db_name, encrypter=None, store_text=True):
        self.session_maker = models.initialize(db_name)
        self.session = None

        models.ENCRYPTER = encrypter

        self.store_text = store_text

        self.nrmoves = 0
        self.latestx = 0
        self.latesty = 0
        self.lastspecial = None
        self.specials_in_row = 0

        self.curtext = u""
        self.key_presses = []
        self.last_key_time = time.time()
        
        self.started = NOW()
        self.cur_class = None
        self.cur_window = None
        self.cur_name = None
        self.cur_process_id = None
        self.cur_win_id = None
        self.cur_win_proc = None

    def trycommit(self):
        for _ in xrange(1000):
            try:
                self.session.commit()
                break
            except sqlalchemy.exc.OperationalError:
                time.sleep(1)

    def run(self):
        self.sniffer = sniff_x.SniffX()
        self.log_cur_window()
        self.sniffer.key_hook = self.got_key
        self.sniffer.mouse_button_hook = self.got_mouse_click
        self.sniffer.mouse_move_hook = self.got_mouse_move

        self.sniffer.run()

    def close(self):
        self.sniffer.cancel()
        self.store_keys()

    def store_window(self):
        cur_window = self.session.query(Window).filter_by(title=self.cur_name.decode('latin1'), process_id=self.cur_process_id).scalar()
        if cur_window is None:
            cur_window = Window(self.cur_name.decode('latin1'), self.cur_process_id)
            self.session.add(cur_window)
            self.trycommit()

        self.cur_win_id = cur_window.id
        self.cur_process_id = cur_window.process_id
        self.cur_win_proc = cur_window.process_id

    def maybe_end_specials(self):
        if self.specials_in_row == 1:
            self.curtext += '>'
        elif self.specials_in_row > 1:
            self.curtext += 'x%d>' % self.specials_in_row
        self.specials_in_row = 0
        self.lastspecial = None

    def store_click(self, button, press):
        if press:
            self.session.add(Click(button, press, self.latestx, self.latesty, self.nrmoves, self.cur_win_proc, self.cur_win_id, self.cur_geo_id))
        self.trycommit()
        self.nrmoves = 0

    def store_keys(self):
        if self.key_presses:
            self.maybe_end_specials()
            
            keys = [press.key for press in self.key_presses]
            timings = [press.time for press in self.key_presses]

            nrkeys = reduce(lambda count, press: count + (not press.is_repeat and 1 or 0), self.key_presses, 0)

            if not self.store_text:
                keys = []
                self.curtext = u""
            
            self.session.add(Keys(self.curtext.encode('utf8'), keys, timings, nrkeys, self.started, self.cur_win_proc, self.cur_win_id, self.cur_geo_id))

            self.trycommit()

            self.started = NOW()
            self.curtext = u""
            self.key_presses = []
            self.last_key_time = time.time()

    def get_cur_window(self):
        i = 0
        while True:
            try:
                cur_window = self.sniffer.the_display.get_input_focus().focus
                cur_class = None
                cur_name = None
                while cur_class is None and cur_class is None:
                    if type(cur_window) is int:
                        return None, None, None
            
                    cur_name = cur_window.get_wm_name()
                    cur_class = cur_window.get_wm_class()
                    if cur_class is None:
                        cur_window = cur_window.query_tree().parent

            except Xlib.error.XError:
                i += 1
                if i >= 10:
                    return None, None, None
                continue
            break
        return cur_class[1], cur_window, cur_name
        

    def check_geometry(self):
        i = 0
        while True:
            try:
                geo = self.cur_window.get_geometry()
                break
            except Xlib.error.XError:
                i += 1
                if i >= 10:
                    return
            
        cur_geo = self.session.query(Geometry).filter_by(xpos=geo.x, ypos=geo.y, width=geo.width, height=geo.height).scalar()
        if cur_geo is None:
            cur_geo = Geometry(geo)
            self.session.add(cur_geo)
            self.trycommit()
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
                self.trycommit()
            
            self.cur_process_id = cur_process.id
            

        if cur_window != self.cur_window or cur_name != self.cur_name:
            self.cur_window = cur_window
            self.cur_name = cur_name
            self.store_keys()
            self.store_window()

        self.check_geometry()

    def got_key(self, keycode, state, s, press, repeat):
        now = time.time()
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
                self.key_presses.append(KeyPress(s, now - self.last_key_time, repeat))
                self.last_key_time = now

    def got_mouse_click(self, button, press):
        self.log_cur_window()
        self.store_click(button, press)
        if not (press or button in [4,5]):
            self.store_keys()

    def got_mouse_move(self, x, y):
        self.nrmoves += 1
        self.latestx = x
        self.latesty = y

    def change_password(self, new_encrypter):
        self.session = self.session_maker()
        keys = self.session.query(Keys).all()
        for k in keys:
            dtext = k.decrypt_text()
            dkeys = k.decrypt_keys()
            k.encrypt_text(dtext, new_encrypter)
            k.encrypt_keys(dkeys, new_encrypter)
        self.session.commit()
