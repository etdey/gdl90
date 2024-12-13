# GDL 90 Decoder and Encoder

This package is a set of tools and libraries for decoding and encoding the GDL
90 protocol used for ADS-B in transmissions. The focus of this package is on a
client application within an aircraft that is receiving a data stream from an
ADS-B hardware device. Any _sending_ tools are meant to simulate the hardware
device for a listening client application.

Unless otherwise stated in the included files, the files within this package
are subject to the following copyright and license.

> Copyright (c) 2016-2024 Eric Dey
> 
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
> 
> The above copyright notice and this permission notice shall be included in
> all copies or substantial portions of the Software.
> 
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.


## Package Overview

The package requires a minimum of Python 3.8, has been tested with Python 3.13,
and makes use of the Python Standard Library for all functions except where 
noted. The primary tool components are:

* `gdl90_receiver.py` -- _receives a live or recorded data stream from ADS-B hardware_
* `gld90_recorder.py` -- _records the raw data stream from ADS-B hardware to file_
* `gld90_sender.py` -- _sends a previously recorded data stream to network_

The `gdl90` subdirectory contains the libraries for decoding and encoding the
GDL 90 and UAT messages.


## Automated Tests

The Python `unittest` framework is used for automated tests. All of 
the unit tests can be executed with the `run_tests.sh` shell script 
on Linux or MacOS, or with the `run_tests.ps1` PowerShell script on
Windows.


## Utilities

This is a description of the utilities that accompany and use the GDL 90 library. These utilities make use of external Python packages, so pay attention to the environment setup.


### Python Environment Setup

See the `requirements.txt` file a list of required external packages. The setup step are:

1. (Optional) Python virtual environment setup
    1. Install [venv](https://docs.python.org/3/library/venv.html): `pip3 install venv`
    1. Setup within source tree: `python3 -m venv .venv`
1. (Optional) Activate the venv: `source .venv/bin/activate`
1. Install dependencies: `pip3 install -r requirements.txt`
1. (Optional) Install code coverage package: `pip3 install coverage`

If you install the dependencies within a Python virtual environment, you will need to _activate_ it each time that you will use one of the utilities that depend upon them. Once you are finished with the virtual environment, you can terminiate it with the `deactivate` command.

If you are completely finished with the virtual environment, make sure it is deactivated and then you can simply remove the `.venv` directory tree.


### Receiver

The receiver can be used decode a live data stream or process a recorded GLD 90
file. The output is a line-by-line decoding of the individual message types,
including the optional UAT messages, or a compact text record format that
allows for automated processing.

#### Usage
```
$ ./gdl90_receiver.py --help
Usage: gdl90_receiver.py {requiredOptions} [otherOptions]

GDL-90 Receiver is a data receiver and decoder.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Verbose reporting on STDERR

  Optional:
    -p NUM, --port=NUM  receive port (default=43211)
    -s BYTES, --maxsize=BYTES
                        maximum packet size (default=9000)
    -r PACKETS, --reportcount=PACKETS
                        report after receiving this many packets (default=100)
    -i FILE, --inputfile=FILE
                        read from input file instead of network
    --date=YYYY-MM-DD   UTC starting date for data (default=now)
    --plotflight        output plotflight format
    --uat               output UAT messages
```

Example usage:
```
$ ./gdl90_receiver.py -i skyradar.20121028.001 --plotflight > ../KML/PlotFlight/skyradar.track.20121028.001.txt
```

#### Time Keeping

The decoding library makes use of a non-standard MSG101 from the SkyRadar
hardware for time-of-day (hh:mm) since the MSG00 timestamp is not usable as
defined in the GDL 90 protocol. Since seconds information is not available when
using the SkyRadar hardware, the decoding library self-corrects its internal
estimation of the number of seconds past the minute as messages are received.



### Recorder

The recorder captures the raw data stream from an ADS-B device and saves it to
a file. It is designed to be run within a device like the RaspberryPi attached
to a wifi network within an aircraft. The raw files are later downloaded and
processed by the `gdl90_receiver.py` program.


#### Usage
```
$ ./gdl90_recorder.py --help
Usage: gdl90_recorder.py {requiredOptions} [otherOptions]

GDL-90 Recorder is a data receiver.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Verbose reporting on STDERR
  --slowexit            Delay error exit for 15 seconds

  Optional:
    --interface=name    receive interface name (default=)
    -p NUM, --port=NUM  receive port (default=43211)
    -s BYTES, --maxsize=BYTES
                        maximum packet size (default=1500)
    --dataflush=SECS    seconds between data file flush (default=10)
    --logprefix=PATH    path prefix for log file names
                        (default=/root/skyradar)
    --rebroadcast=name  rebroadcast interface (default=off)
```

#### Automatic Startup

When running the recorder in a head-less device like the RPi, this should be
run as root with the ability to automatically start and restart. 

##### Systemd
This is the most commonly used startup system on Linux distributions since about 2015. For automatic startup at boot, do the following as root:

1. Edit the configuration items in the `gdl90_service_wrapper` file.
1. Copy service unit file: `cp gdl90.service /etc/systemd/system/.`
1. Reload systemd configuration: `systemctl daemon-reload`
1. Start the GDL 90 service: `systemctl start gdl90`
1. Confirm operation: `systemctl status gdl90`

The service wrapper is used by the gdl90.service unit and systemd for start/stop/restart operations. You should edit the following items based on your system's network and install path:
```
NETWORK_DEV=wlan0
LISTEN_PORT=4000
ADSB_DIRECTORY=/root/adsb
```

##### Init
This is less common on newer Linux systems. For automatic startup at boot, you will add an  
`/etc/inittab` entry such as this:

```
#Run GDL90 recorder
fdr1:23:respawn:/usr/bin/python3 /root/gdl90_recorder.py --slowexit
```

The `--slowexit` option should be used when running from inittab in order to
prevent init from disabling respawns at boot time when the wifi network is
still initializing. Until a valid network interface exists, the recorder will
exit and needs to be restarted.


### Sender

The sender is useful for replaying a previously recorded data stream from an
ADS-B hardware device. This can be used for testing an application or the
decoder library.


```
$ ./gdl90_sender.py --help
Usage: gdl90_sender.py {requiredOptions} [otherOptions]

GDL-90 Sender transmits data to the network.

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         Verbose reporting on STDERR
  -f FILE, --file=FILE  input file (default=STDIN)

  Optional:
    -d IP, --dest=IP    destination IP (default=255.255.255.255)
    -p NUM, --port=NUM  destination port (default=43211)
    -s BYTES, --size=BYTES
                        packet size (default=50)
    --delay=MSEC        time between packets (default=10)
```
