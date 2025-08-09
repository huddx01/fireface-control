"""
CLI arguments parsing
"""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from sys import argv
from . import __version__

parser = ArgumentParser(prog='python -m fireface_control', formatter_class=ArgumentDefaultsHelpFormatter)

parser.add_argument('--port', help='http port for the web application', default=8080)
parser.add_argument('--engine-port', help='osc port for the engine (random by default)', default=0)
parser.add_argument('--dev', help='enable gui editor and launch gui client at startup (requires open-stage-control)', default=False, action='store_true')
parser.add_argument('--version', action='version', version=__version__)

config = parser.parse_args()
