import os

from subprocess import Popen, PIPE, run
from sys import argv

from mentat import Module

class OSC(Module):

    def __init__(self, ff802, *args, **kwargs):
        """
        Open Stage Control manager, runs the server and bridges between ff802's parameters and widget state
        """

        super().__init__('OSC', *args, **kwargs)

        self.engine.add_event_callback('parameter_changed', self.parameter_changed)
        self.ff802 = ff802
        self.local_state = {}
        self.remote_state = {}
        self.first_connect = False
        self.clipboard = {}

        folder = os.path.dirname(os.path.abspath(__file__))
        # run instance of o-s-c (will quit when python process exits if everything goes well)
        if not self.engine.restarted:
            if '--dev-gui' not in argv:
                Popen([
                    'open-stage-control',
                    '--port', str(self.port),
                    '-s', '127.0.0.1:%i' % self.engine.port,
                    '-l', '%s/ui/ui.json' % folder,
                    '-t', '%s/ui/styles.css' % folder
                ] + (['-n'] if '--nogui' in argv else []))
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
                if name == 'output:select':
                    self.send_output_sel_state(value[0])
                if name == 'input:select':
                    self.send_input_sel_state(value[0])

                if name in self.remote_state and self.remote_state[name] == value:
                    return

                if self.filter_param(name) is False:
                    return

                self.remote_state[name] = value
                self.send(f'/{name}', *value)


    def send_state(self):
        """
        Send local state when a new osc client connects (or if it refreshes).
        This module doesn't have its own parameters and instead watches ff802's,
        it uses its own value store to optimize traffic where possible.
        """

        super().send_state()

        state = list(self.local_state.items())
        state.sort(key=lambda item: self.ff802.parameters[item[0]].metadata['osc_order'] if 'osc_order' in self.ff802.parameters[item[0]].metadata else 0)
        for name, value in state:
            if self.filter_param(name) is not False:
                self.send(f'/{name}', *value)

    def send_output_sel_state(self, index):
        """
        Send values related to output channel selection:
            - output fxs
            - output options
            - monitor mix for this output
        """

        if 'output:select' in self.local_state:
            self.send('/output:select', self.ff802.get('output:select'))

        output_select = str(self.ff802.get('output:select'))
        for name, value in self.local_state.items():
            if 'output:' in name and name.split(':')[-1] == output_select:
                self.send(f'/{name}', *value)
            elif 'monitor:' in name and name.split(':')[-2] == output_select:
                self.send(f'/{name}', *value)

    def send_input_sel_state(self, index):
        """
        Send values related to input channel selection:
            - input fxs
            - input options
        """

        if 'input:select' in self.local_state:
            self.send('/input:select', self.ff802.get('input:select'))

        input_select = str(self.ff802.get('input:select'))
        for name, value in self.local_state.items():
            if 'input:' in name and name.split(':')[-1] == input_select:
                self.send(f'/{name}', *value)


    def filter_param(self, name):
        """
        Filter out unneeded value to reduce traffic:
            - input parameters for unselected input
            - monitor mix for unselected output
            - output fx for unselect output
        """
        output_select = str(self.ff802.get('output:select'))
        input_select = str(self.ff802.get('input:select'))

        if 'input:' in name and name.split(':')[-1] != input_select:
            return False

        if 'monitor:' in name and name.split(':')[-2] != output_select:
            return False

        if 'output:' in name and (':eq' in name or ':dyn' in name or ':hpf' in name) and name.split(':')[-1] != output_select:
            return False


    def route(self, address, args):
        """
        Widget routing
        """

        if address == '/connect':
            self.first_connect = True
            self.send_state()

        elif address == '/state':
            cmd = args[0].lower()
            state_name = self.ff802.get('current-state')
            if cmd == 'save':
                self.ff802.save(state_name, omit_defaults=True)
                self.start_scene('defered state', lambda: [
                    self.send('/current-state', self.ff802.get('current-state'))
                ])
                self.send('/NOTIFY', 'save', f'State {state_name} saved',)
            elif cmd == 'load':
                self.ff802.soft_reset()
                self.ff802.load(state_name)
                self.ff802.set('current-state', state_name)
                self.send('/NOTIFY', 'folder-open', f'State {state_name} loaded'),
            elif cmd == 'delete':
                if state_name != 'default':
                    self.ff802.delete(state_name)
                    self.ff802.reset('current-state')
                    self.send('/NOTIFY', 'trash', f'State {state_name} deleted')
                else:
                    self.send('/NOTIFY', 'times', f'State {state_name} cannot be deleted')
            elif cmd == 'reset':
                self.ff802.soft_reset()
                self.ff802.set('current-state', state_name)
                self.send('/NOTIFY', 'undo', 'State reset')


        elif address == '/fx':
            strip_type, fx, cmd = [a.lower() for a in args]
            if strip_type:
                select = str(self.ff802.get(f'{strip_type}:select'))

            if cmd == 'copy':
                self.clipboard[fx] = {}
                for name in self.local_state:
                    if fx == 'echo' and (':echo' in name) or fx == 'reverb' and (':reverb' in name):
                        self.clipboard[fx][name] = self.local_state[name]
                    elif strip_type and f'{strip_type}:' in name and name.split(':')[-1] == select:
                        if fx == 'eq' and (':eq' in name or ':hpf' in name) or fx == 'dyn' and (':dyn' in name):
                            generic_name = ':'.join(name.split(':')[1:-1])
                            self.clipboard[fx][generic_name] = self.local_state[name]
                            
            elif cmd == 'paste':
                if fx in self.clipboard:
                    for name in self.clipboard[fx]:
                        if fx in ['echo', 'reverb']:
                            self.ff802.set(f'{name}', *self.clipboard[fx][name])
                        elif fx in ['eq', 'dyn']:
                            self.ff802.set(f'{strip_type}:{name}:{select}', *self.clipboard[fx][name])


            elif cmd == 'reset':
                for name in self.local_state:
                    if fx == 'echo' and (':echo' in name) or fx == 'reverb' and (':reverb' in name):
                        self.ff802.reset(name)
                    elif strip_type and f'{strip_type}:' in name and name.split(':')[-1] == select:
                        if fx == 'eq' and (':eq' in name or ':hpf' in name) or fx == 'dyn' and (':dyn' in name):
                            self.ff802.reset(name)

        else:
            name = address[1:]
            if self.ff802.get_parameter(name):
                self.remote_state[name] = args
                self.ff802.set(name, *args)
