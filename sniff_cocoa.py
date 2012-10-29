from Foundation import NSObject, NSLog
from AppKit import NSApplication, NSApp, NSWorkspace
from Cocoa import (NSEvent,
                   NSKeyDown, NSKeyDownMask, NSKeyUp, NSKeyUpMask,
                   NSLeftMouseUp, NSLeftMouseDown, NSLeftMouseUpMask, NSLeftMouseDownMask,
                   NSRightMouseUp, NSRightMouseDown, NSRightMouseUpMask, NSRightMouseDownMask,
                   NSMouseMoved, NSMouseMovedMask,
                   NSScrollWheel, NSScrollWheelMask,
                   NSFlagsChanged, NSFlagsChangedMask,
                   NSAlternateKeyMask, NSCommandKeyMask, NSControlKeyMask,
                   NSShiftKeyMask, NSAlphaShiftKeyMask)
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
from PyObjCTools import AppHelper

class SniffCocoa:
    def __init__(self):
        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.screen_hook = lambda x: True

    def createAppDelegate (self) :
        sc = self
        class AppDelegate(NSObject):
            def applicationDidFinishLaunching_(self, notification):
                mask = (NSKeyDownMask 
                        | NSKeyUpMask
                        | NSLeftMouseDownMask 
                        | NSLeftMouseUpMask
                        | NSRightMouseDownMask 
                        | NSRightMouseUpMask
                        | NSMouseMovedMask 
                        | NSScrollWheelMask
                        | NSFlagsChangedMask)
                NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask, sc.handler)
        return AppDelegate

    def run(self):
        NSApplication.sharedApplication()
        delegate = self.createAppDelegate().alloc().init()
        NSApp().setDelegate_(delegate)
        self.workspace = NSWorkspace.sharedWorkspace()
        AppHelper.runEventLoop()

    def cancel(self):
        AppHelper.stopEventLoop()
    
    def handler(self, event):
        try:
            activeApps = self.workspace.runningApplications()
            #Have to look into this if it is too slow on move and scoll,
            #right now the check is done for everything.
            for app in activeApps:
                if app.isActive():
                    options = kCGWindowListOptionOnScreenOnly 
                    windowList = CGWindowListCopyWindowInfo(options,
                                                            kCGNullWindowID)
                    for window in windowList:
                        if (window['kCGWindowNumber'] == event.windowNumber() 
                            or (not event.windowNumber()
                                and window['kCGWindowOwnerName'] == app.localizedName())):
                            geometry = window['kCGWindowBounds'] 
                            self.screen_hook(window['kCGWindowOwnerName'],
                                             window.get('kCGWindowName', u''),
                                             geometry['X'], 
                                             geometry['Y'], 
                                             geometry['Width'], 
                                             geometry['Height'])
                            break
                    break

            loc = NSEvent.mouseLocation()
            if event.type() == NSLeftMouseDown:
                self.mouse_button_hook(1, loc.x, loc.y)
#           elif event.type() == NSLeftMouseUp:
#               self.mouse_button_hook(1, loc.x, loc.y)
            elif event.type() == NSRightMouseDown:
                self.mouse_button_hook(3, loc.x, loc.y,)
#           elif event.type() == NSRightMouseUp:
#               self.mouse_button_hook(2, loc.x, loc.y)
            elif event.type() == NSScrollWheel:
                if event.deltaY() > 0:
                    self.mouse_button_hook(4, loc.x, loc.y)
                elif event.deltaY() < 0:
                    self.mouse_button_hook(5, loc.x, loc.y)
                if event.deltaX() > 0:
                    self.mouse_button_hook(6, loc.x, loc.y)
                elif event.deltaX() < 0:
                    self.mouse_button_hook(7, loc.x, loc.y)
