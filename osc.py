from subprocess import Popen, PIPE, run, STDOUT

from mentat import Module

class OSC(Module):

    def __init__(self, ff802, *args, **kwargs):

        super().__init__('OSC', *args, **kwargs)

        self.engine.add_event_callback('parameter_changed', self.parameter_changed)
        self.ff802 = ff802
        self.osc_state = {}

        if not self.engine.restarted:
            Popen(['open-stage-control', '-s', '127.0.0.1:%i' % self.engine.port, '-l', '%s/ff802.json' % self.engine.folder])


    def parameter_changed(self, mod, name, value):

        if mod != self:
            if type(value) is not list:
                value = [value]
            self.send(f'/{name}', *value)
            self.osc_state[f'/{name}'] = value

    def send_state(self):
        """
        Send local state (because it's not part of this module's actual state)
        """

        super().send_state()

        # send custom state
        prioritized = ['/sources-types', '/sources-ids']
        for address in prioritized:
            self.send(address, *self.osc_state[address])

        for address, value in self.osc_state.items():
            if address not in prioritized:
                self.send(address, *value)

    def route(self, address, args):
        
        if address == '/connect':
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
                self.ff802.set(name, *args)