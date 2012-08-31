import time
from datetime import datetime
NOW = datetime.now

import sqlalchemy

import platform
if platform.system() == 'Darwin':
    import sniff_cocoa
else:
    import sniff_x

import models
from models import Process, Window, Geometry, Click, Keys

class Display:
    def __init__(self):
         self.proc_id = None
         self.win_id = None 
         self.geo_id = None

class KeyPress:
    def __init__(self, key, time, is_repeat):
        self.key = key
        self.time = time
        self.is_repeat = is_repeat

class ActivityStore:
    def __init__(self, db_name, encrypter=None, store_text=True):
        self.session_maker = models.initialize(db_name)

        models.ENCRYPTER = encrypter

        self.store_text = store_text
        self.curtext = u""

        self.key_presses = []
        self.mouse_path = []

        self.current_window = Display()

        self.last_key_time = time.time()        
        self.started = NOW()

    def trycommit(self):
        for _ in xrange(1000):
            try:
                self.session.commit()
                break
            except sqlalchemy.exc.OperationalError:
                time.sleep(1)

    def run(self):
        self.session = self.session_maker()

        if platform.system() == 'Darwin':
            self.sniffer = sniff_cocoa.SniffCocoa()
        else:
            self.sniffer = sniff_x.SniffX()
        self.sniffer.screen_hook = self.got_screen_change
        self.sniffer.key_hook = self.got_key
        self.sniffer.mouse_button_hook = self.got_mouse_click
        self.sniffer.mouse_move_hook = self.got_mouse_move

        self.sniffer.run()

    def got_screen_change(self, process_name, window_name, win_x, win_y, win_width, win_height):
        """ Recieves a screen change and stores any changes. If the process or window has
            changed it will also store any queued pressed keys.
            process_name is the name of the process running the current window
            window_name is the name of the window 
            win_x is the x position of the window
            win_y is the y position of the window
            win_width is the width of the window
            win_height is the height of the window """
        cur_process = self.session.query(Process).filter_by(name=process_name).scalar()
        if cur_process is None:
            cur_process = Process(process_name)
            self.session.add(cur_process)
            
        cur_geometry = self.session.query(Geometry).filter_by(xpos=win_x, 
                                                              ypos=win_y, 
                                                              width=win_width, 
                                                              height=win_height).scalar()
        if cur_geometry is None:
            cur_geometry = Geometry(win_x, win_y, win_width, win_height)
            self.session.add(cur_geometry)
        
        cur_window = self.session.query(Window).filter_by(title=window_name,
                                                          process_id=cur_process.id).scalar()
        if cur_window is None:
            cur_window = Window(window_name, cur_process.id)
            self.session.add(cur_window)

        if (self.current_window.proc_id != cur_process.id or 
            self.current_window.win_id != cur_window.id):
            self.store_keys() # happens before as these keypresses belong to the previous window
            self.current_window.proc_id = cur_process.id
            self.current_window.win_id = cur_window.id
            self.current_window.geo_id = cur_geometry.id
            
        self.trycommit()


    def store_keys(self):
        """ Stores the current queued key-presses """
        if self.key_presses:
            keys = [press.key for press in self.key_presses]
            timings = [press.time for press in self.key_presses]
            add = lambda count, press: count + (not press.is_repeat and 1 or 0)
            nrkeys = reduce(add, self.key_presses, 0)
            
            curtext = u""
            if not self.store_text:
                keys = []
            else:
                for key in keys:
                    curtext += key

            self.session.add(Keys(curtext.encode('utf8'), 
                                  keys,
                                  timings,
                                  nrkeys,
                                  self.started,
                                  self.current_window.proc_id,
                                  self.current_window.win_id,
                                  self.current_window.geo_id))

            self.trycommit()

            self.started = NOW()
            self.key_presses = []
            self.last_key_time = time.time()
    
    def got_key(self, keycode, state, string, is_repeat):
        """ Recieves key-presses and queues them for storage.
            keycode is the code sent by the keyboard to represent the pressed key
            state is the list of modifier keys pressed, each modifier key should be represented
                  with capital letters and optionally followed by an underscore and location
                  specifier, i.e: SHIFT or SHIFT_L/SHIFT_R, ALT, CTRL
            string is the string representation of the key press
            repeat is True if the current key is a repeat sent by the keyboard """
        now = time.time()
        if string and (len(state) == 1) and (state[0] in ['SHIFT' ,'SHIFT_L', 'SHIFT_R']):
            self.key_presses.append(KeyPress(string, now - self.last_key_time, is_repeat))
            self.last_key_time = now
        else:
            s = string
            for modifier in state:
                s = '<['+modifier+'] ' + s +'>'
            self.key_presses.append(KeyPress(s, now - self.last_key_time, is_repeat))
            self.last_key_time = now

    def store_click(self, button, x, y):
        """ Stores incoming mouse-clicks """
        self.session.add(Click(button, 
                               True, 
                               x, y,
                               len(self.mouse_path),
                               self.current_window.proc_id,
                               self.current_window.win_id, 
                               self.current_window.geo_id))
        self.mouse_path = []
        self.trycommit()

    def got_mouse_click(self, button, x, y):
        """ Recieves mouse clicks and sends them for storage.
            Mouse buttons: left: 1, middle: 2, right: 3, scroll up: 4, down:5, left:6, right:7
            x,y are the coordinates of the keypress
            press is True if it pressed down, False if released"""
        self.store_click(button, x, y)

    def got_mouse_move(self, x, y):
        """ Queues mouse movements.
            x,y are the new coorinates on moving the mouse"""
        self.mouse_path.append([x,y])
        
    def close(self):
        """ stops the sniffer and stores the latest keys. To be used on shutdown of program"""
        self.sniffer.cancel()
        self.store_keys()

