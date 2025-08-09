import pystray
import warnings

from pystray import MenuItem as item
from PIL import Image
from threading import Thread
from subprocess import Popen

from mentat import Module


class Tray(Module):

    def __init__(self, *args, **kwargs):

        super().__init__('Tray', *args, **kwargs)

        # warnings.filterwarnings("ignore")
        self.icon = pystray.Icon(self.engine.name, Image.open('ui/icon.png'), self.engine.name, pystray.Menu(
            item('Open control app', lambda: Popen(['xdg-open', self.engine.modules['OSC'].url]), default=True),
            item('Quit', lambda: self.engine.stop())
        ))

        Thread(target=self.icon.run).start()

        self.engine.add_event_callback('stopping', self.stop)

    def stop(self):

        self.icon.stop()
