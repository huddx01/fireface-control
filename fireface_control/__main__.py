import socket
from sys import path, argv
from os.path import dirname

# load local package
# if not installed
if __package__ == None:
    __package__ = 'fireface_control'
    path.insert(0, './')

from mentat import Engine

from .config import config
from .alsamixer import AlsaMixer
from .fireface import FireFace
from .osc import OSC
from .tray import Tray

# Check if ports are available
# and get random ports if 0
# let it throw if port is not free
engine_port = config.engine_port
webapp_port = config.port
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', engine_port))
engine_port = sock.getsockname()[1]
sock.close()
if not config.dev:
    # in dev mode the server is not restarted
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', webapp_port))
    webapp_port = sock.getsockname()[1]
    sock.close()

engine = Engine('FirefaceControl', port=engine_port, folder='~/.config/fireface-control/', debug='--debug' in argv)

alsamixer = AlsaMixer('AlsaMixer')
fireface = FireFace(alsamixer=alsamixer)
osc = OSC(protocol='osc', fireface=fireface, port=webapp_port)
tray = Tray(port=None)

engine.add_module(alsamixer)
engine.add_module(fireface)
engine.add_module(osc)
engine.add_module(tray)

engine.autorestart()
engine.start()
