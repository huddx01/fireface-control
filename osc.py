from subprocess import Popen, PIPE, run, STDOUT

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

        # run instance of o-s-c (will quit when python process exits if everything goes well)
        if not self.engine.restarted:
            Popen([
                'open-stage-control',
                '--port', str(self.port),
                '-s', '127.0.0.1:%i' % self.engine.port,
                '-l', '%s/ui/ui.json' % self.engine.folder,
                '-t', '%s/ui/styles.css' % self.engine.folder
            ])


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
                if name in self.remote_state and self.remote_state[name] == value:
                    return
                self.send(f'/{name}', *value)
                self.local_state[f'/{name}'] = value

    def remote_state(self):
        """
        Send local state when a new osc client connects (or if it refreshes)
        """

        super().remote_state()

        # send custom state
        prioritized = ['/sources-types', '/sources-ids']
        for address in prioritized:
            self.send(address, *self.local_state[address])

        for address, value in self.local_state.items():
            if address not in prioritized:
                self.send(address, *value)

    def route(self, address, args):
        """
        Widget routing.
        """

        if address == '/connect':
            self.remote_state()

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
