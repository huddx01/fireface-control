from sys import path, argv
from os.path import dirname
path.insert(0, dirname(__file__) + '/../')

from mentat import Engine

from alsamixer import AlsaMixer
from fireface import FireFace
from osc import OSC

engine = Engine('FirefaceControl', port=5555, folder='~/.config/FirefaceControl/', debug='--debug' in argv)

alsamixer = AlsaMixer('AlsaMixer')
fireface = FireFace(name=alsamixer.card_model, alsamixer=alsamixer)
osc = OSC(protocol='osc', fireface=fireface, port=8080)

engine.add_module(alsamixer)
engine.add_module(fireface)
engine.add_module(osc)

engine.autorestart()
engine.start()