#               if event.deltaZ() > 0:
#                   self.mouse_button_hook(8, loc.x, loc.y)
#               elif event.deltaZ() < 0:
#                   self.mouse_button_hook(9, loc.x, loc.y)
            elif event.type() == NSKeyDown:
                flags = event.modifierFlags()
                modifiers = [] # OS X api doesn't care it if is left or right
                if flags & NSControlKeyMask:
                    modifiers.append('Ctrl')
                if flags & NSAlternateKeyMask:
                    modifiers.append('Alt')
                if flags & NSCommandKeyMask:
                    modifiers.append('Cmd')
                if flags & (NSShiftKeyMask | NSAlphaShiftKeyMask):
                    modifiers.append('Shift')
                character = event.charactersIgnoringModifiers()
                # these two get a special case because I am unsure of
                # their unicode value
                if event.keyCode() is 36:
                    character = "Enter"
                elif event.keyCode() is 51:
                    character = "Backspace"                    
                self.key_hook(event.keyCode(), 
                              modifiers,
                              keycodes.get(character,
                                           character),
                              event.isARepeat())
            elif event.type() == NSMouseMoved:
                self.mouse_move_hook(loc.x, loc.y)
        except (Exception, KeyboardInterrupt):
            AppHelper.stopEventLoop()
            raise

# Cocoa does not provide a good api to get the keycodes, therefore we
# have to provide our own.
keycodes = {
   u"\u0009" : "Tab",
   u"\u001b" : "Escape",
   u"\uf700" : "Up",
   u"\uF701" : "Down",
   u"\uF702" : "Left",
   u"\uF703" : "Right",
   u"\uF704" : "F1",
   u"\uF705" : "F2",
   u"\uF706" : "F3",
   u"\uF707" : "F4",
   u"\uF708" : "F5",
   u"\uF709" : "F6",
   u"\uF70A" : "F7",
   u"\uF70B" : "F8",
   u"\uF70C" : "F9",
   u"\uF70D" : "F10",
   u"\uF70E" : "F11",
   u"\uF70F" : "F12",
   u"\uF710" : "F13",
   u"\uF711" : "F14",
   u"\uF712" : "F15",
   u"\uF713" : "F16",
   u"\uF714" : "F17",
   u"\uF715" : "F18",
   u"\uF716" : "F19",
   u"\uF717" : "F20",
   u"\uF718" : "F21",
   u"\uF719" : "F22",
   u"\uF71A" : "F23",
   u"\uF71B" : "F24",
   u"\uF71C" : "F25",
   u"\uF71D" : "F26",
   u"\uF71E" : "F27",
   u"\uF71F" : "F28",
   u"\uF720" : "F29",
   u"\uF721" : "F30",
   u"\uF722" : "F31",
   u"\uF723" : "F32",
   u"\uF724" : "F33",
   u"\uF725" : "F34",
   u"\uF726" : "F35",
   u"\uF727" : "Insert",
   u"\uF728" : "Delete",
   u"\uF729" : "Home",
   u"\uF72A" : "Begin",
   u"\uF72B" : "End",
   u"\uF72C" : "PageUp",
   u"\uF72D" : "PageDown",
   u"\uF72E" : "PrintScreen",
   u"\uF72F" : "ScrollLock",
   u"\uF730" : "Pause",
   u"\uF731" : "SysReq",
   u"\uF732" : "Break",
   u"\uF733" : "Reset",
   u"\uF734" : "Stop",
   u"\uF735" : "Menu",
   u"\uF736" : "User",
   u"\uF737" : "System",
   u"\uF738" : "Print",
   u"\uF739" : "ClearLine",
   u"\uF73A" : "ClearDisplay",
   u"\uF73B" : "InsertLine",
   u"\uF73C" : "DeleteLine",
   u"\uF73D" : "InsertChar",
   u"\uF73E" : "DeleteChar",
   u"\uF73F" : "Prev",
   u"\uF740" : "Next",
   u"\uF741" : "Select",
   u"\uF742" : "Execute",
   u"\uF743" : "Undo",
   u"\uF744" : "Redo",
   u"\uF745" : "Find",
   u"\uF746" : "Help",
   u"\uF747" : "ModeSwitch" }
