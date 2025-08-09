from pystray import Icon, MenuItem, Menu

from PIL import Image
from threading import Thread
from subprocess import Popen

from mentat import Module


class Tray(Module):

    def __init__(self, *args, **kwargs):

        super().__init__('Tray', *args, **kwargs)

        self.icon = Icon(self.engine.name, Image.open('ui/icon.png'), self.engine.name, Menu(
            MenuItem('Open control app', lambda: Popen(['xdg-open', self.engine.modules['OSC'].url]), default=True),
            MenuItem('Quit', lambda: self.engine.stop())
        ))

        Thread(target=self.icon.run).start()

        self.engine.add_event_callback('stopping', self.stop)

    def stop(self):

        self.icon.stop()
