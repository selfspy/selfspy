import sys
import getpass

from Tkinter import *
import tkSimpleDialog

def get_password(verify=None, message=None):
    if sys.stdin.isatty():
        for i in xrange(3):
            if message:
                pw = getpass.getpass(message)
            else:
                pw = getpass.getpass()
            if not verify: break
            if verify(pw): break
    else:
        pw = get_tk_password(verify, message)
    return pw


def get_tk_password(verify, message=None):
    root = Tk()
    root.withdraw()
    if message is None:
        message = 'Password'
    
    while True:
        pw = tkSimpleDialog.askstring(title='Selfspy encryption password', prompt=message, show='*', parent=root)

        if pw is None: return ""

        if not verify: break
        if verify(pw): break
    return pw
        

if __name__ == '__main__':
    print(get_password())
