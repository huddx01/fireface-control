from math import log10
from alsamixer import AlsaMixer

class FireFace802(AlsaMixer):

    mixer_sources = {
        'mixer:line-source-gain':  [f'AN {x + 1}' for x in range(8)],
        'mixer:mic-source-gain': [f'MIC {x + 1}' for x in range(4)],
        'mixer:spdif-source-gain': [f'AES {x + 1}' for x in range(2)],
        'mixer:adat-source-gain': [f'ADAT {x + 1}' for x in range(16)]
    }

    mixer_outputs = range(30)


    mixer_outputs_default_names = [f'AN {x + 1}' for x in range(8)] + \
                                       ['PH 9', 'PH 10'] + \
                                       ['PH 11', 'PH 12'] + \
                                       [f'AES {x + 1}' for x in range(2)] + \
                                       [f'ADAT {x + 1}' for x in range(16)]


    output_meters = {
        'meter:line-output':  range(8),
        'meter:hp-output': range(4),
        'meter:spdif-output': range(2),
        'meter:adat-output': range(16)
    }
    meter_noisefloor = -85

    stereo_mixers = {
        8: 'RME 1',
        10: 'RME 2',
        14: 'AES',
    }



    def __init__(self, *args, **kwargs):

        super().__init__(name='Fireface802', *args, **kwargs)

        """
        Source mixers gain parameters
        """
        for (mixer, sources) in self.mixer_sources.items():

            for output in self.mixer_outputs:

                for source, source_name in enumerate(sources):
                    self.add_parameter(f'{mixer}:{output}:{source}', None, types='i', default=0)


                self.add_parameter(f'{mixer}:{output}', None, types='i' * len(sources), alsa=f'name="{mixer}",index={output}')

                self.add_mapping(
                    src=[f'{mixer}:{output}:{source}' for source, source_name in enumerate(sources)],
                    dest=f'{mixer}:{output}',
                    transform=lambda *v: list(v)
                )


        """
        Create output controls
        """
        for dest in self.mixer_outputs:
            self.add_parameter(f'output:volume:{dest}', None, types='i', default=0)
            self.add_parameter(f'output:volume-db:{dest}', None, types='f', default=0, osc=True)
            self.add_parameter(f'output:mute:{dest}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:hardware-name:{dest}', None, types='s', default=self.mixer_outputs_default_names[dest], osc=True)
            self.add_parameter(f'output:name:{dest}', None, types='s', default='', osc=True)
            self.add_parameter(f'output:color:{dest}', None, types='s', default='', osc=True)
            self.add_parameter(f'output:hide:{dest}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:stereo:{dest}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:mono:{dest}', None, types='i', default=0, osc=True)

            self.add_mapping(
                src=[f'output:volume-db:{dest}', f'output:mute:{dest}', f'output:hide:{dest}'],
                dest=f'output:volume:{dest}',
                transform=lambda v, m, h: v*10 - (m+h) * 900,
            )

            self.add_mapping(
                src=f'output:stereo:{dest}',
                dest=f'output:mono:{dest}',
                transform=lambda v: not v,
            )



        self.add_parameter(f'output:volume', None, types='i'*len(self.mixer_outputs), alsa='')

        self.add_mapping(
            src=[f'output:volume:{dest}' for dest in self.mixer_outputs],
            dest='output:volume',
            transform=lambda *v: list(v)
        )



        """
        Sources gui custom parameters (name, colors, etc)
        """
        sources_types = []
        sources_ids = []

        for (mixer, sources) in self.mixer_sources.items():

            sourcetype = mixer.split(':')[1].split('-')[0]

            for source, source_name in enumerate(sources):

                self.add_parameter(f'source-{sourcetype}-hardware-name:{source}', None, types='s', default=source_name, osc=True)
                self.add_parameter(f'source-{sourcetype}-name:{source}', None, types='s', default='', osc=True)
                self.add_parameter(f'source-{sourcetype}-color:{source}', None, types='s', default='', osc=True)
                self.add_parameter(f'source-{sourcetype}-hide:{source}', None, types='i', default=0, osc=True)

                sources_types.append(sourcetype)
                sources_ids.append(source)

        self.add_parameter('sources-types', None, types='s'*len(sources_types), default=sources_types, osc=True, osc_order=-2)
        self.add_parameter('sources-ids', None, types='i'*len(sources_ids), default=sources_ids, osc=True, osc_order=-2)

        """
        Input options
        """
        for option in ['invert-phase', 'mic-instrument', 'mic-power']:
            for i in range(4):
                self.add_parameter(f'input:{option}:{i}', None, types='i', default=0, osc=True)

            self.add_parameter(f'input:{option}', None, types='iiii', alsa='')
            self.add_mapping(
                src=[f'input:{option}:{i}' for i in range(4)],
                dest=f'input:{option}',
                transform=lambda *v: list(v)
            )

        """
        Meters
        """

        for (mixer, sources) in self.mixer_sources.items():

            sourcetype = mixer.split(':')[1].split('-')[0]

            for source, source_name in enumerate(sources):

                self.add_parameter(f'source-{sourcetype}-meter:{source}', None, types='f', default=-90, osc=True)

            self.add_parameter(f'source-{sourcetype}-meters-visible', None, types='i', default=1)
            self.add_mapping(
                src=[f'source-{sourcetype}-hide:{source}' for source, source_name in enumerate(sources)],
                dest=f'source-{sourcetype}-meters-visible',
                transform= lambda *hidden: int(0 in hidden)
            )

        out_index = -1
        for (output_meter, outputs) in self.output_meters.items():
            outputtype = output_meter.split(':')[1].split('-')[0]

            for output in outputs:
                out_index += 1
                self.add_parameter(f'output-meter:{out_index}', None, types='f', default=-90, osc=True)

            self.add_parameter(f'output-{outputtype}-meters-visible', None, types='i', default=1)
            self.add_mapping(
                src=[f'output:hide:{dest + out_index - len(outputs) + 1}' for dest in outputs],
                dest=f'output-{outputtype}-meters-visible',
                transform= lambda *hidden: int(0 in hidden)
            )

        self.add_parameter('metering', None, types='s', default='on', alsa='', osc=True)

        """
        Mixers
        """
        for index in self.mixer_outputs:
            self.create_mixer(index)


        self.add_parameter('output-ids', None, types='i' * len(self.mixer_outputs), default=list(self.mixer_outputs), osc=True, osc_order=-1)
        self.add_parameter('output-stereo', None, types='i' * len(self.mixer_outputs), osc=True, osc_order=-1)

        self.add_mapping(
            src=[f'output:stereo:{index}' for index in self.mixer_outputs],
            dest='output-stereo',
            transform= lambda *stereo: list(stereo)
        )


        self.add_parameter('mixers:select', None, types='i', default=0, osc=True)




    def update_meters(self):
        """
        Fetch meter values periodically
        """
        while True:
            self.wait(1/20, 's')

            for (mixer, sources) in self.mixer_sources.items():

                sourcetype = mixer.split(':')[1].split('-')[0]
                if self.get(f'source-{sourcetype}-meters-visible') == 1:

                    meters = self.alsa_get(f'meter:{sourcetype}-input', f'name="meter:{sourcetype}-input",iface=CARD')
                    if meters:
                        for i, v in enumerate(meters):
                            self.set(f'source-{sourcetype}-meter:{i}', self.meter_abs_to_db(v))


            out_index = -1
            for (output_meter, outputs) in self.output_meters.items():

                    outputtype = output_meter.split(':')[1].split('-')[0]
                    if self.get(f'output-{outputtype}-meters-visible') == 1:
                        meters = self.alsa_get(output_meter, f'name="{output_meter}",iface=CARD')
                        if meters:
                            for i, v in enumerate(meters):
                                out_index += 1
                                self.set(f'output-meter:{out_index}', self.meter_abs_to_db(v))
                    else:
                        out_index += len(outputs)

    def meter_abs_to_db(self, v):
        """
        Convert meter value to dBs
        """
        v = 20*log10(max(v / 134217712,0.00001))
        v = round(v*10) / 10
        if v < self.meter_noisefloor:
            v = -90
        return v


    def parameter_changed(self, mod, name, value):
        """
        Custom parameter update hooks
        """

        super().parameter_changed(mod, name, value)

        # Start/stop metering thread and reset meters when it stops
        if name == 'metering':
            if value == 'off':
                self.stop_scene('meters')
                for n in self.parameters:
                    if '-meter:' in n:
                        self.set(n, -90)
            else:
                self.start_scene('meters', self.update_meters)

        # stereo output link change
        if 'output:stereo:' in name:
            dest = int(name.split(':')[-1])
            def sc():
                # force meter update
                self.reset(f'output-meter:{int(dest/2)*2}')
                self.reset(f'output-meter:{int(dest/2)*2+1}')
                if dest % 2 == 0:
                    # rename stereo outputs
                    if value == 1:
                        nx2 = self.mixer_outputs_default_names[dest].split(' ')[-1]
                        self.set(f'output:hardware-name:{dest}', f'{self.mixer_outputs_default_names[dest]}/{int(nx2)+1}')
                        for param in ['output:volume-db', 'output:mute', 'output:name', 'output:color']:
                            self.set(f'{param}:{dest + 1}' ,self.get(f'{param}:{dest}'))
                    else:
                        self.reset(f'output:hardware-name:{dest}')
                else:
                    # switch mixer selection to stereo channel if previously on future right channel
                    if value == 1 and self.get('mixers:select') == dest:
                        self.set('mixers:select', dest - 1)

            # reset gain/pan/mute
            for (mixer, sources) in self.mixer_sources.items():
                for source, source_name in enumerate(sources):
                    self.reset(f'{mixer.replace('mixer', 'monitor')}:{dest}:{source}')
                    self.reset(f'{mixer.replace('mixer', 'monitor').replace('gain', 'pan')}:{dest}:{source}')
                    self.reset(f'{mixer.replace('mixer', 'monitor').replace('gain', 'mute')}:{dest}:{source}')

            self.start_scene(name, sc)

    def create_mixer(self, index):
        """
        Create mixers
        """
        stereo_index = int(index/2) * 2
        lambda_is_stereo = lambda: self.get_parameter(f'output:stereo:{stereo_index}') and self.get(f'output:stereo:{stereo_index}') == 1
        lambda_is_mono = lambda: self.get_parameter(f'output:stereo:{stereo_index}') and self.get(f'output:stereo:{stereo_index}') == 0

        # this doesn't work well (https://github.com/alsa-project/snd-firewire-ctl-services/issues/194)
        # lambda_volume_stereo = lambda volume, pan, mute, hide: self.volume_pan_to_gains(volume, pan, mute or hide, in_range=[-65,6], out_range=[32768, 40960])
        # instead, we hack the negative gain scale (-65 to 0dB) with some magic power
        lambda_volume_stereo = lambda volume, pan, mute, hide: self.volume_pan_to_gains_hack(volume, pan, mute or hide, in_range=[-65,6], out_range=[32768, 40960])
        
        lambda_volume_mono = lambda *a, **k: lambda_volume_stereo(*a, **k)[0]


        # create gain, mute and pan controls for every input
        # and map them to the appropriate mixer source gains
        for (mixer, sources) in self.mixer_sources.items():

            sourcetype = mixer.split(':')[1].split('-')[0]

            for source, source_name in enumerate(sources):

                self.add_parameter(f'{mixer.replace('mixer', 'monitor')}:{index}:{source}', None, types='f', default=-65, osc=True)
                self.add_parameter(f'{mixer.replace('mixer', 'monitor').replace('gain', 'pan')}:{index}:{source}', None, types='f', default=0.5, osc=True)
                self.add_parameter(f'{mixer.replace('mixer', 'monitor').replace('gain', 'mute')}:{index}:{source}', None, types='i', default=0, osc=True)

                self.add_mapping(
                    src = [
                        f'{mixer.replace('mixer', 'monitor')}:{index}:{source}',
                        f'{mixer.replace('mixer', 'monitor').replace('gain', 'pan')}:{index}:{source}',
                        f'{mixer.replace('mixer', 'monitor').replace('gain', 'mute')}:{index}:{source}',
                        f'source-{sourcetype}-hide:{source}',
                    ],
                    dest = f'{mixer}:{index}:{source}',
                    transform = lambda_volume_mono,
                    condition = f'output:mono:{index}'
                )

        if index % 2 == 0:
            for (mixer, sources) in self.mixer_sources.items():

                sourcetype = mixer.split(':')[1].split('-')[0]

                for source, source_name in enumerate(sources):

                    self.add_mapping(
                        src = [
                            f'{mixer.replace('mixer', 'monitor')}:{index}:{source}',
                            f'{mixer.replace('mixer', 'monitor').replace('gain', 'pan')}:{index}:{source}',
                            f'{mixer.replace('mixer', 'monitor').replace('gain', 'mute')}:{index}:{source}',
                            f'source-{sourcetype}-hide:{source}',
                        ],
                        dest = [f'{mixer}:{index}:{source}', f'{mixer}:{index + 1}:{source}'],
                        transform = lambda_volume_stereo,
                        condition = f'output:stereo:{stereo_index}'
                    )

            # link outputs
            for param in ['output:volume-db', 'output:mute', 'output:name', 'output:color']:
                self.add_mapping(
                    src = f'{param}:{index}',
                    dest = f'{param}:{index + 1}',
                    transform = lambda v: v,
                    inverse = lambda v: v,
                    condition = f'output:stereo:{stereo_index}'
                )

            for param in ['output:stereo']:
                self.add_mapping(
                    src = f'{param}:{index}',
                    dest = f'{param}:{index + 1}',
                    transform = lambda v: v,
                    inverse = lambda v: v,
                )


    def volume_pan_to_gains(self, vol, pan, mute, in_range, out_range):

        # apply mute
        if mute:
            if mono:
                return out_range[0]
            return [out_range[0], out_range[0]]

        # normalise input
        g1 = g2 = (max(in_range[0], min(in_range[1], vol)) - in_range[0]) / (in_range[1] - in_range[0])
        
        # apply simple pan: linear attenuation of the weakest side
        pan = max(0, min(1, pan))
        if pan < 0.5:
            g2 *= pan * 2
        elif pan > 0.5:
            g1 *= 2 - 2 * pan

        # map to out range
        g1 = g1 * (out_range[1]-out_range[0]) + out_range[0]
        g2 = g2 * (out_range[1]-out_range[0]) + out_range[0]

        return [g1, g2]

    def volume_pan_to_gains_hack(self, vol, pan, mute, in_range, out_range):

        # apply mute
        if mute:
            return [out_range[0], out_range[0]]

        # normalise input
        g1 = g2 = (max(in_range[0], min(in_range[1], vol)) - in_range[0]) / (in_range[1] - in_range[0])
        
        # apply simple pan: linear attenuation of the weakest side
        pan = max(0, min(1, pan))
        if pan < 0.5:
            g2 *= pan * 2
        elif pan > 0.5:
            g1 *= 2 - 2 * pan

        # dirty hack: split in range before 0 and map it to half of out range
        zerodb = (-in_range[0]) / (in_range[1] - in_range[0])
        half_out = (out_range[1]-out_range[0]) / 2

        if g1 < zerodb:
            g1 = g1 / zerodb
            g1 = pow(g1,4) # very vague way to get a usable scale
            g1 = g1 * (out_range[1]-out_range[0] - half_out)  + out_range[0]
        else:
            g1 = (g1 - zerodb) / (1 - zerodb) 

            g1 = g1 * (out_range[1]-out_range[0] - half_out) + out_range[0] + half_out

        if g2 < zerodb:
            g2 = g2 / zerodb
            g2 = pow(g2,4)
            g2 = g2 * (out_range[1]-out_range[0] - half_out)  + out_range[0]
        else:
            g2 = (g2 - zerodb) / (1 - zerodb) 
            g2 = g2 * (out_range[1]-out_range[0] - half_out) + out_range[0] + half_out

        return [g1, g2]
