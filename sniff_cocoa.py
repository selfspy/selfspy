from Foundation import NSObject, NSLog
from AppKit import NSApplication, NSApp
from Cocoa import (NSEvent,
                   NSKeyDown, NSKeyDownMask, 
                   NSLeftMouseUp, NSLeftMouseDown, NSLeftMouseUpMask, NSLeftMouseDownMask,
                   NSRightMouseUp, NSRightMouseDown, NSRightMouseUpMask, NSRightMouseDownMask,
                   NSMouseMoved, NSMouseMovedMask,
                   NSScrollWheel, NSScrollWheelMask)
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
            if event.type() in [NSLeftMouseDown, NSRightMouseDown, NSMouseMoved]:
                windowNumber = event.windowNumber()
                windowList = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, 
                                                        kCGNullWindowID)
                for window in windowList:
                    if window['kCGWindowNumber'] == windowNumber:
                        process_name = window['kCGWindowOwnerName']
                        window_name = window['kCGWindowName']
                        # BELOW IS NOT CORRECT, NEED TRANSFORM
                        geometry = window['kCGWindowBounds'] 
                        screen_hook(process_name, 
                                    window_name, 
                                    geometry.x, 
                                    geometry.y, 
                                    geometry.width, 
                                    geometry.height)
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
            elif event.type() == NSKeyDown:
                self.key_hook(event.keyCode(), 
                              NSEvent.modifierFlags(), #This is not correct, need to transform
                              event.characters(), 
                              True, 
                              event.isARepeat())
            elif event.type() == NSMouseMoved:
                loc = NSEvent.mouseLocation()
                self.mouse_move_hook(loc.x, loc.y)
        except KeyboardInterrupt:
            AppHelper.stopEventLoop()

if __name__ == '__main__':
    sc = SniffCocoa()
    sc.run()
