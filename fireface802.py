from time import sleep
from math import log10
import json
import logging
from alsamixer import AlsaMixer

class FireFace802(AlsaMixer):

    mixer_sources = {
        'mixer:line-source-gain':  [f'Line {x + 1}' for x in range(8)],
        'mixer:mic-source-gain': [f'MIC {x + 1}' for x in range(4)],
        # 'mixer:spdif-source-gain': [f'SPDIF in {x + 1}' for x in range(2)],
        'mixer:adat-source-gain': [f'ADAT {x + 1}' for x in range(16)]
    }

    mixer_outputs = range(30)


    mixer_outputs_default_names = [f'Line {x + 1}' for x in range(8)] + \
                                       ['Phones 9', 'Phones 10'] + \
                                       ['Phones 11', 'Phones 12'] + \
                                       [f'SPDIF {x + 1}' for x in range(2)] + \
                                       [f'ADAT {x + 1}' for x in range(16)]


    output_meters = {
        'meter:line-output':  range(8),
        'meter:hp-output': range(4),
        # 'meter:spdif-output': range(2),
        'meter:adat-output': range(16)
    }
    meter_noisefloor = -85

    stereo_mixers = {
        8: 'RME 1',
        10: 'RME 2',
    }



    def __init__(self, *args, **kwargs):

        super().__init__(name='Fireface802', *args, **kwargs)

        """
        Create mixers gain parameters
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
        Output
        """
        for dest in self.mixer_outputs:
            self.add_parameter(f'output:volume:{dest}', None, types='i', default=0)
            self.add_parameter(f'output:volume-db:{dest}', None, types='f', default=0, osc=True)
            self.add_parameter(f'output:mute:{dest}', None, types='i', default=0, osc=True)
            self.add_parameter(f'output:default-name:{dest}', None, types='s', default=self.mixer_outputs_default_names[dest], osc=True)
            self.add_parameter(f'output:name:{dest}', None, types='s', default='', osc=True)
            self.add_parameter(f'output:color:{dest}', None, types='s', default='', osc=True)

            self.add_mapping(
                src=[f'output:volume-db:{dest}', f'output:mute:{dest}'],
                dest=f'output:volume:{dest}',
                transform=lambda v, m: v*10 - m * 900,
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

                self.add_parameter(f'source-{sourcetype}-default-name:{source}', None, types='s', default=source_name, osc=True)
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


        out_index = -1
        for (output_meter, outputs) in self.output_meters.items():
            for output in outputs:
                out_index += 1
                self.add_parameter(f'output-meter:{out_index}', None, types='f', default=-90, osc=True)



        self.add_parameter('metering', None, types='s', default='on', alsa='', osc=True)

        """
        Mixers
        """
        mixers = []
        index = 0
        while index < len(self.mixer_outputs):
            mixers.append(index)
            if index in self.stereo_mixers:
                self.create_mixer(index, True, self.stereo_mixers[index])
                index +=2
            else:
                self.create_mixer(index, False)
                index +=1

        self.add_parameter('mixers:choices', None, types='s', default=json.dumps(mixers), osc=True, osc_order=-1)
        self.add_parameter('mixers:select', None, types='i', default=0, osc=True)
        self.add_mapping(
            src=[f'monitor-name:{i}' for i in mixers],
            dest='mixers:choices',
            transform= lambda *names: json.dumps({"labels":names, "values": mixers})
        )

    def update_meters(self):
        """
        Fetch meter values periodically
        """
        while True:
            sleep(1/20)

            for (mixer, sources) in self.mixer_sources.items():

                sourcetype = mixer.split(':')[1].split('-')[0]

                meters = self.alsa_get(f'meter:{sourcetype}-input', f'name="meter:{sourcetype}-input",iface=CARD')
                if meters:
                    for i, v in enumerate(meters):
                        self.set(f'source-{sourcetype}-meter:{i}', self.meter_abs_to_db(v))


            out_index = -1
            for (output_meter, outputs) in self.output_meters.items():

                    meters = self.alsa_get(output_meter, f'name="{output_meter}",iface=CARD')
                    if meters:
                        for i, v in enumerate(meters):
                            out_index += 1

                            self.set(f'output-meter:{out_index}', self.meter_abs_to_db(v))


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


    def create_mixer(self, index, stereo=False, name=None):
        """
        Create mixers
        """

        # create gain, mute and pan controls for every input
        # and map them to the appropriate mixer source gains
        for (mixer, sources) in self.mixer_sources.items():

            sourcetype = mixer.split(':')[1].split('-')[0]

            for source, source_name in enumerate(sources):

                self.add_parameter(f'{mixer.replace('mixer', 'monitor')}:{index}:{source}', None, types='f', default=-65, osc=True)
                self.add_parameter(f'{mixer.replace('mixer', 'monitor').replace('gain', 'pan')}:{index}:{source}', None, types='f', default=0.5, osc=True)
                self.add_parameter(f'{mixer.replace('mixer', 'monitor').replace('gain', 'mute')}:{index}:{source}', None, types='i', default=0, osc=True)

                if stereo:
                    transform = lambda volume, pan, mute, hide: self.volume_pan_to_gains(volume, pan, mute or hide, in_range=[-65,6], out_range=[0, 40960])
                    dest = [f'{mixer}:{index}:{source}', f'{mixer}:{index + 1}:{source}']
                else:
                    transform = lambda volume, pan, mute, hide: self.volume_pan_to_gains(volume, pan, mute or hide, in_range=[-65,6], out_range=[0, 40960], mono=True)
                    dest = f'{mixer}:{index}:{source}'

                self.add_mapping(
                    src = [
                        f'{mixer.replace('mixer', 'monitor')}:{index}:{source}',
                        f'{mixer.replace('mixer', 'monitor').replace('gain', 'pan')}:{index}:{source}',
                        f'{mixer.replace('mixer', 'monitor').replace('gain', 'mute')}:{index}:{source}',
                        f'source-{sourcetype}-hide:{source}',
                    ],
                    dest = dest,
                    transform = transform
                )

        # monitor master controls
        if stereo:
            default_name = name if name is not None else f'{self.mixer_outputs_default_names[index]} + {self.mixer_outputs_default_names[index + 1]}'
        else:
            default_name = name if name is not None else self.mixer_outputs_default_names[index]

        self.add_parameter(f'monitor-name:{index}', None, types='s', default=default_name, osc=True, osc_order=2)
        self.add_parameter(f'monitor-master-gain:{index}', None, types='f', default=0, osc=True)
        self.add_parameter(f'monitor-master-mute:{index}', None, types='i', default=0, osc=True)
        self.add_parameter(f'monitor-stereo:{index}', None, types='i', default=int(stereo), osc=True)

        # map monitor master to output
        self.add_mapping(
            src = f'monitor-master-gain:{index}',
            dest = f'output:volume-db:{index}',
            transform = lambda v: v,
            inverse = lambda v: v,
        )
        self.add_mapping(
            src = f'monitor-master-mute:{index}',
            dest = f'output:mute:{index}',
            transform = lambda v: v,
            inverse = lambda v: v,
        )

        # stereo link outputs
        if stereo:
            for param in ['output:volume-db', 'output:mute', 'output:name', 'output:color']:
                self.add_mapping(
                    src = f'{param}:{index}',
                    dest = f'{param}:{index + 1}',
                    transform = lambda v: v,
                    inverse = lambda v: v,
                )

    def volume_pan_to_gains(self, vol, pan, mute, in_range, out_range, mono=False):

        # apply mute
        if mute:
            if mono:
                return out_range[0]
            return [out_range[0], out_range[0]]

        # map volume to raw gain -65dB,6dB to 0,40960
        g1 = g2 = (max(in_range[0], min(in_range[1], vol)) - in_range[0]) / (in_range[1] - in_range[0]) * (out_range[1]-out_range[0]) + out_range[0]

        if mono:
            return g1

        # apply simple pan: linear attenuation of the weakest side
        pan = max(0, min(1, pan))
        if pan < 0.5:
            g2 *= pan * 2
        elif pan > 0.5:
            g1 *= 2 - 2 * pan

        return [g1, g2]
