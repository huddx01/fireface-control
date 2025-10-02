from time import sleep
from math import log10
from mentat import Module

class FireFace(Module):

    def __init__(self, *args, alsamixer, **kwargs):

        super().__init__(name=alsamixer.get('card-model'))

        self.alsamixer = alsamixer

        self.add_event_callback('parameter_changed', self.parameter_changed)
        self.alsamixer.add_event_callback('parameter_changed', self.parameter_changed)

        self.add_parameter('card-model', None, types='s', default=self.alsamixer.get('card-model'), osc=True, skip_state=True)
        self.add_parameter('card-online', None, types='i', default=self.alsamixer.get('card-online'), osc=True, skip_state=True)

        """
        Card spec
        """
        if self.name == '802':

            self.inputs =  [(x, 'line', f'AN {x + 1}') for x in range(8)] + \
                           [(x, 'mic', f'MIC {x + 1}') for x in range(4)] + \
                           [(x, 'spdif', f'AES {x + 1}') for x in range(2)] + \
                           [(x, 'adat', f'ADAT {x + 1}') for x in range(16)]

            self.outputs = [(x, 'line', f'AN {x + 1}') for x in range(8)] + \
                           [(x, 'hp', f'PH {x + 9}') for x in range(4)] + \
                           [(x, 'spdif', f'AES {x + 1}') for x in range(2)] + \
                           [(x, 'adat', f'ADAT {x + 1}') for x in range(16)]

            self.mic_options = ['invert-phase', 'mic-instrument', 'mic-power']

            self.output_meters = {
                'meter:line-output':  range(8),
                'meter:hp-output': range(4),
                'meter:spdif-output': range(2),
                'meter:adat-output': range(16)
            }

        else: # UCX (untested)

            self.inputs = [(x, 'mic', f'MIC {x + 1}') for x in range(2)] + \
                          [(x, 'line', f'AN {x + 1}') for x in range(6)] + \
                          [(x, 'spdif', f'AES {x + 1}') for x in range(2)] + \
                          [(x, 'adat', f'ADAT {x + 1}') for x in range(8)]

            self.outputs =  [(x, 'line', f'AN {x + 1}') for x in range(6)] + \
                            [(x, 'hp', f'PH {x + 7}') for x in range(2)] + \
                            [(x, 'spdif', f'AES {x + 1}') for x in range(2)] + \
                            [(x, 'adat', f'ADAT {x + 1}') for x in range(8)]

            self.mic_options = ['invert-phase', 'mic-power']

            self.output_meters = {
                'meter:line-output':  range(6),
                'meter:hp-output': range(2),
                'meter:spdif-output': range(2),
                'meter:adat-output': range(8)
            }


        self.meter_noisefloor = -78
        self.default_eq_freqs = {'low':100, 'middle': 1000, 'high': 10000}
        self.default_eq_types = {'low': 1, 'middle': 0, 'high': 1} # 0 = peak, 1 = shelf, 2 = cut

        """
        Source mixers gain parameters
        """
        for out_index, (out_nth_of_type, out_type, out_name) in enumerate(self.outputs):
            for in_index, (in_nth_of_type, in_type, in_name) in enumerate(self.inputs):
                self.add_parameter(f'mixer:{in_type}-source-gain:{out_index}:{in_index}', None, types='i', default=32768)

            for in_type in ['line', 'mic', 'spdif', 'adat']:

                self.add_parameter(
                    f'mixer:{in_type}-source-gain:{out_index}',
                    None,
                    types='i' * len([x for x in self.inputs if in_type in x]),
                    alsa={'name': f'mixer:{in_type}-source-gain', 'index': out_index}
                )
                self.add_mapping(
                    src=[p.name for p in self.parameters.values() if f'mixer:{in_type}-source-gain:{out_index}:' in p.name],
                    dest=f'mixer:{in_type}-source-gain:{out_index}',
                    transform=lambda *v: list(v)
                )


        """
        Create output controls
        """
        for out_index, (out_nth_of_type, out_type, out_name) in enumerate(self.outputs):

            # read-only
            self.add_parameter(f'output:hardware-name:{out_index}', None, types='s', default=out_name, osc=True, skip_state=True)
            self.add_parameter(f'output:type:{out_index}', None, types='s', default=out_type, osc=True, skip_state=True)

            # gui options
            self.add_parameter(f'output:name:{out_index}', None, types='s', default='', osc=True)
            self.add_parameter(f'output:color:{out_index}', None, types='s', default='', osc=True)
            self.add_parameter(f'output:hide:{out_index}', None, types='i', default=0, osc=True, output_type=out_type)

            # volume + mute
            self.add_parameter(f'output:volume-db:{out_index}', None, types='f', default=0, osc=True)
            self.add_parameter(f'output:mute:{out_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:stereo:{out_index}', None, types='i', default=0, osc=True, state_order=-10)

            self.add_parameter(f'output:volume:{out_index}', None, types='i', default=0)
            self.add_mapping(
                src=[f'output:volume-db:{out_index}', f'output:mute:{out_index}', f'output:hide:{out_index}'],
                dest=f'output:volume:{out_index}',
                transform=lambda v, m, h: v*10 - (m+h) * 900,
            )

            # meter
            self.add_parameter(f'output:meter:{out_index}', None, types='f', default=-138, osc=True, output_type=out_type, skip_state=True)

            # channel options
            self.add_parameter(f'output:invert-phase:{out_index}', None, types='i', default=0, osc=True)

            # line options
            if out_type == 'line':
                self.add_parameter(f'output:line-level:{out_index}', None, types='i', default=1, osc=True)

            # fx sends
            self.add_parameter(f'output:fx-return:{out_index}', None, types='f', default=-65, osc=True, output_type=out_type)

            # eq
            self.add_parameter(f'output:eq-activate:{out_index}', None, types='i', default=0, osc=True)
            for band in ['low', 'middle', 'high']:
                self.add_parameter(f'output:eq-{band}-freq:{out_index}', None, types='i', default=self.default_eq_freqs[band], osc=True)
                self.add_parameter(f'output:eq-{band}-gain:{out_index}', None, types='i', default=0, osc=True)
                self.add_parameter(f'output:eq-{band}-quality:{out_index}', None, types='i', default=10, osc=True)
                if band != 'middle':
                    self.add_parameter(f'output:eq-{band}-type:{out_index}', None, types='i', default=self.default_eq_types[band], osc=True)

            self.add_parameter(f'output:hpf-activate:{out_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:hpf-activate-conditionnal:{out_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:hpf-cut-off:{out_index}', None, types='i', default=20, osc=True)
            self.add_parameter(f'output:hpf-roll-off:{out_index}', None, types='i', default=0, osc=True)

            # only activate hpf when eq is activated
            self.add_mapping(
                src=[f'output:eq-activate:{out_index}', f'output:hpf-activate-conditionnal:{out_index}'],
                dest=f'output:hpf-activate:{out_index}',
                transform=lambda eq, hpf: eq and hpf
            )

            # stream return : straight routing from stream sources
            self.add_parameter(f'output:stream-return:{out_index}', None, types='f', default=0, osc=True)
            self.add_parameter(f'mixer:stream-source-gain:{out_index}', None, types='i' * len(self.outputs), alsa={'name': 'mixer:stream-source-gain', 'index': out_index})
            def stream_return_mapping_factory(out_index):
                return lambda vol: [0] * (out_index) + [self.volume_pan_to_gains(vol, 0.5, False, in_range=[-65, 6], out_range=[32768, 40960])[0]] + [0] * (len(self.outputs) - out_index - 1)
            self.add_mapping(
                src=f'output:stream-return:{out_index}',
                dest=f'mixer:stream-source-gain:{out_index}',
                transform=stream_return_mapping_factory(out_index)
            )

            # monitor return: global dimmer for monitor mix
            self.add_parameter(f'output:monitor-return:{out_index}', None, types='f', default=0, osc=True)

            # dynamics
            self.add_parameter(f'output:dyn-activate:{out_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:dyn-attack:{out_index}', None, types='i', default=10, osc=True)
            self.add_parameter(f'output:dyn-release:{out_index}', None, types='i', default=300, osc=True)
            self.add_parameter(f'output:dyn-gain:{out_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:dyn-compressor-threshold:{out_index}', None, types='i', default=-300, osc=True)
            self.add_parameter(f'output:dyn-expander-threshold:{out_index}', None, types='i', default=-600, osc=True)
            self.add_parameter(f'output:dyn-compressor-ratio:{out_index}', None, types='i', default=10, osc=True)
            self.add_parameter(f'output:dyn-expander-ratio:{out_index}', None, types='i', default=10, osc=True)

            self.add_parameter(f'output:autolevel-activate:{out_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:autolevel-max-gain:{out_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:autolevel-head-room:{out_index}', None, types='i', default=30, osc=True)
            self.add_parameter(f'output:autolevel-rise-time:{out_index}', None, types='i', default=1, osc=True)

        # map single output params to array params for alsa
        output_alsa_params = [
            'output:volume', 'output:invert-phase', 'output:eq-activate', 'output:hpf-activate', 'output:hpf-cut-off', 'output:hpf-roll-off',
            'output:dyn-activate',  'output:dyn-attack',  'output:dyn-release',  'output:dyn-gain',
            'output:dyn-compressor-threshold',  'output:dyn-expander-threshold',  'output:dyn-compressor-ratio',  'output:dyn-expander-ratio',
            'output:autolevel-activate', 'output:autolevel-max-gain', 'output:autolevel-head-room', 'output:autolevel-rise-time'
            ]

        for band in ['low', 'middle', 'high']:
            for p in ['type', 'freq', 'gain', 'quality']:
                if band == 'middle' and p == 'type':
                    continue
                output_alsa_params.append(f'output:eq-{band}-{p}')

        for param in output_alsa_params:
            self.add_parameter(param, None, types='i' * len(self.inputs), alsa={})
            self.add_mapping(
                src=[f'{param}:{out_index}' for out_index, data in enumerate(self.inputs)],
                dest=param,
                transform=lambda *v: list(v)
            )

        # line option arrays
        self.add_parameter(f'output:line-level', None, types='i' * len([x for x in self.outputs if 'line' in x]), alsa={})
        self.add_mapping(
            src=[p.name for p in self.parameters.values() if f'output:line-level:' in p.name],
            dest=f'output:line-level',
            transform=lambda *v: list(v)
        )

        for out_type in ['line', 'hp', 'spdif', 'adat']:
            # fx return arrays
            self.add_parameter(f'fx:{out_type}-output-volume', None, types='i' * len([x for x in self.outputs if out_type in x]), alsa={})
            self.add_mapping(
                src=[p.name for p in self.parameters.values() if f'output:fx-return:' in p.name and p.metadata['output_type'] == out_type],
                dest=f'fx:{out_type}-output-volume',
                transform= lambda *return_gains: [x * 10 for x in return_gains]
            )

            # meters visibility
            self.add_parameter(f'output:{out_type}-meters-visible', None, types='i', default=1)
            self.add_mapping(
                src=[p.name for p in self.parameters.values() if f'output:hide:' in p.name and p.metadata['output_type'] == out_type],
                dest=f'output:{out_type}-meters-visible',
                transform= lambda *hidden: int(0 in hidden)
            )

            # meters value
            self.add_parameter(f'meter:{out_type}-output', None, types='i' * len([x for x in self.outputs if out_type in x]), alsa={'iface': 'CARD'}, skip_state=True)
            self.add_mapping(
                src=f'meter:{out_type}-output',
                dest=[p.name for p in self.parameters.values() if f'output:meter:' in p.name and p.metadata['output_type'] == out_type],
                transform= lambda values: [self.meter_abs_to_db(v) for v in values]
            )

        """
        Input options, eq & dyn
        """
        for in_index, (in_nth_of_type, in_type, in_name) in enumerate(self.inputs):

            # read-only
            self.add_parameter(f'input:hardware-name:{in_index}', None, types='s', default=in_name, osc=True, skip_state=True)
            self.add_parameter(f'input:type:{in_index}', None, types='s', default=in_type, osc=True, skip_state=True)

            # gui options
            self.add_parameter(f'input:name:{in_index}', None, types='s', default='', osc=True)
            self.add_parameter(f'input:color:{in_index}', None, types='s', default='', osc=True)
            self.add_parameter(f'input:hide:{in_index}', None, types='i', default=0, osc=True, input_type=in_type)

            # meter
            self.add_parameter(f'input:meter:{in_index}', None, types='f', default=-138, osc=True, input_type=in_type, skip_state=True)

            # line options
            if in_type == 'line':
                self.add_parameter(f'input:line-level:{in_index}', None, types='i', default=0, osc=True)

            # mic options
            if in_type == 'mic':
                for option in self.mic_options:
                    self.add_parameter(f'input:{option}:{in_index}', None, types='i', default=0, osc=True, input_type=in_type)

                # prevent mic inst + mic power state (also protected at driver level)
                if self.name == '802':
                    self.add_mapping(
                        src=f'input:mic-instrument:{in_index}',
                        dest=f'input:mic-power:{in_index}',
                        transform=lambda v: 1 - v,
                        condition=f'input:mic-instrument:{in_index}',
                    )
                    self.add_mapping(
                        src=f'input:mic-power:{in_index}',
                        dest=f'input:mic-instrument:{in_index}',
                        transform=lambda v: 1 - v,
                        condition=f'input:mic-power:{in_index}',
                    )

            # fx send
            self.add_parameter(f'input:fx-send:{in_index}', None, types='f', default=-65, osc=True, input_type=in_type)

            # eq
            self.add_parameter(f'input:eq-activate:{in_index}', None, types='i', default=0, osc=True)
            for band in ['low', 'middle', 'high']:
                self.add_parameter(f'input:eq-{band}-freq:{in_index}', None, types='i', default=self.default_eq_freqs[band], osc=True)
                self.add_parameter(f'input:eq-{band}-gain:{in_index}', None, types='i', default=0, osc=True)
                self.add_parameter(f'input:eq-{band}-quality:{in_index}', None, types='i', default=10, osc=True)
                if band != 'middle':
                    self.add_parameter(f'input:eq-{band}-type:{in_index}', None, types='i', default=self.default_eq_types[band], osc=True)

            self.add_parameter(f'input:hpf-activate:{in_index}', None, types='i', default=0)
            self.add_parameter(f'input:hpf-activate-conditionnal:{in_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'input:hpf-cut-off:{in_index}', None, types='i', default=20, osc=True)
            self.add_parameter(f'input:hpf-roll-off:{in_index}', None, types='i', default=0, osc=True)

            # only activate hpf when eq is activated
            self.add_mapping(
                src=[f'input:eq-activate:{in_index}', f'input:hpf-activate-conditionnal:{in_index}'],
                dest=f'input:hpf-activate:{in_index}',
                transform=lambda eq, hpf: eq and hpf
            )

            # dynamics
            self.add_parameter(f'input:dyn-activate:{in_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'input:dyn-attack:{in_index}', None, types='i', default=10, osc=True)
            self.add_parameter(f'input:dyn-release:{in_index}', None, types='i', default=300, osc=True)
            self.add_parameter(f'input:dyn-gain:{in_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'input:dyn-compressor-threshold:{in_index}', None, types='i', default=-300, osc=True)
            self.add_parameter(f'input:dyn-expander-threshold:{in_index}', None, types='i', default=-600, osc=True)
            self.add_parameter(f'input:dyn-compressor-ratio:{in_index}', None, types='i', default=10, osc=True)
            self.add_parameter(f'input:dyn-expander-ratio:{in_index}', None, types='i', default=10, osc=True)

            self.add_parameter(f'input:autolevel-activate:{in_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'input:autolevel-max-gain:{in_index}', None, types='i', default=0, osc=True)
            self.add_parameter(f'input:autolevel-head-room:{in_index}', None, types='i', default=30, osc=True)
            self.add_parameter(f'input:autolevel-rise-time:{in_index}', None, types='i', default=1, osc=True)


        # map single output params to array params for alsa
        input_alsa_params = [
            'input:eq-activate', 'input:hpf-activate', 'input:hpf-cut-off', 'input:hpf-roll-off',
            'input:dyn-activate',  'input:dyn-attack',  'input:dyn-release',  'input:dyn-gain',
            'input:dyn-compressor-threshold',  'input:dyn-expander-threshold',  'input:dyn-compressor-ratio',  'input:dyn-expander-ratio',
            'input:autolevel-activate', 'input:autolevel-max-gain', 'input:autolevel-head-room', 'input:autolevel-rise-time'
        ]

        for band in ['low', 'middle', 'high']:
            for p in ['type', 'freq', 'gain', 'quality']:
                if band == 'middle' and p == 'type':
                    continue
                input_alsa_params.append(f'input:eq-{band}-{p}')

        for param in input_alsa_params:
            self.add_parameter(param, None, types='i'*len(self.inputs), alsa={})
            self.add_mapping(
                src=[f'{param}:{inp}' for inp, data in enumerate(self.inputs)],
                dest=param,
                transform=lambda *v: list(v)
            )

        # line options arrays
        self.add_parameter(f'input:line-level', None, types='i' * len([x for x in self.inputs if 'line' in x]), alsa={})
        self.add_mapping(
            src=[p.name for p in self.parameters.values() if f'input:line-level:' in p.name],
            dest=f'input:line-level',
            transform=  lambda *v: list(v)
        )

        # mic options arrays
        for option in self.mic_options:
            self.add_parameter(f'input:{option}', None, types='i' * len([x for x in self.inputs if 'mic' in x]), alsa={})
            self.add_mapping(
                src=[p.name for p in self.parameters.values() if f'input:{option}:' in p.name],
                dest=f'input:{option}',
                transform=lambda *v: list(v)
            )

        for in_type in ['line', 'mic', 'spdif', 'adat']:
            # fx sends arrays
            self.add_parameter(f'fx:{in_type}-source-gain', None, types='i' * len([x for x in self.inputs if in_type in x]), alsa={})
            self.add_mapping(
                src=[p.name for p in self.parameters.values() if f'input:fx-send:' in p.name and p.metadata['input_type'] == in_type],
                dest=f'fx:{in_type}-source-gain',
                transform=lambda *gains: [x * 10 for x in gains]
            )

            # meters visibility
            self.add_parameter(f'input:{in_type}-meters-visible', None, types='i', default=1)
            self.add_mapping(
                src=[p.name for p in self.parameters.values() if f'input:hide:' in p.name and p.metadata['input_type'] == in_type],
                dest=f'input:{in_type}-meters-visible',
                transform= lambda *hidden: int(0 in hidden)
            )

            # meters value
            self.add_parameter(f'meter:{in_type}-input', None, types='i' * len([x for x in self.inputs if in_type in x]), alsa={'iface': 'CARD'}, skip_state=True)
            self.add_mapping(
                src=f'meter:{in_type}-input',
                dest=[p.name for p in self.parameters.values() if f'input:meter:' in p.name and p.metadata['input_type'] == in_type],
                transform= lambda values: [self.meter_abs_to_db(v) for v in values]
            )

        """
        Meters
        """
        self.add_parameter('metering', None, types='i', default=0, alsa={}, osc=True)

        """
        Monitor mixers
        """
        for out_index, (out_nth_of_type, out_type, out_name) in enumerate(self.outputs):

            stereo_index = int(out_index / 2) * 2

            lambda_volume_stereo = lambda volume, pan, mute, hide, dimmer: self.volume_pan_to_gains(volume, pan, mute or hide, in_range=[-65,6], out_range=[32768, 40960], dimmer_gain=dimmer)
            lambda_volume_mono = lambda *a, **k: lambda_volume_stereo(*a, **k)[0]

            # create gain, mute and pan controls for every input
            # and map them to the appropriate mixer source gains
            for in_index, (in_nth_of_type, in_type, in_name) in enumerate(self.inputs):

                self.add_parameter(f'monitor:input-gain:{out_index}:{in_index}', None, types='f', default=-65, osc=True)
                self.add_parameter(f'monitor:input-pan:{out_index}:{in_index}', None, types='f', default=0.5, osc=True)
                self.add_parameter(f'monitor:input-mute:{out_index}:{in_index}', None, types='i', default=0, osc=True)

                # Mono mapping
                self.add_mapping(
                    src = [
                        f'monitor:input-gain:{out_index}:{in_index}',
                        f'monitor:input-pan:{out_index}:{in_index}',
                        f'monitor:input-mute:{out_index}:{in_index}',
                        f'input:hide:{in_index}',
                        f'output:monitor-return:{out_index}'
                    ],
                    dest = f'mixer:{in_type}-source-gain:{out_index}:{in_index}',
                    transform = lambda_volume_mono,
                    condition = f'output:stereo:{stereo_index}',
                    condition_test = lambda stereo: not stereo
                )

            if out_index % 2 == 0:
                # first channel of every stereo pair

                for in_index, (in_nth_of_type, in_type, in_name) in enumerate(self.inputs):
                    # Stereo mapping
                    self.add_mapping(
                        src = [
                            f'monitor:input-gain:{out_index}:{in_index}',
                            f'monitor:input-pan:{out_index}:{in_index}',
                            f'monitor:input-mute:{out_index}:{in_index}',
                            f'input:hide:{in_index}',
                            f'output:monitor-return:{out_index}'
                        ],
                        dest = [f'mixer:{in_type}-source-gain:{index}:{in_index}' for index in (out_index, out_index + 1)],
                        transform = lambda_volume_stereo,
                        condition = f'output:stereo:{stereo_index}'
                    )

                linked_params = [
                    'output:hide', 'output:volume-db', 'output:mute', 'output:name', 'output:color',
                    'output:eq-activate', 'output:hpf-activate-conditionnal', 'output:hpf-cut-off', 'output:hpf-roll-off',
                    'output:dyn-activate',  'output:dyn-attack',  'output:dyn-release',  'output:dyn-gain',
                    'output:dyn-compressor-threshold',  'output:dyn-expander-threshold',  'output:dyn-compressor-ratio', 'output:dyn-expander-ratio',
                    'output:stream-return', 'output:monitor-return', 'output:fx-return']

                for band in ['low', 'middle', 'high']:
                    for p in ['type', 'freq', 'gain', 'quality']:
                        if band == 'middle' and p == 'type':
                            continue
                        linked_params.append(f'output:eq-{band}-{p}')

                if out_type == 'line':
                    linked_params.append('output:line-level')

                # link outputs
                for param in linked_params:
                    self.add_mapping(
                        src = f'{param}:{out_index}',
                        dest = f'{param}:{out_index + 1}',
                        transform = lambda v: v,
                        condition = f'output:stereo:{stereo_index}'
                    )

                for param in ['output:stereo']:
                    self.add_mapping(
                        src = f'{param}:{out_index}',
                        dest = f'{param}:{out_index + 1}',
                        transform = lambda v: v,
                        inverse = lambda v: v,
                    )

                self.add_parameter(f'output:pan:{out_index}', None, types='f', default=0.5, osc=True, state_order=-9)

        """
        Stereo outputs
        """
        n_stereo_pairs = int(len(self.outputs) / 2)
        # dsp stereo link, needed for stereo fx
        self.add_parameter('output:stereo-link', None, types='i' * n_stereo_pairs , alsa={}, state_order=-2)
        self.add_mapping(
            src=[f'output:stereo:{index}' for index in range(0, len(self.outputs), 2)],
            dest='output:stereo-link',
            transform= lambda *stereo: list(stereo)
        )
        self.add_parameter('output:stereo-balance', None, types='i' * n_stereo_pairs, default=[0] * n_stereo_pairs, alsa={}, state_order=-1)
        self.add_mapping(
            src=[f'output:pan:{index}' for index in range(0, len(self.outputs), 2)],
            dest='output:stereo-balance',
            transform= lambda *pan: [p * 200 - 100 for p in pan]
        )

        """
        FX (reverb & echo)
        """
        self.add_parameter('fx:echo-activate', None, types='i', default=0, osc=True, alsa={})
        self.add_parameter('fx:echo-delay', None, types='i', default=10, alsa={})
        self.add_parameter('fx:echo-feedback', None, types='i', default=0, osc=True, alsa={})
        self.add_parameter('fx:echo-lpf-freq', None, types='i', default=0, osc=True, alsa={})
        self.add_parameter('fx:echo-stereo-width', None, types='i', default=100, osc=True, alsa={})
        self.add_parameter('fx:echo-type', None, types='i', default=0, osc=True, alsa={})
        self.add_parameter('fx:echo-volume', None, types='i', default=0, alsa={})

        self.add_parameter('fx:echo-volume-db', None, types='i', default=0, osc=True)
        self.add_parameter('fx:echo-delay-s', None, types='f', default=0.1, osc=True)

        self.add_mapping(
            src='fx:echo-volume-db',
            dest='fx:echo-volume',
            transform= lambda gain: 10 * gain
        )

        self.add_mapping(
            src='fx:echo-delay-s',
            dest='fx:echo-delay',
            transform= lambda time: 100 * time
        )

        self.add_parameter('fx:reverb-activate', None, types='i', default=0, osc=True, alsa={})
        self.add_parameter('fx:reverb-attack', None, types='i', default=100, osc=True, alsa={})
        self.add_parameter('fx:reverb-hold', None, types='i', default=300, osc=True, alsa={})
        self.add_parameter('fx:reverb-release', None, types='i', default=250, osc=True, alsa={})
        self.add_parameter('fx:reverb-type', None, types='i', default=0, osc=True, alsa={})
        self.add_parameter('fx:reverb-room-scale', None, types='i', default=100, osc=True, alsa={})
        self.add_parameter('fx:reverb-smooth', None, types='i', default=100, osc=True, alsa={})
        self.add_parameter('fx:reverb-stereo-width', None, types='i', default=100, osc=True, alsa={})
        self.add_parameter('fx:reverb-time', None, types='i', default=10, osc=True, alsa={})
        self.add_parameter('fx:reverb-volume', None, types='i', default=0, osc=True, alsa={})
        self.add_parameter('fx:reverb-damping', None, types='i', default=20000, osc=True, alsa={})
        self.add_parameter('fx:reverb-post-lpf-freq', None, types='i', default=20000, osc=True, alsa={})
        self.add_parameter('fx:reverb-pre-delay', None, types='i', default=0, osc=True, alsa={})
        self.add_parameter('fx:reverb-pre-hpf-freq', None, types='i', default=0, osc=True, alsa={})

        self.add_parameter('fx:reverb-volume-db', None, types='i', default=0, osc=True)
        self.add_parameter('fx:reverb-time-s', None, types='f', default=1, osc=True)

        self.add_mapping(
            src='fx:reverb-volume-db',
            dest='fx:reverb-volume',
            transform= lambda gain: 10 * gain
        )
        self.add_mapping(
            src='fx:reverb-time-s',
            dest='fx:reverb-time',
            transform= lambda time: 10 * time
        )

        """
        Clock and Sync parameters
        """
        # Read-only parameters (alsa param + skip_state meta = read-only)
        self.add_parameter('active-clock-rate', None, types='i', default=2, alsa={'iface': 'CARD'}, osc=True, skip_state=True, poll=True)
        self.add_parameter('active-clock-source', None, types='i', default=0, alsa={'iface': 'CARD'}, osc=True, skip_state=True, poll=True)


        for name in ['external-source-lock', 'external-source-rate', 'external-source-sync']:

            for i in range(4):
                self.add_parameter(f'{name}:{i}', None, types='i', default=0, osc=True, skip_state=True)

            self.add_parameter(name, None, types='iiii', default=[0] * 4, alsa={'iface': 'CARD'}, skip_state=True, poll=True)

            self.add_mapping(
                src=name,
                dest=[f'{name}:{i}' for i in range(4)],
                transform=lambda lock:lock
            )

        # Writable parameters
        self.add_parameter('primary-clock-source', None, types='i', default=0, alsa={'iface': 'CARD'}, osc=True)
        self.add_parameter('optical-output-signal', None, types='i', default=0, alsa={'iface': 'CARD'}, osc=True)
        self.add_parameter('spdif-input-interface', None, types='i', default=0, alsa={'iface': 'CARD'}, osc=True)
        self.add_parameter('spdif-output-format', None, types='i', default=1, alsa={'iface': 'CARD'}, osc=True)
        self.add_parameter('word-clock-single-speed', None, types='i', default=0, alsa={'iface': 'CARD'}, osc=True)

        """
        Other settings
        """
        self.add_parameter('effect-on-input', None, types='i', default=0, alsa={}, osc=True)

        """
        Channel selection
        """
        self.add_parameter('input:select', None, types='i', default=0, osc=True, state_order=10)
        self.add_parameter('output:select', None, types='i', default=0, osc=True, state_order=10)

        """
        Gui constants
        """
        self.add_parameter('inputs', None, types='i', default=len(self.inputs), osc=True, skip_state=True, state_order=-2)
        self.add_parameter('outputs', None, types='i', default=len(self.outputs), osc=True, skip_state=True, state_order=-2)

        """
        Misc gui options
        """
        self.add_parameter('show-eq', None, types='i', default=1, osc=True)
        self.add_parameter('show-dyn', None, types='i', default=1, osc=True)
        self.add_parameter('show-fx', None, types='i', default=1, osc=True)
        self.add_parameter('show-hw', None, types='i', default=1, osc=True)

        self.add_parameter('state-slots', None, types='s', default='', osc=True, skip_state=True)
        self.add_parameter('current-state', None, types='s', default='', osc=True, skip_state=True)

        self.add_parameter('gui-clients', None, types='i', default=0, skip_state=True)


        self.update_state_list()
        self.loading_state = False

        self.engine.add_event_callback('started', lambda: self.start_scene('engine_started', self.engine_started))


        self.alsa_parameters = {}
        self.alsa_poll_parameters = {}
        for name in self.parameters:
            if 'alsa' in self.parameters[name].metadata:
                self.alsa_parameters[name] = self.parameters[name]
                if 'poll' in self.parameters[name].metadata:
                    self.alsa_poll_parameters[name] = self.parameters[name]


        self.logger.info(f'initialized with {len(self.parameters.items())} parameters and {len(self.mappings)} mappings')

    def engine_started(self):
        """
        Engine started callback
        """
        # Start polling
        self.start_scene('poll_alsa_parameters', self.poll_alsa_parameters)

        # remove invalid params from states
        for statename in self.states:
            for s in self.states[statename]:
                valid_state = [x for x in self.states[statename] if self.get_parameter(x[0])]
                if len(valid_state) != len(self.states[statename]):
                    invalid_param = [x[0] for x in self.states[statename] if not self.get_parameter(x[0])]
                    self.logger.warning(f'invalid parameters found in state {statename}, they will be ignored: {invalid_param}')
                    self.states[statename] = valid_state
                    break

        # auto load last state ?
        if self.engine.get('Settings', 'autoload-state'):
            statename = self.engine.get('Settings', 'last-state')
            if statename in self.states:
                self.load(statename)


    def poll_alsa_parameters(self):
        """
        Periodically update parameters that might change
        """
        while True:
            self.wait(1, 's')  # Update every second

            for name in self.alsa_poll_parameters:
                lookup = self.param_to_alsa_lookup(name)
                values = self.alsamixer.alsa_get(lookup)
                if values:
                    self.set(name, *values)

    def update_meters(self):
        """
        Fetch meter values periodically
        """
        while True:
            self.wait(1/20, 's')

            if self.get('gui-clients') == 0:
                # bypass meter polling if there's no client connected
                continue

            for chnl_type in ['line', 'mic', 'spdif', 'adat']:

                if self.get(f'input:{chnl_type}-meters-visible'):
                    name = f'meter:{chnl_type}-input'
                    lookup = self.param_to_alsa_lookup(name)
                    meter_values = self.alsamixer.alsa_get(lookup)
                    if meter_values:
                        self.set(name, *meter_values)

            for chnl_type in ['line', 'hp', 'spdif', 'adat']:

                if self.get(f'output:{chnl_type}-meters-visible'):
                    name = f'meter:{chnl_type}-output'
                    lookup = self.param_to_alsa_lookup(name)
                    meter_values = self.alsamixer.alsa_get(lookup)
                    if meter_values:
                        self.set(name, *meter_values)

    def meter_abs_to_db(self, v):
        """
        Convert meter value to dBs
        """
        if v == 0:
            v = -138
        else:
            v = 20*log10(v / 134217712)
            v = round(v*10) / 10
            if v < self.meter_noisefloor:
                v = -138
        return v

    def param_to_alsa_lookup(self, name):

        alsadata = self.get_parameter(name).metadata['alsa']

        # use cache lookup stinkg
        if 'lookup' in alsadata:
            return alsadata['lookup']

        name = alsadata['name'] if 'name' in alsadata else name
        iface = alsadata['iface'] if 'iface' in alsadata else 'MIXER'
        lookup = f'iface={iface},name="{name}"'

        if 'index' in alsadata:
            lookup += f',index={alsadata['index']}'

        # cache lookup stinkg
        alsadata['lookup'] = lookup

        return lookup

    def alsa_send(self, name, value):
        """
        Prepare message for alsamixer
        """
        lookup = self.param_to_alsa_lookup(name)

        if name == 'output:stereo-link':
            # workaround a bug (in driver or firmware ?) that makes stereo balance toward left ignored
            # when stereo link is off. part 1: reset balance and wait a bit (doesn't work otherwise)
            self.alsa_send('output:stereo-balance', [0]* int(len(self.outputs) / 2))
            sleep(0.1)

        self.alsamixer.alsa_set(lookup, value)

        if name == 'output:stereo-link':
            # workaround part 2: retore balance
            self.alsa_send('output:stereo-balance', self.get('output:stereo-balance'))



    def parameter_changed(self, mod, name, value):
        """
        Custom parameter update hooks
        """
        # Mirror some parameters of alsamixer module
        if mod == self.alsamixer:
            if self.get_parameter(name):
                self.set(name, value)
            return

        # Update Alsa mixer (amixer) when a parameter with the alsa flag updates
        if 'alsa' in mod.parameters[name].metadata and 'skip_state' not in mod.parameters[name].metadata:
            self.alsa_send(name, value)

        # card is back online: sync it
        if name == 'card-online' and value == 1:
            self.logger.info('card is online, syncing')

            state = self.get_alsa_state()
            for s in state:
                self.alsa_send(s[0], s[1:])

        # Start/stop metering thread and reset meters when it stops
        if name == 'metering':
            if value == 0:
                self.stop_scene('meters')
                for n in self.parameters:
                    if '-meter:' in n:
                        self.set(n, -138)
            else:
                self.start_scene('meters', self.update_meters)

        # stereo output link change
        if 'output:stereo:' in name:
            dest = int(name.split(':')[-1])
            # force meter update
            self.reset(f'output-meter:{int(dest/2)*2}')
            self.reset(f'output-meter:{int(dest/2)*2+1}')
            if dest % 2 == 0:
                # rename stereo outputs
                if value == 1:
                    nx2 = self.outputs[dest][2].split(' ')[-1]
                    self.set(f'output:hardware-name:{dest}', f'{self.outputs[dest][2]}/{int(nx2)+1}')
                    for param in ['output:volume-db', 'output:mute', 'output:name', 'output:color']:
                        self.set(f'{param}:{dest + 1}' ,self.get(f'{param}:{dest}'))
                else:
                    self.reset(f'output:hardware-name:{dest}')
            else:
                # switch mixer selection to stereo channel if previously on future right channel
                if value == 1 and self.get('output:select') == dest:
                    self.set('output:select', dest - 1)

            # reset gain/pan/mute when stereo changes
            if not self.loading_state and dest % 2 == 0 and value == 0:

                for in_index, (in_nth_of_type, in_type, in_name) in enumerate(self.inputs):
                    mute = self.get(f'monitor:input-mute:{dest}:{in_index}')

                    if value == 1:
                        gain = max(self.get(f'monitor:input-gain:{dest}:{in_index}'),
                                    self.get(f'monitor:input-gain:{dest + 1}:{in_index}'))
                    else:
                        gain = self.get(f'monitor:input-gain:{dest}:{in_index}')


                    # apply gain
                    self.set(f'monitor:input-gain:{dest}:{in_index}', gain)
                    self.set(f'monitor:input-gain:{dest + 1}:{in_index}', gain)
                    if value == 0:
                        # reset pan
                        self.reset(f'output:pan:{dest}')
                        self.reset(f'monitor:input-pan:{dest}:{in_index}')
                        self.reset(f'monitor:input-pan:{dest + 1}:{in_index}')
                        # copy mute
                        self.set(f'monitor:input-mute:{dest}:{in_index}', mute)
                        self.set(f'monitor:input-mute:{dest + 1}:{in_index}', mute)


    def volume_pan_to_gains(self, vol, pan, mute, in_range, out_range, dimmer_gain=0):

        # apply mute
        if mute or dimmer_gain <= in_range[0] or vol <= in_range[0]:
            return [out_range[0], out_range[0]]
        # apply dimmer
        if vol > in_range[0]:
            vol = min(max(vol + dimmer_gain, in_range[0]), in_range[1])

        # db to linear coef
        g1 = g2 = pow(10, (vol-6)/20)

        # apply simple pan: linear attenuation of the weakest side
        pan = max(0, min(1, pan))
        if pan < 0.5:
            g2 *= pan * 2
        elif pan > 0.5:
            g1 *= 2 - 2 * pan

        # map to out range
        g1 = int(g1 * (out_range[1]-out_range[0])) + out_range[0]
        g2 = int(g2 * (out_range[1]-out_range[0])) + out_range[0]

        return [g1, g2]


    def get_state(self, *args, **kwargs):
        """
        Only save what's needed to manage the app's state.
        We only need what's controllable from the ui, all the rest is reset
        to defaults at startup and when loading a state file.
        """

        state = super().get_state(*args, **kwargs)
        state = [p for p in state if 'osc' in self.get_parameter(p[0]).metadata and 'skip_state' not in self.get_parameter(p[0]).metadata]

        state = sorted(state, key=lambda p: self.get_parameter(p[0]).metadata['state_order'] if 'state_order' in self.get_parameter(p[0]).metadata else 0)

        return state

    def get_alsa_state(self, *args, **kwargs):
        """
        Get what's needed to manage the cards's state.
        """

        state = super().get_state(*args, **kwargs)
        state = [p for p in state if 'alsa' in self.get_parameter(p[0]).metadata]
        state = sorted(state, key=lambda p: self.get_parameter(p[0]).metadata['state_order'] if 'state_order' in self.get_parameter(p[0]).metadata else 0)

        return state


    def begin_loading_state(self):
        """
        We need to prevent some param change callbacks when loading a state
        """
        self.loading_state = True
        def done():
            with self.engine.lock():
                self.loading_state = False

        self.start_scene('loading_state', done)

    def load(self, name, force_send=False, preload=False):
        """
        Keep track of last state
        """
        if not preload:
            self.begin_loading_state()

        super().load(name, force_send, preload)

        if not preload:
            self.set('current-state', name)
            self.engine.set('Settings', 'last-state', name)

    def save(self, name, omit_defaults=False):
        """
        Keep track of available states & last state
        """
        super().save(name, omit_defaults)

        self.set('current-state', name)
        self.engine.set('Settings', 'last-state', name)

        self.update_state_list()

    def delete(self, name):
        """
        Keep track of available states
        """
        super().delete(name)

        if self.engine.get('Settings', 'last-state') == name:
            self.engine.set('Settings', 'last-state', '')

        self.update_state_list()

    def soft_reset(self):
        """
        Soft reset for parameters that should persist (eg current state name)
        """
        self.begin_loading_state()

        state = []
        for name in self.parameters:
            p = self.get_parameter(name)
            if 'skip_state' not in p.metadata and p.default is not None:
                if isinstance(p.default, list):
                    state.append([name, *p.default])
                else:
                    state.append([name, p.default])

        state = sorted(state, key=lambda p: self.get_parameter(p[0]).metadata['state_order'] if 'state_order' in self.get_parameter(p[0]).metadata else 0)
        self.set_state(state)

    def update_state_list(self):
        """
        Alpha sort state names
        """
        slist = list(self.states.keys())
        slist.sort()
        self.set('state-slots', '::'.join(slist))
