import time
from datetime import datetime
NOW = datetime.now
import struct

import Xlib.error

import hook_manager
from models import Process, Window, Focus, Session

"""
Todo:
  test map switch

  document
  simple utility for reading and stats
---Later

  word search
  optional crypto
"""

"""
        if event.detail == 1:
            MessageName = "mouse left "
        elif event.detail == 3:
            MessageName = "mouse right "
        elif event.detail == 2:
            MessageName = "mouse middle "
        elif event.detail == 5:
            MessageName = "mouse wheel down "
        elif event.detail == 4:
            MessageName = "mouse wheel up "
"""

class Spook:
    def __init__(self):
        self.session = None

        self.nrmoves = 0

        self.curtext = u""
        self.mousing = []
        self.timings = []
        
        self.started = NOW()
        self.cur_class = None
        self.cur_window = None
        self.cur_name = None
        self.cur_process_id = None
        self.cur_win_id = None

        self.hm = hook_manager.HookManager()
        self.log_cur_window()
        self.hm.key_hook = self.got_key
        self.hm.mouse_button_hook = self.got_mouse_click
        self.hm.mouse_move_hook = self.got_mouse_move

        self.log_cur_window()
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

    def store_focus(self, new_win=False):
        if self.timings or (self.mousing and new_win):
            print len(self.timings), len(self.mousing)
            geo = self.cur_window.get_geometry()
            self.session.add(Focus(self.curtext, self.timings, self.started, self.cur_win_id, self.mousing,
                                   geo.x, geo.y, geo.width, geo.height))
            self.session.commit()

            self.started = NOW()
            self.curtext = u""
            self.timings = []
            self.mousing = []

    def log_cur_window(self):
        self.session = Session()

        i = 0
        while True:
            try:
                cur_window = self.hm.the_display.get_input_focus().focus
                cur_class = None
                cur_name = None
                while cur_class is None and cur_class is None:
                    if type(cur_window) is int:
                        print 'int?'
                        return
            
                    cur_name = cur_window.get_wm_name()
                    cur_class = cur_window.get_wm_class()
                    if cur_class is None:
                        cur_window = cur_window.query_tree().parent
            except Xlib.error.BadWindow:
                print 'Badwin'
                i += 1
                if i >= 10:
                    print 'Really bad win..'
                    return
                continue
            break
        cur_class = cur_class[1]

        if cur_class != self.cur_class:
            self.cur_class = cur_class
            cur_process = self.session.query(Process).filter_by(name=self.cur_class.decode('latin1')).scalar()
            if cur_process is None:
                cur_process = Process(self.cur_class.decode('latin1'))
                self.session.add(cur_process)
                self.session.commit()
            
            self.cur_process_id = cur_process.id
            

        if cur_window != self.cur_window or cur_name != self.cur_name:
            self.cur_window = cur_window
            self.cur_name = cur_name
            self.store_focus(new_win=True)
            self.store_window()

    def got_key(self, keycode, state, s, press):
        self.log_cur_window()
        if press:
            if len(s) == 1:
                self.curtext += s
            self.timings.append((s, time.time()))

    def got_mouse_click(self, button, press):
        self.log_cur_window()
        self.mousing.append((button, time.time()))
        if not (press or button in [4,5]):
            self.store_focus()

    def got_mouse_move(self, x, y):
        self.nrmoves += 1
        self.mousing.append((x,y, time.time()))

if __name__ == '__main__':
    spook = Spook()

    try:
        time.sleep(1000000000)
    except KeyboardInterrupt:
        pass

    spook.close()
