from Foundation import NSObject, NSLog
from AppKit import NSApplication, NSApp, NSWorkspace
from Cocoa import (NSEvent,
                   NSKeyDown, NSKeyDownMask, NSKeyUp, NSKeyUpMask,
                   NSLeftMouseUp, NSLeftMouseDown, NSLeftMouseUpMask, NSLeftMouseDownMask,
                   NSRightMouseUp, NSRightMouseDown, NSRightMouseUpMask, NSRightMouseDownMask,
                   NSMouseMoved, NSMouseMovedMask,
                   NSScrollWheel, NSScrollWheelMask,
                   NSAlternateKeyMask, NSCommandKeyMask, NSControlKeyMask)
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
from PyObjCTools import AppHelper

class SniffCocoa:
    def __init__(self):
        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.screen_hook = lambda x: True

        self.currentApp = None

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
                        | NSScrollWheelMask)
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
                    if app.localizedName() != self.currentApp:
                        self.currentApp = app.localizedName()
                        options = kCGWindowListOptionOnScreenOnly 
                        windowList = CGWindowListCopyWindowInfo(options,
                                                                kCGNullWindowID)
                        for window in windowList:
                            if window['kCGWindowOwnerName'] == self.currentApp:
                                geometry = window['kCGWindowBounds'] 
                                self.screen_hook(window['kCGWindowOwnerName'],
                                                 window['kCGWindowName'],
                                                 geometry['X'], 
                                                 geometry['Y'], 
                                                 geometry['Width'], 
                                                 geometry['Height'])
                                break
                    break
            if event.type() == NSLeftMouseDown:
                loc = NSEvent.mouseLocation()
                self.mouse_button_hook(1, loc.x, loc.y, True)
#           elif event.type() == NSLeftMouseUp:
#               self.mouse_button_hook(1, False)
            elif event.type() == NSRightMouseDown:
                loc = NSEvent.mouseLocation()
                self.mouse_button_hook(3, loc.x, loc.y, True)
#           elif event.type() == NSRightMouseUp:
#               self.mouse_button_hook(2, False)
#           elif event.type() == NSScrollWheel:
                # Scroll behaves differently on OS X then in Xorg, need to think of something here
            elif event.type() == NSKeyDown:
                flags = event.modifierFlags()
                modifiers = [] # OS X api doesn't care it if is left or right
                if (flags & NSControlKeyMask):
                    modifiers.append('CONTROL')
                if (flags & NSAlternateKeyMask):
                    modifiers.append('ALTERNATE')
                if (flags & NSCommandKeyMask):
                    modifiers.append('COMMAND')
                self.key_hook(event.keyCode(), 
                              modifiers,
                              event.characters(),
                              event.isARepeat())
            elif event.type() == NSMouseMoved:
                loc = NSEvent.mouseLocation()
                self.mouse_move_hook(loc.x, loc.y)
        except (Exception, KeyboardInterrupt) as e:
            print e
            AppHelper.stopEventLoop()

if __name__ == '__main__':
    sc = SniffCocoa()
    sc.run()
