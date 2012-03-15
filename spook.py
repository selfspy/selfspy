import time

import hook_manager

"""
Todo:
 test map switch

 real log format
  one dump file per class
  tight struct.pack dump format
  dump file stores seek-index in separate file for each hour
  flush every 60(?) seconds

word search
  add inverted word index for each file (word->[pos])
   bdb? something more stable?

---Later
  utility for reading and stats
  crypto
"""

WIN_PREFIX = 0 #class, title, geo, time
KEY_PREFIX = 1 #keycode,state,c, press, time
MOUSE_CLICK_PREFIX = 2 #button, press, time
MOUSE_MOVE_PREFIX = 3 #[(coord, time)..]

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

        self.hm = hook_manager.HookManager()
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

        if cur_window == self.cur_window:
            if cur_name != self.cur_name:
                self.cur_name = cur_name
                print 'name', self.cur_name
                #binlog
        else:
            self.cur_window = cur_window
            self.cur_name = cur_name
            geo = cur_window.get_geometry()
            print 'win', cur_window.get_wm_class(), self.cur_name, (geo.x, geo.y, geo.width, geo.height), cur_window.id
            #binlog


    def got_key(self, keycode, state, s, press):
        self.log_cur_window()
        if press:
            print keycode, state, s
        #binlog


    def got_mouse_click(self, button, press):
        self.log_cur_window()
        if press:
            print 'click', button, self.nrmoves
        #binlog

    def got_mouse_move(self, x, y):
        self.nrmoves += 1
        #binlog

if __name__ == '__main__':
    spook = Spook('output.log')

    try:
        time.sleep(1000000000)
    except KeyboardInterrupt:
        pass

    spook.close()
