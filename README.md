<details>
  <summary>Work in progress</summary>

# Fireface Control

Totalmix replacement on Linux for RME's latter firewire interfaces 802 and UCX.

![](https://private-user-images.githubusercontent.com/5261671/473997461-dc741105-b13a-45c1-ace4-1398f49cfb86.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTQzMDg0NjIsIm5iZiI6MTc1NDMwODE2MiwicGF0aCI6Ii81MjYxNjcxLzQ3Mzk5NzQ2MS1kYzc0MTEwNS1iMTNhLTQ1YzEtYWNlNC0xMzk4ZjQ5Y2ZiODYucG5nP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI1MDgwNCUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTA4MDRUMTE0OTIyWiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MzJjNzM2MWZiOWNiOTFkMWFhOTViNWI0OTBlNTlmY2E5MjA3NmI4MjA4YzIxOTYzOTA5MDVkODdiY2FkNzQ5YyZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.l1nHrRReHy3F_dpYXcp7TbXqqkKTHPwei7L63xajdCc)

**Requirements**

```
python3 python3-pystray python3-liblo python3-pyalsa python3-pyinotify nodejs
```

- Fireface 802 / UCX (firewire only, usb not supported)
- https://github.com/alsa-project/snd-firewire-ctl-services/

**Usage**

```
git clone https://github.com/jean-emmanuel/FirefaceControl
python FirefaceControl
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

</details>
