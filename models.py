import zlib
import json

import datetime

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Index, Column, Boolean, Integer, Unicode, UnicodeText, DateTime, Binary, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref


def initialize(fname):
    engine = create_engine('sqlite:///%s' % fname)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

ENCRYPTER = None

Base = declarative_base()


class SpookMixin(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.now, index=True)


class Process(SpookMixin, Base):
    name = Column(Unicode, index=True, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<Process '%s'>" % self.name


class Window(SpookMixin, Base):
    title = Column(Unicode, index=True)

    process_id = Column(Integer, ForeignKey('process.id'), nullable=False, index=True)
    process = relationship("Process", backref=backref('windows'))

    def __init__(self, title, process_id):
        self.title = title
        self.process_id = process_id

    def __repr__(self):
        return "<Window '%s'>" % (self.title)

    
class Geometry(SpookMixin, Base):
    xpos = Column(Integer, nullable=False)
    ypos = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)

    Index('idx_geo', 'xpos', 'ypos', 'width', 'height')

    def __init__(self, x, y, width, height):
        self.xpos = x
        self.ypos = y
        self.width = width
        self.height = height

    def __repr__(self):
        return "<Geometry (%d, %d), (%d, %d)>" % (self.xpos, self.ypos, self.width, self.height)

    
class Click(SpookMixin, Base):
    button = Column(Integer, nullable=False)
    press = Column(Boolean, nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    nrmoves = Column(Integer, nullable=False)

    process_id = Column(Integer, ForeignKey('process.id'), nullable=False, index=True)
    process = relationship("Process", backref=backref('clicks'))

    window_id = Column(Integer, ForeignKey('window.id'), nullable=False)
    window = relationship("Window", backref=backref('clicks'))
    
    geometry_id = Column(Integer, ForeignKey('geometry.id'), nullable=False)
    geometry = relationship("Geometry", backref=backref('clicks'))

    def __init__(self, button, press, x, y, nrmoves, process_id, window_id, geometry_id):
        self.button = button
        self.press = press
        self.x = x
        self.y = y
        self.nrmoves = nrmoves

        self.process_id = process_id
        self.window_id = window_id
        self.geometry_id = geometry_id

    def __repr__(self):
        return "<Click (%d, %d), (%d, %d, %d)>" % (self.x, self.y, self.button, self.press, self.nrmoves)

    
def pad(s, padnum):
    ls = len(s)
    if ls % padnum == 0:
        return s
    return s + '\0' * (padnum - (ls % padnum))


def maybe_encrypt(s):
    if ENCRYPTER:
        s = pad(s, 8)
        s = ENCRYPTER.encrypt(s)
    return s


def maybe_decrypt(s):
    if ENCRYPTER:
        s = ENCRYPTER.decrypt(s)
    return s


class Keys(SpookMixin, Base):
    text = Column(Binary, nullable=False)
    started = Column(DateTime, nullable=False)

    process_id = Column(Integer, ForeignKey('process.id'), nullable=False, index=True)
    process = relationship("Process", backref=backref('keys'))

    window_id = Column(Integer, ForeignKey('window.id'), nullable=False)
    window = relationship("Window", backref=backref('keys'))

    geometry_id = Column(Integer, ForeignKey('geometry.id'), nullable=False)
    geometry = relationship("Geometry", backref=backref('keys'))

    nrkeys = Column(Integer, index=True)

    keys = Column(Binary)
    timings = Column(Binary)

    def __init__(self, text, keys, timings, nrkeys, started, process_id, window_id, geometry_id):
        ztimings = zlib.compress(json.dumps(timings))
        zkeys = maybe_encrypt(zlib.compress(json.dumps(keys)))
        ztext = maybe_encrypt(text)

        self.text = ztext
        self.keys = zkeys
        self.nrkeys = nrkeys
        self.timings = ztimings
        self.started = started

        self.process_id = process_id
        self.window_id = window_id
        self.geometry_id = geometry_id

    def decrypt_text(self):
        return maybe_decrypt(self.text)

    def decrypt_keys(self):
        keys = maybe_decrypt(self.keys)
        return json.loads(zlib.decompress(keys))

    def __repr__(self):
        return "<Keys %s>" % self.nrkeys



