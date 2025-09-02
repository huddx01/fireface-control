# Fireface Control

Totalmix replacement on Linux for RME's latter firewire interfaces 802 and UCX.

**Requirements** *(as Debian packages)*

```
python3 python3-pystray python3-liblo python3-pyalsa python3-pyinotify nodejs alsa-utils
```

Additionaly `snd-fireface-ctl-service` must be built and installed manually from https://github.com/alsa-project/snd-firewire-ctl-services/ and the python package `mentat` (https://jean-emmanuel.github.io/mentat/) must be installed as well.

The web application requires firefox or chromium to work, it's designed for desktop use (high-res tablets may work).


**Usage**

```
git clone https://github.com/jean-emmanuel/fireface-control
cd fireface-control
git submodule update --init
python -m fireface_control -h
```

**Features**

- web based interface accessible over the network
- customizable channel visibility, color and name
- eq and dynamics controls for selected channel
- fx (echo and reverb)

*Key differences with Totalmix*

- software output mixer is replaced with a straight routing and "pc return" controls for hardware outputs
- inputs are mono only
- echo fx are mono except pong echo


**Notes**

Some settings made in Totalmix may conflict.

UCX has not been tested yet.

The first UFX model (firewire) might work as well and be seen as a 802 (untested).
