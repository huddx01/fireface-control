from mentat import Module

class Settings(Module):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.add_parameter('autoload-state', None, types='i', default=0)

        self.load('default')