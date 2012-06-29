from Cocoa import (NSApp,
                   NSEvent,
                   NSKeyDownMask, 
                   NSLeftMouseUp, NSLeftMouseDown, NSLeftMouseUpMask, NSLeftMouseDownMask,
                   NSRightMouseUp, NSRightMouseDown, NSRightMouseUpMask, NSRightMouseDownMask,
                   NSMouseMoved, NSMouseMovedMask,
                   NSScrollWheel, NSScrollWheelMask)
from Foundation import NSObject, NSApplication, NSLog
from PyObjCTools import AppHelper


class SniffCocoa:
    def __init__(self):
        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True

    def createAppDelegate (self) :
        sc = self
        class AppDelegate(NSObject):
            def applicationDidFinishLaunching_(self, notification):
                mask = (NSKeyDownMask 
                        | NSLeftMouseDownMask 
                        | NSLeftMouseUpMask
                        | NSRightMouseDownMask 
                        | NSRightMouseUpMask
                        | NSMouseMovedMask 
                        | NSScrollWheelMask)
                NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask, sc.handler)
        return AppDelegate

    def run(self):
        app = NSApplication.sharedApplication()
        delegate = self.createAppDelegate().alloc().init()
        NSApp().setDelegate_(delegate)
        AppHelper.runEventLoop()

    def cancel(self):
        AppHelper.stopEventLoop()
    
    def handler(self, event):
        NSLog(u"%@", event)
        """
        if event.type == NSLeftMouseDown:
           self.mouse_button_hook(1, True)
        elif event.type == NsLeftMouseUp:
           self.mouse_button_hook(1, False)
        elif event.type == NSRightMouseDown:
           self.mouse_button_hook(2, True)
        elif event.type == NSRightMouseUp:
           self.mouse_button_hook(2, False)
        elif event.type == NSKeyDown:
           self.key_hook(event.keyCode, None, event.characters, True, event.isARepeat)
        elif event.type == NSMouseMoved:
            loc = NSEvent.mouseLocation
            self.mouse_move_hook(loc.x, loc.y)
        """

