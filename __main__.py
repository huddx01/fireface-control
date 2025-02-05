from sys import path
from os.path import dirname
path.insert(0, dirname(__file__) + '/../')

from mentat import Engine

from fireface802 import FireFace802
from osc import OSC

engine = Engine('AlsaMixer', port=5555, folder=dirname(__file__))

ff802 = FireFace802()
osc = OSC(protocol='osc', ff802=ff802, port=8080)

engine.add_module(ff802)
engine.add_module(osc)

# RME phones 1 & 2
ff802.create_monitor(0, [8,9], 'RME Phones 1')
ff802.create_monitor(1, [10,11], 'RME Phones 2')

# # HP4 phones 1 - 4
ff802.create_monitor(2, [14,15], 'HP4 Phones 1')
ff802.create_monitor(3, [16,17], 'HP4 Phones 2')
ff802.create_monitor(4, [18,19], 'HP4 Phones 3')
ff802.create_monitor(5, [20,21], 'HP4 Phones 4')




engine.autorestart()
engine.start()