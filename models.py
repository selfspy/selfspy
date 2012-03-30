import datetime

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Index, Column, Boolean, Integer, Unicode, UnicodeText, DateTime, Binary, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref

def initialize(fname):
    engine = create_engine('sqlite:///%s' % fname)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


Base = declarative_base()

class SpookMixin(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.now(), index=True)


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

    def __init__(self, geo):
        self.xpos = geo.x
        self.ypos = geo.y
        self.width = geo.width
        self.height = geo.height

    def __repr__(self):
        return "<Geometry (%d, %d), (%d, %d)>" % (self.xpos, self.ypos, self.width, self.height)

class Click(SpookMixin, Base):
    button = Column(Integer, nullable=False)
    press = Column(Boolean, nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    nrmoves = Column(Integer, nullable=False)

    window_id = Column(Integer, ForeignKey('window.id'), nullable=False)
    window = relationship("Window", backref=backref('clicks'))
    
    geometry_id = Column(Integer, ForeignKey('geometry.id'), nullable=False)
    geometry = relationship("Geometry", backref=backref('clicks'))

    def __init__(self, button, press, x, y, nrmoves, window_id, geometry_id):
        self.button = button
        self.press = press
        self.x = x
        self.y = y
        self.nrmoves = nrmoves

        self.window_id = window_id
        self.geometry_id = geometry_id

    def __repr__(self):
        return "<Click (%d, %d), (%d, %d, %d)>" % (self.xpos, self.ypos, self.button, self.press, self.nrmoves)

class Keys(SpookMixin, Base):
    text = Column(Binary, nullable=False)
    started = Column(DateTime, nullable=False)

    window_id = Column(Integer, ForeignKey('window.id'), nullable=False)
    window = relationship("Window", backref=backref('keys'))

    geometry_id = Column(Integer, ForeignKey('geometry.id'), nullable=False)
    geometry = relationship("Geometry", backref=backref('keys'))

    timings = Column(Binary)

    def __init__(self, text, timings, started, window_id, geometry_id):
        self.text = text
        self.timings = timings
        self.started = started

        self.window_id = window_id
        self.geometry_id = geometry_id

    def __repr__(self):
        return "<Keys %s>" % self.text



