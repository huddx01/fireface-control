from subprocess import Popen, PIPE, run
from sys import argv

from mentat import Module

class OSC(Module):

    def __init__(self, ff802, *args, **kwargs):
        """
        Open Stage Control manager
        """

        super().__init__('OSC', *args, **kwargs)

        self.engine.add_event_callback('parameter_changed', self.parameter_changed)
        self.ff802 = ff802
        self.local_state = {}
        self.remote_state = {}
        self.first_connect = False

        # run instance of o-s-c (will quit when python process exits if everything goes well)
        if not self.engine.restarted:
            if not '--nogui' in argv:
                Popen([
                    'open-stage-control',
                    '--port', str(self.port),
                    '-s', '127.0.0.1:%i' % self.engine.port,
                    '-l', '%s/ui/ui.json' % self.engine.folder,
                    '-t', '%s/ui/styles.css' % self.engine.folder
                ])
        else:
            self.first_connect = True

    def parameter_changed(self, mod, name, value):
        """
        Update GUI when a parameter with the osc flag updates
        """


        if 'osc' in mod.parameters[name].metadata:

            if type(value) is not list:
                value = [value]

            if 'meter:' in name:
                # optimize meter update (bypass o-s-c's cross-widgets sync checks)
                self.send('/SCRIPT', f'set("{name}", {value[0]}, {'{sync: false, send:false}'})')
            else:
                self.local_state[name] = value

                if not self.first_connect:
                    return

                if name == 'mixers:select':
                    self.send_sel_state(value[0])

                if name in self.remote_state and self.remote_state[name] == value:
                    return

                if self.filter_param(name) is False:
                    return

                self.remote_state[name] = value
                self.send(f'/{name}', *value)


    def send_state(self):
        """
        Send local state when a new osc client connects (or if it refreshes)
        """

        super().send_state()


        state = list(self.local_state.items())
        state.sort(key=lambda item: self.ff802.parameters[item[0]].metadata['osc_order'] if 'osc_order' in self.ff802.parameters[item[0]].metadata else 0)
        for name, value in state:
            if self.filter_param(name) is not False:
                self.send(f'/{name}', *value)
        self.send_sel_state(self.ff802.get('mixers:select'))

    def send_sel_state(self, index):
        if 'mixers:select' in self.local_state:
            self.send('/mixers:select', *self.local_state['mixers:select'])
        for name, value in self.local_state.items():
            if 'monitor:' in name and self.filter_param(name) is not False:
                self.send(f'/{name}', *value)
            if 'output:eq' in name and self.filter_param(name) is not False:
                self.send(f'/{name}', *value)


    def filter_param(self, name):
        select =  self.ff802.get('mixers:select')
        if 'monitor:' in name and f':{select}:' not in name:
            return False
        if 'output:eq' in name and 'activate' not in name and f':{select}' not in name:
            return False

    def route(self, address, args):
        """
        Widget routing.
        """

        if address == '/connect':
            self.first_connect = True
            self.send_state()

        elif address == '/state':
            if args[0] == 'save':
                self.ff802.save('test', omit_defaults=True)
            elif args[0] == 'load':
                self.ff802.load('test')
            elif args[0] == 'reset':
                self.ff802.reset()

        else:
            name = address[1:]
            if self.ff802.get_parameter(name):
                self.remote_state[name] = args
                self.ff802.set(name, *args)
