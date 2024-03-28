# record player icecast
Using raspberry pi zero 2 W with 128GB SD to host icecast2 "radio" which playbacks the record player.
The record player is an old Dual DT 210 USB, which is connected via USB-B to USB-A cable and USB-A to microUSB OTG cable to the Pi.

## Initial test setup
looking for usb devices:
```bash
albrechs@plattenspieler:~ $ lsusb
Bus 001 Device 002: ID 08bb:2900 Texas Instruments PCM2900 Audio Codec
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

So it was connected and recognized - good.
Next find out which alsa card it is mapped to:
```bash
albrechs@plattenspieler:~ $ cat /proc/asound/cards
 0 [vc4hdmi        ]: vc4-hdmi - vc4-hdmi
                      vc4-hdmi
 1 [CODEC          ]: USB-Audio - USB Audio CODEC
                      Burr-Brown from TI USB Audio CODEC at usb-3f980000.usb-1, full speed
```
The first one is the HDMI port of the Pi, so the second one should be the record player. So we will be using `hw:1`.
(also checked for subcards using `arecord -l`)

Simple test recording for 10 seconds using `ffmpeg`:

```bash
ffmpeg -f alsa -i hw:1 -t 10 out.mp3
```

Sounded well enough, so we proceed with setting up darkice+icecast2 server:
```bash
sudo apt update && sudo apt install darkice icecast2
```
During installation of icecast2, the initial configuration has to be performed.

> :warning: You'll set the admin password, that will be used by darkice to connect to the icecast2 server!

Now we just need to write the darkice config in ´/etc/darkice.cfg´:

```ini
[general]
duration      =  0
bufferSecs    =  1
reconnect     =  yes
[input]
device        =  plughw:1
sampleRate    =  44100
bitsPerSample =  16
channel       =  2
[icecast2-0]
bitrateMode   =  abr
format        =  mp3
bitrate       =  320
server        =  localhost
port          =  8000
password      =  hackme
mountPoint    =  stream
name          =  Plattenspieler
description   =  Broadcast from my analog vinyl player
```

start manually with `darkice`.

Now the streaming server should be available at `<ip/hostname of rpi>:8000/` and the `m3u` stream can be accessed at `<ip/hostname of rpi>:8000/stream` 
## material
- [Tutorial for icecast2](https://circuitdigest.com/microcontroller-projects/raspberry-pi-internet-radio-and-streaming-station) ([mirror](https://web.archive.org/web/20230314172445/https://circuitdigest.com/microcontroller-projects/raspberry-pi-internet-radio-and-streaming-station))
