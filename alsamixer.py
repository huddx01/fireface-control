from subprocess import Popen, PIPE, run, check_output
from threading import RLock
from time import sleep
from os import set_blocking

from mentat import Module

class AlsaMixer(Module):

        def __init__(self, id=0, *args, **kwargs):

            super().__init__(*args, **kwargs)

            self.add_event_callback('parameter_changed', self.parameter_changed)
            self.card_id = str(id)

            self.alsaset_process = None
            self.alsa_ok = False

            try:
                if 'Fireface' in check_output(['cat', '/proc/asound/card%s/id' % self.card_id], text=True):
                    self.alsaset_process = Popen(['amixer', '-c', self.card_id, '-s', '-q'], stdin=PIPE, text=True)
                    self.alsa_ok = True
            except:
                pass

            if not self.alsa_ok:
                self.logger.warning('Fireface interface not found')

        def parameter_changed(self, mod, name, value):
            """
            Update Alsa mixer (amixer) when a parameter with the alsa flag updates
            """
            if 'alsa' in mod.parameters[name].metadata:
                lookup = mod.parameters[name].metadata['alsa']
                if not lookup:
                    lookup = f'name="{name}"'
                self.alsa_set(lookup, value)


        def alsa_set(self, alsa_lookup, value):
            """
            Alsa mixer set function, uses an interactive amixer instance
            """
            if not self.alsa_ok:
                return

            if type(value) is list:
                value = ",".join([str(x) for x in value])

            self.alsaset_process.stdin.write('cset ' + alsa_lookup + ' ' + str(value) + '\n')
            self.alsaset_process.stdin.flush()

        def alsa_get(self, name, alsa_lookup):
            """
            Alsa mixer get function, uses an amixer instance per call
            because it doesn't work with a interactive instance (cget is not supported)
            """
            if not self.alsa_ok:
                return []

            out = run(['amixer', '-c', self.card_id, 'cget', alsa_lookup], stdout=PIPE).stdout.decode('utf-8')
            for line in out.split('\n'):
                if ': values=' in line:
                    values = line.split('=')[1]
                    values = [int(v) for v in values.split(',')]
                    return values

            return []
