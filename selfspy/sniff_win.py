# -*- coding: utf-8 -*-
# Copyright 2012 Morten Linderud

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

import pyHook
import pythoncom
import sys
import threading
import ctypes


class SnifferThread(threading.Thread):
    def __init__(self, hook):
        threading.Thread.__init__(self)
        self.daemon = True
        self.encoding = sys.stdin.encoding
        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.screen_hook = lambda x: True
        self.remap = {
                248: u"\xf8",
                216: u"\xd8",
                230: u"\xe6",
                198: u"\xc6",
                229: u"\xe5",
                197: u"\xc5"
                }
        self.hm = hook

    def run(self):
        self.hm.KeyDown = self.KeyboardEvent
        self.hm.MouseAllButtonsDown = self.MouseButtons
        self.hm.MouseMove = self.MouseMove
        self.hm.HookKeyboard()
        self.hm.HookMouse()
        pythoncom.PumpMessages()


    def MouseButtons(self, event):
        loc = event.Position
        if event.MessageName == "mouse right down":
            self.mouse_button_hook(3, loc[0], loc[1],)
        if event.MessageName == "mouse left down":
            self.mouse_button_hook(1, loc[0], loc[1])
        if event.MessageName == "mouse middle down":
            self.mouse_button_hook(2, loc[0], loc[1])
        try:
            string_event = event.WindowName.decode(self.encoding)
        except AttributeError:
            string_event = ""
        self.screen_hook(str(event.Window), string_event, loc[0], loc[1], 0, 0)
        return True

    def MouseMove(self, event):
        loc = event.Position
        if event.MessageName == "mouse move":
            self.mouse_move_hook(loc[0], loc[1])
        if event.MessageName == "mouse wheel":
            if event.Wheel == -1:
                self.mouse_button_hook(5, loc[0], loc[1],)
            elif event.Wheel == 1:
                self.mouse_button_hook(4, loc[0], loc[1],)
        return True

    def KeyboardEvent(self, event):
        modifiers = []
        if event.Key in ["Lshift", "Rshift"]:
            modifiers.append('Shift')
        elif event.Key in ["Lmenu", "Rmenu"]:
            modifiers.append('Alt')
        elif event.Key in ["Rcontrol", "Lcontrol"]:
            modifiers.append('Ctrl')
        elif event.Key in ["Rwin", "Lwin"]:
            modifiers.append('Super')
        if event.Ascii in self.remap.keys():
            string = self.remap[event.Ascii]
        else:
            string = unicode(chr(event.Ascii))
        self.key_hook(str(event.Ascii), modifiers, string, False)
        window_name = event.WindowName or ''
        self.screen_hook(str(event.Window), window_name.decode(self.encoding), 0, 0, 0, 0)
        return True


class Sniffer:
    """Winning!"""
    def __init__(self):
        self.encoding = sys.stdin.encoding
        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.screen_hook = lambda x: True
        self.remap = {
                248: u"\xf8",
                216: u"\xd8",
                230: u"\xe6",
                198: u"\xc6",
                229: u"\xe5",
                197: u"\xc5"
                }

    def run(self):
        try:
            self.hm = pyHook.HookManager()
            self.thread = SnifferThread(self.hm)
            # pythoncom.PumpMessages needs to be in the same thread as the events
            self.thread.mouse_button_hook = self.mouse_button_hook
            self.thread.mouse_move_hook = self.mouse_move_hook
            self.thread.screen_hook = self.screen_hook
            self.thread.key_hook = self.key_hook
            self.thread.start()
            while True:
                self.thread.join(100)
        except:
            self.cancel()

    def cancel(self):
        ctypes.windll.user32.PostQuitMessage(0)
        self.hm.UnhookKeyboard()
        self.hm.UnhookMouse()
        del self.thread
        del self.hm
