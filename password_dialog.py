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

import sys
import getpass

from Tkinter import Tk
import tkSimpleDialog

def get_password(verify=None, message=None):
    if sys.stdin.isatty():
        for i in xrange(3):
            if message:
                pw = getpass.getpass(message)
            else:
                pw = getpass.getpass()
            if (not verify) or verify(pw):
                break
    else:
        pw = get_tk_password(verify, message)
    return pw

def get_tk_password(verify, message=None):
    root = Tk()
    root.withdraw()
    if message is None:
        message = 'Password'

    while True:
        pw = tkSimpleDialog.askstring(title='Selfspy encryption password',
                                      prompt=message,
                                      show='*',
                                      parent=root)

        if pw is None:
            return ""

        if (not verify) or verify(pw):
            break
    return pw


if __name__ == '__main__':
    print get_password()
