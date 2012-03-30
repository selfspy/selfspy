import sys
import getpass

from Tkinter import *
import tkSimpleDialog

def get_password():
    if sys.stdin.isatty():
        return getpass.getpass()
    else:
        return get_tk_password()


def get_tk_password():
    root = Tk()
    root.withdraw()
    return tkSimpleDialog.askstring(title='Selfspy encryption password', prompt='Password', show='*', parent=root)

if __name__ == '__main__':
    print get_password()
