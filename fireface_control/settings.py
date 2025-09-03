from mentat import Module

class Settings(Module):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.may_cancel = False

        self.add_parameter('last-state', None, types='s', default='')
        self.add_parameter('autoload-state', None, types='i', default=0)

        self.load('default')