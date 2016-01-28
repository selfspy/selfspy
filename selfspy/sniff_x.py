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


# This file is loosely based on examples/record_demo.py in python-xlib

import sys

from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.error import XError
from Xlib.protocol import rq


def state_to_idx(state):  # this could be a dict, but I might want to extend it.
    if state == 1:
        return 1
    if state == 128:
        return 4
    if state == 129:
        return 5
    return 0


class Sniffer:
    def __init__(self):
        self.keysymdict = {}
        for name in dir(XK):
            if name.startswith("XK_"):
                self.keysymdict[getattr(XK, name)] = name[3:]

        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.screen_hook = lambda x: True

        self.contextEventMask = [X.KeyPress, X.MotionNotify]

        self.the_display = display.Display()
        self.record_display = display.Display()
        self.keymap = self.the_display._keymap_codes

        self.atom_NET_WM_NAME = self.the_display.intern_atom('_NET_WM_NAME')
        self.atom_UTF8_STRING = self.the_display.intern_atom('UTF8_STRING')

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

        cur_class, cur_window, cur_name = self.get_cur_window()
        if cur_class:
            cur_geo = self.get_geometry(cur_window)
            if cur_geo:
                self.screen_hook(cur_class,
                                 cur_name,
                                 cur_geo.x,
                                 cur_geo.y,
                                 cur_geo.width,
                                 cur_geo.height)

        data = reply.data
        while len(data):
            ef = rq.EventField(None)
            event, data = ef.parse_binary_value(data, self.record_display.display, None, None)
            if event.type in [X.KeyPress]:
                # X.KeyRelease, we don't log this anyway
                self.key_hook(*self.key_event(event))
            elif event.type in [X.ButtonPress]:
                # X.ButtonRelease we don't log this anyway.
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
            return chr(cn).decode('latin1')
        else:
            return self.lookup_keysym(cn)

    def key_event(self, event):
        flags = event.state
        modifiers = []
        if flags & X.ControlMask:
            modifiers.append('Ctrl')
        if flags & X.Mod1Mask:  # Mod1 is the alt key
            modifiers.append('Alt')
        if flags & X.Mod4Mask:  # Mod4 should be super/windows key
            modifiers.append('Super')
        if flags & X.ShiftMask:
            modifiers.append('Shift')
        return (event.detail,
                modifiers,
                self.get_key_name(event.detail, event.state),
                event.sequence_number == 1)

    def button_event(self, event):
        return event.detail, event.root_x, event.root_y

    def lookup_keysym(self, keysym):
        if keysym in self.keysymdict:
            return self.keysymdict[keysym]
        return "[%d]" % keysym

    def get_wm_name(self, win):
        """
        Custom method to query for _NET_WM_NAME first, before falling back to
        python-xlib's method, which (currently) only queries WM_NAME with
        type=STRING."""

        # Alternatively, we could also try WM_NAME with "UTF8_STRING" and
        # "COMPOUND_TEXT", but _NET_WM_NAME should be good.

        d = win.get_full_property(self.atom_NET_WM_NAME, self.atom_UTF8_STRING)
        if d is None or d.format != 8:
            # Fallback.
            r = win.get_wm_name()
            if r:
                return r.decode('latin1')  # WM_NAME with type=STRING.
        else:
            # Fixing utf8 issue on Ubuntu (https://github.com/gurgeh/selfspy/issues/133)
            # Thanks to https://github.com/gurgeh/selfspy/issues/133#issuecomment-142943681
            try:
                return d.value.decode('utf8')
            except UnicodeError:
                return d.value.encode('utf8').decode('utf8')

    def get_cur_window(self):
        i = 0
        cur_class = None
        cur_window = None
        cur_name = None
        while i < 10:
            try:
                cur_window = self.the_display.get_input_focus().focus
                cur_class = None
                cur_name = None
                while cur_class is None:
                    if type(cur_window) is int:
                        return None, None, None

                    cur_name = self.get_wm_name(cur_window)
                    cur_class = cur_window.get_wm_class()

                    if cur_class:
                        cur_class = cur_class[1]
                    if not cur_class:
                        cur_window = cur_window.query_tree().parent
            except XError:
                i += 1
                continue
            break
        cur_class = cur_class or ''
        cur_name = cur_name or ''
        return cur_class.decode('latin1'), cur_window, cur_name

    def get_geometry(self, cur_window):
        i = 0
        geo = None
        while i < 10:
            try:
                geo = cur_window.get_geometry()
                break
            except XError:
                i += 1
        return geo
