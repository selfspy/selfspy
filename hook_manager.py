#    This file is loosely based on pyxhook.py by 
#    Tim Alexander <dragonfyre13@gmail.com> and Daniel Folkinshteyn <nanotube@users.sf.net>
#    but almost nothing remains of the original code

import sys
import os
import re
import time
import threading

from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq

def state_to_idx(state): #this could be a dict, but after improvements a dict will not be enough
    if state == 1: return 1
    if state == 128: return 4
    if state == 129: return 5
    return 0

class HookManager(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.finished = threading.Event()

        self.keysymdict = {}
        for name in dir(XK):
            if name.startswith("XK_"):
                self.keysymdict[getattr(XK, name)] = name[3:]
        
        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True

        self.contextEventMask = [X.KeyPress, X.MotionNotify] #X.MappingNotify?
        
        self.the_display = display.Display()
        self.record_display = display.Display()
        self.keymap = self.the_display._keymap_codes
        
    def run(self):
        # Check if the extension is present
        if not self.record_display.has_extension("RECORD"):
            print "RECORD extension not found"
            sys.exit(1)
        else:
            print "RECORD extension present"

        # Create a recording context; we only want key and mouse events
        self.ctx = self.record_display.record_create_context(
                0,
                [record.AllClients],
                [{
                        'core_requests': (0, 0),
                        'core_replies': (0, 0),
                        'ext_requests': (0, 0, 0, 0),
                        'ext_replies': (0, 0, 0, 0),
                        'delivered_events': (0, 0),
                        'device_events': tuple(self.contextEventMask),
                        'errors': (0, 0),
                        'client_started': False,
                        'client_died': False,
                }])

        # Enable the context; this only returns after a call to record_disable_context,
        # while calling the callback function in the meantime
        self.record_display.record_enable_context(self.ctx, self.processevents)
        # Finally free the context
        self.record_display.record_free_context(self.ctx)

    def cancel(self):
        self.finished.set()
        self.the_display.record_disable_context(self.ctx)
        self.the_display.flush()
    
    def processevents(self, reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            print "* received swapped protocol data, cowardly ignored"
            return
        if not len(reply.data) or ord(reply.data[0]) < 2:
            # not an event
            return
        data = reply.data
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, self.record_display.display, None, None)
            if event.type in [X.KeyPress, X.KeyRelease]:
                self.key_hook(*self.key_event(event))
            elif event.type in [X.ButtonPress, X.ButtonRelease]:
                self.mouse_button_hook(*self.button_event(event))
            elif event.type == X.MotionNotify:
                self.mouse_move_hook(event.root_x, event.root_y)
            elif event.type == X.MappingNotify:
                self.the_display.refresh_keyboard_mapping()
                newkeymap = self.the_display._keymap_codes
                print 'Change keymap!', newkeymap == self.keymap
                self.keymap = newkeymap
                

    def get_key_name(self, keycode, state):
        state_idx = state_to_idx(state)
        cn = self.keymap[keycode][state_idx]
        if cn < 256:
            return chr(cn).decode('latin1')#.encode('utf8')
        else:
            return self.lookup_keysym(cn)

    def key_event(self, event):
        return event.detail, event.state, self.get_key_name(event.detail, event.state), event.type == X.KeyPress
    
    def button_event(self, event):
        return event.detail, event.type == X.ButtonPress

    def lookup_keysym(self, keysym):
        if keysym in self.keysymdict:
            return self.keysymdict[keysym]
        return "[%d]" % keysym

    


