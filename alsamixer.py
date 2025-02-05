from subprocess import Popen, PIPE, run, STDOUT
from threading import RLock
from time import sleep
from os import set_blocking

from mentat import Module

class AlsaMixer(Module):

        def __init__(self, *args, **kwargs):

            super().__init__(*args, **kwargs)

            self.watched_parameters = {}
            self.add_event_callback('parameter_changed', self.parameter_changed)

            self.alsaset_process = Popen(['amixer', '-c', '0', '-s', '-q'], stdin=PIPE, text=True)

        def add_alsa_parameter(self, *args, alsa_lookup=None, **kwargs):
            
            self.add_parameter(*args, **kwargs)
           
            name = kwargs['name'] if 'name' in kwargs else args[0] 
            if alsa_lookup is None:
                alsa_lookup = f'name="{name}"'
            self.watched_parameters[name] = alsa_lookup

        def parameter_changed(self, mod, name, value):

            if name in self.watched_parameters:
                alsa_lookup =  self.watched_parameters[name]

                self.alsa_set(alsa_lookup, value)


        def alsa_set(self, alsa_lookup, value):
            if type(value) is list:
                value = ",".join([str(x) for x in value])

            self.alsaset_process.stdin.write('cset ' + alsa_lookup + ' ' + str(value) + '\n')
            self.alsaset_process.stdin.flush()


        def alsa_update(self):
            while True:
                sleep(0.001)
                # with self.alsaget_lock:
                self.alsaget_process.stdout.flush()
                for line in self.alsaget_process.stdout:
                    # line =  self.alsaget_process.stdout.readline()
                    if 'name=' in line:
                        self.alsaget_key = line.split('name=')[1][1:-2]
                    elif ': values=' in line and self.alsaget_key is not None:
                        values = line.split('=')[1]
                        try:
                            values = [int(v) for v in values.split(',')]
                            self.alsaget_data[self.alsaget_key] = values
                        except:
                            pass

                    
     
        def alsa_get(self, name, alsa_lookup):

            out = run(['amixer', '-c', '0', 'cget', alsa_lookup], stdout=PIPE).stdout.decode('utf-8')
            for line in out.split('\n'):
                if ': values=' in line:
                    values = line.split('=')[1]
                    values = [int(v) for v in values.split(',')]
                    return values

            return []