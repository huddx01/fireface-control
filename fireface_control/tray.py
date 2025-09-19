import os

from pystray import Icon, MenuItem, Menu

from PIL import Image
from threading import Thread
from subprocess import Popen

from mentat import Module

from . import __version__

class Tray(Module):

    def __init__(self, *args, **kwargs):

        super().__init__('Tray', *args, **kwargs)

        folder = os.path.dirname(os.path.abspath(__file__))

        self.icon = Icon(self.engine.name, Image.open(f'{folder}/ui/logo.png'), self.engine.name, Menu(
            MenuItem(f'{self.engine.name} v{__version__}', action=lambda:[], enabled=False, default=True),
            Menu.SEPARATOR,
            MenuItem('Open control app', lambda: Popen(['xdg-open', self.engine.modules['OSC'].url], start_new_session=True)),
            MenuItem('Quit', lambda: self.engine.stop())
        ))

        Thread(target=self.icon.run).start()

        self.engine.add_event_callback('stopping', self.stop)

    def stop(self):

        self.icon.stop()
