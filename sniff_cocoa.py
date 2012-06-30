from Foundation import NSObject, NSLog
from AppKit import NSApplication, NSApp
from Cocoa import (NSEvent,
                   NSKeyDown, NSKeyDownMask, 
                   NSLeftMouseUp, NSLeftMouseDown, NSLeftMouseUpMask, NSLeftMouseDownMask,
                   NSRightMouseUp, NSRightMouseDown, NSRightMouseUpMask, NSRightMouseDownMask,
                   NSMouseMoved, NSMouseMovedMask,
                   NSScrollWheel, NSScrollWheelMask)
from PyObjCTools import AppHelper

class Display:
    def __init__(self):
        self.focus = self.Focus()

    class Focus:
        def __init__(self):
            self.focus = self
            self.geo = self.Geometry() 
            self.wm_name = 'unknown'
            self.app_name = 'unknown'
        def get_wm_name(self):
            return wm_name
        def get_wm_class(self):
            return "unknown", self.app_name, self.wm_name
        class Geometry:
            def __init__(self):
                self.x = 1680
                self.y = 1050
                self.width = 1680
                self.height = 1050

        def get_geometry(self):
            return self.geo

    def get_input_focus(self):
        return self.focus

class SniffCocoa:
    def __init__(self):
        self.key_hook = lambda x: True
        self.mouse_button_hook = lambda x: True
        self.mouse_move_hook = lambda x: True
        self.the_display = Display()

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
        NSApplication.sharedApplication()
        delegate = self.createAppDelegate().alloc().init()
        NSApp().setDelegate_(delegate)
        AppHelper.runEventLoop()

    def cancel(self):
        AppHelper.stopEventLoop()
    
    def handler(self, event):
        try:
            if event.type() == NSLeftMouseDown:
                self.mouse_button_hook(1, True)
 #           elif event.type() == NSLeftMouseUp:
  #              self.mouse_button_hook(1, False)
            elif event.type() == NSRightMouseDown:
                self.mouse_button_hook(2, True)
   #         elif event.type() == NSRightMouseUp:
    #            self.mouse_button_hook(2, False)
            elif event.type() == NSKeyDown:
                self.key_hook(event.keyCode(), None, event.characters(), True, event.isARepeat())
            elif event.type() == NSMouseMoved:
                loc = NSEvent.mouseLocation()
                self.mouse_move_hook(loc.x, loc.y)
            if event.type() in [NSLeftMouseDown, NSRightMouseDown, NSMouseMoved]:
                windowNumber = event.windowNumber()
                windowList = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, 
                                                        kCGNullWindowID)
                for window in windowList:
                    if window['kCGWindowNumber'] == windowNumber:
                        self.focus.wm_name = window['kCGWindowName']
                        self.fucus.app_name = window['kCGWindowOwnerName']
                        break
        except KeyboardInterrupt:
            AppHelper.stopEventLoop()

if __name__ == '__main__':
    sc = SniffCocoa()
    sc.run()
