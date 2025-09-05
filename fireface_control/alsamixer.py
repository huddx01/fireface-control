from subprocess import Popen, PIPE, run, check_output, DEVNULL
from threading import RLock
from time import sleep
from os import set_blocking

from mentat import Module

class AlsaMixer(Module):

        def __init__(self, *args, **kwargs):

            super().__init__(*args, **kwargs)

            self.snd_process = None
            self.alsaset_process = None

            self.add_parameter('card-online', None, types='i', default=0)
            self.add_parameter('card-model', None, types='s', default='')

            self.waking_up = False

            for model in ['802', 'UCX']:
                try:
                    status = check_output(['cat', f'/proc/asound/Fireface{model}/firewire/status'], text=True, stderr=DEVNULL)
                    if status:
                        self.set('card-model', model)
                        self.logger.info(f'Fireface {self.get('card-model')} found')
                        self.start_alsaset_process()
                        break
                except:
                    pass

            if not self.get('card-model'):
                self.set('card-model', '802')
                self.logger.warning(f'Fireface interface not found, falling back to offline Fireface {self.get('card-model')}')

            self.start_scene('status_check', self.status_check)


            self.add_event_callback('parameter_changed', self.parameter_changed)
            self.engine.add_event_callback('stopping', self.stop)

        def status_check(self):
            """
            Detect interface connection status
            """
            while True:
                self.wait(1.5, 's')
                if self.waking_up:
                    continue
                try:
                    status = check_output(['cat', f'/proc/asound/Fireface{self.get('card-model')}/firewire/status'], text=True, stderr=DEVNULL)
                    if status and not self.get('card-online'):
                        self.logger.info(f'Fireface {self.get('card-model')} found')
                        self.start_alsaset_process()
                except:
                    if self.get('card-online'):
                        self.logger.warning(f'Fireface disconnected, falling back to offline mode')
                        self.stop()
                        self.set('card-online', 0)


        def start_snd_process(self):
            """
            Start snd-fireface-ctl-service
            """
            cards = check_output(['cat', f'/proc/asound/cards'], text=True)
            for line in cards.split('\n'):
                if f'Fireface{self.get('card-model')}' in line:
                    card_number = line.split('[')[0].strip()
                    try:
                        self.snd_process = Popen(['snd-fireface-ctl-service', card_number], text=True)
                        self.logger.info('snd-firewire-ctl-services started')
                    except Exception as e:
                        self.logger.warning(f'error while starting snd-firewire-ctl-services ({e})')
                    break

        def start_alsaset_process(self):
            """
            Start amixer process
            """
            self.stop()
            try:
                self.start_snd_process()
                self.start_scene('wake_up', self.wake_up)
            except Exception as e:
                self.logger.warning(f'could not start amixer process\n{e}')

        def wake_up(self):
            """
            snd-firewire-ctl-services takes some time to take over the interface
            we must wait a little before pushing any value
            """
            self.waking_up = True

            while True:
                try:
                    test = check_output(['amixer', '-c', f'Fireface{self.get('card-model')}', 'cget', 'iface=CARD,name=\'active-clock-rate\'' ], text=True, stderr=DEVNULL)
                    break
                except:
                    self.wait(0.1, 's')

            self.alsaset_process = Popen(['amixer', '-c', f'Fireface{self.get('card-model')}', '-s', '-q'], stdin=PIPE, text=True)

            self.set('card-online', 1)


        def parameter_changed(self, mod, name, value):
            """
            Custom parameter update hooks
            """
            # device is back online
            if name == 'card-online' and value == 1:
                self.waking_up = False



        def alsa_set(self, alsa_lookup, value):
            """
            Alsa mixer set function, uses an interactive amixer instance
            """
            if type(value) is list:
                value = ",".join([str(x) for x in value])
            if type(value) is not str:
                value = str(value)

            if self.get('card-online'):
                self.alsaset_process.stdin.write('cset ' + alsa_lookup + ' ' + value + '\n')
                self.alsaset_process.stdin.flush()

        def alsa_get(self, name, alsa_lookup):
            """
            Alsa mixer get function, uses an amixer instance per call
            because it doesn't work with a interactive instance (cget is not supported)
            """
            if not self.get('card-online'):
                return []

            out = run(['amixer', '-c', f'Fireface{self.get('card-model')}', 'cget', alsa_lookup], stdout=PIPE, stderr=DEVNULL).stdout.decode('utf-8')
            for line in out.split('\n'):
                if ': values=' in line:
                    values = line.split('=')[1]
                    values = [int(v) for v in values.split(',')]
                    return values

            return []

        def stop(self):
            """
            Kill alsa processes when stopping
            """
            try:
                if self.snd_process:
                    self.snd_process.kill()
                    self.snd_process = None
                if self.alsaset_process:
                    self.alsaset_process.kill()
                    self.alsaset_process = None
            except:
                pass
