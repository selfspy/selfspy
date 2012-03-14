import time

import hook_manager

"""
Todo:
 test run
 test map switch

 real log format

Bugs:
 why win=None sometimes?
"""

WIN_PREFIX = 0
KEY_PREFIX = 1
MOUSE_PREFIX = 2

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
    def __init__(self, fname):
        self.f = open(fname, 'ab+')

        self.nrmoves = 0

        self.hm = pyxhook.HookManager()
        self.cur_window = None
        self.cur_name = None
        self.log_cur_window()
        self.hm.key_hook = self.got_key
        self.hm.mouse_button_hook = self.got_mouse_click
        self.hm.mouse_move_hook = self.got_mouse_move
        self.hm.start()

    def close(self):
        self.hm.cancel()
        self.f.close()

    def log_cur_window(self):
        cur_window = self.hm.local_dpy.get_input_focus().focus
        cur_name = cur_window.get_wm_name()
        if cur_window == self.cur_window:
            if cur_name != self.cur_name:
                self.cur_name = cur_name
                print 'name', self.cur_name
                #binlog
        else:
            self.cur_window = cur_window
            self.cur_name = cur_name
            print 'win', self.cur_name
            #binlog


    def got_key(self, keycode, state, s):
        self.log_cur_window()
        if press:
            print keycode, state, s
        #binlog


    def got_mouse_click(self, button, press, t):
        self.log_cur_window()
        if press:
            print 'click', button, (t, time.time()), self.nrmoves
        #binlog

    def got_mouse_move(self, x, y):
        self.nrmoves += 1
        #binlog

if __name__ == '__main__':
    spook = Spook('output.log')
    try:
        time.sleep(1000000000)
    except:
        pass
    spook.close()
