from setuptools import setup, find_packages
from setuptools.command.install import install

from sys import path

path.insert(0, './')

from fireface_control import __version__

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)

setup(
    name='fireface_control',
    packages=['fireface_control'],
    package_data={'fireface_control': ['ui/**']},
    version=__version__,
    description='Mixer for RME\'s latter firewire interfaces 802 and UCX',
    url='https://github.com/jean-emmanuel/fireface-control',
    author='Jean-Emmanuel Doucet',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    python_requires='>=3',
    install_requires=[],
    cmdclass={
        'install': PostInstallCommand,
    }
)
