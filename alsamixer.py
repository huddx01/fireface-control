from subprocess import Popen, PIPE, run, check_output
from threading import RLock
from time import sleep
from os import set_blocking

from mentat import Module

class AlsaMixer(Module):

        def __init__(self, *args, **kwargs):

            super().__init__(*args, **kwargs)

            self.alsaset_process = None
            self.alsa_ok = False

            self.card_id = 0
            self.card_model = '802'

            while True:
                try:
                    card = check_output(['cat', f'/proc/asound/card{card_index}/id'], text=True)
                    if 'Fireface' in card:
                        self.alsa_ok = True
                        if 'UCX' in card:
                            self.card_model = 'UCX'
                        break
                except:
                    break
                self.card_id += 1

            self.card_id = str(self.card_id)

            if not self.alsa_ok:
                self.logger.warning('Fireface interface not found')

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
