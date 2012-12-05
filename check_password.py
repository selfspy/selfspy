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

import os

DIGEST_NAME = 'password.digest'
MAGIC_STRING = '\xc5\x7fdh\x05\xf6\xc5=\xcfh\xafv\xc0\xf4\x13i*.O\xf6\xc2\x8d\x0f\x87\xdb\x9f\xc2\x88\xac\x95\xf8\xf0\xf4\x96\xe9\x82\xd1\xca[\xe5\xa32\xa0\x03\nD\x12\n\x1dr\xbc\x03\x9bE\xd3q6\x89Cwi\x10\x92\xdf(#\x8c\x87\x1b3\xd6\xd4\x8f\xde)\xbe\x17\xbf\xe4\xae\xb73\\\xcb\x7f\xd3\xc4\x89\xd0\x88\x07\x90\xd8N,\xbd\xbd\x93j\xc7\xa3\xec\xf3P\xff\x11\xde\xc9\xd6 \x98\xe8\xbc\xa0|\x83\xe90Nw\xe4=\xb53\x08\xf0\x14\xaa\xf9\x819,X~\x8e\xf7mB\x13\xe9;\xde\x9e\x10\xba\x19\x95\xd4p\xa7\xd2\xa9o\xbdF\xcd\x83\xec\xc5R\x17":K\xceAiX\xc1\xe8\xbe\xb8\x04m\xbefA8\x99\xee\x00\x93\xb4\x00\xb3\xd4\x8f\x00@Q\xe9\xd5\xdd\xff\x8d\x93\xe3w6\x8ctRQK\xa9\x97a\xc1UE\xdfv\xda\x15\xf5\xccA)\xec^]AW\x17/h)\x12\x89\x15\x0e#8"\x7f\x16\xd6e\x91\xa6\xd8\xea \xb9\xdb\x93W\xce9\xf2a\xe7\xa7T=q'


def check(data_dir, decrypter, read_only=False):
    fname = os.path.join(data_dir, DIGEST_NAME)
    if os.path.exists(fname):
        if decrypter is None:
            return False
        f = open(fname, 'rb')
        s = f.read()
        f.close()
        return decrypter.decrypt(s) == MAGIC_STRING
    else:
        if decrypter is not None:
            if read_only:
                return False
            else:
                s = decrypter.encrypt(MAGIC_STRING)
                f = open(fname, 'wb')
                f.write(s)
                f.close()
        return True
