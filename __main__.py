from sys import path, argv
from os.path import dirname
path.insert(0, dirname(__file__) + '/../')

from mentat import Engine

from fireface802 import FireFace802
from osc import OSC

engine = Engine('AlsaMixer', port=5555, folder='~/.config/FirefaceControl/', debug='--debug' in argv)

ff802 = FireFace802(id=0)
osc = OSC(protocol='osc', ff802=ff802, port=8080)

engine.add_module(ff802)
engine.add_module(osc)

engine.autorestart()
engine.start()
