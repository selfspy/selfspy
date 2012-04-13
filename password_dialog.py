import sys
import getpass

from Tkinter import *
import tkSimpleDialog

def get_password(verify=None):
    if sys.stdin.isatty():
        for i in xrange(3):
            pw = getpass.getpass()
            if not verify: break
            if verify(pw): break
    else:
        pw = get_tk_password(verify)
    return pw
        


def get_tk_password(verify):
    root = Tk()
    root.withdraw()
    
    while True:
        pw = tkSimpleDialog.askstring(title='Selfspy encryption password', prompt='Password', show='*', parent=root)

        if pw is None: return ""

        if not verify: break
        if verify(pw): break
    return pw
        

if __name__ == '__main__':
    print get_password()
