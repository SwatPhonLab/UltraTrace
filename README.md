# UltraTrace

This is a tool for [currently] manual annotation of 2D UTI (Ultrasound Tongue Imaging) data.

You can have a look at our [UltraFest IX presentation](https://swatphonlab.github.io/2020-UltraTrace-presentation/presentation.html) for some details on featureset and functionality as of October, 2020.

## Screenshot
![Screenshot](screenshot.png)

## Installation

This tool requires the following system packages to be installed:

* [`ffmpeg`](https://ffmpeg.org/)
* [`portaudio`](http://www.portaudio.com/)
* [`python3`](https://www.python.org/) (3.7 or later)

Additionally, you'll need the following Python components (which are sometimes distributed separately):

* [Python development headers](https://devguide.python.org/getting-started/setup-building/#install-dependencies)
* [`pip`](https://pypi.org/project/pip/)
* [`tkinter`](https://docs.python.org/3/library/tkinter.html)
* [`venv`](https://docs.python.org/3/library/venv.html)

See below for platform-specific installation instructions:
* [Ubuntu](#ubuntu)
* [Fedora](#fedora)
* [macOS](#macos)
* [Windows](#windows)

Once these libraries are installed, you can just `pip install` the package with

```sh
$ python3 -m pip install -r ./requirements.txt
```

NOTE: For hacking on `ultratrace` itself, see [Development](#development) below.

NOTE: You probably want to install into a [virtual environment](https://docs.python.org/3/tutorial/venv.html) to avoid conflicts with system packages.  Alternatively, you can do a [`--user` installation](https://pip.pypa.io/en/latest/user_guide/#user-installs).

### Ubuntu

Supported versions: 18.04, 20.04

```sh
$ apt-get update
$ apt-get install --yes \
    ffmpeg \
    portaudio19-dev \
    python3.8 \
    python3.8-dev \
    python3.8-venv \
    python3-pip \
    python3-tk
```

### Fedora

Supported versions: TODO

```sh
$ dnf upgrade
$ dnf install \
    ffmpeg \
    python3 \
    portaudio
```

### macOS

Supported versions: TODO

These instructions use the [Homebrew](https://brew.sh) package manager.

```sh
$ brew update
$ brew install \
    ffmpeg \
    portaudio
```

### Windows

TODO

## Usage

Once [installed](#installation), you can just run

```sh
$ ultratrace path/to/data
```

### Data format

The minimum data required for UltraTrace to run is at least one ultrasound file and at least one audio file (supported formats listed below).  Annotation files store timing of the ultrasound frames as well as any linguistic information of use (words, segments, etc.).  Corresponding ultrasound, audio, and annotation files should have the same base name (everything except the extension), and may be symlinked or stored in subdirectories.  (The naming convention for AAA-exported data is a little different.)

#### Supported data formats
* ultrasound: DICOM (.dicom, .dcm), AAA-exported scanline data (.ult)
* audio: .wav, .flac
* text alignment: .TextGrid
* traces/splines: native .json, old native .measurement, AAA-exported splines

#### Supported data access methods:
Reading DICOM data is supported in the following ways:
* Reading native pixel data directly
* Converting pixel data to PNG
* Reading from Philips scanline data

Alignment of audio and ultrasound frames supports the following methods:
* From native Philips timing data
* Generated from DICOM frametime (or framerate) specification
* Manual adjustment of alignment
* Stored in TextGrids (actively stores above methods this way; can read alignment previously stored this way)
* Future: auxiliary synchronisation data

### Themes

The theme should just look right on Mac.

#### Setting the theme on linux

We use [`ttkthemes`](https://ttkthemes.readthedocs.io/en/latest/), which can be installed with `pip`, e.g.,
```sh
$ python3 -m pip install --user ttkthemes
```

Add the following line to your `~/.Xresources` file:
```
*TtkTheme: arc
```

You may select something other than clam for your theme.  Currently, the main options are something like this: `arc`, `plastik`, `clearlooks`, `elegance`, `radiance`, `equilux`, `black`, `smog`, `scidblue`, etc.  See the [ttkthemes documentation](https://ttkthemes.readthedocs.io/) for more information.

Otherwise it'll fall back to `*TtkTheme`, and if that's not specified in `~/.Xresources`, it'll fall back to `clam`.

## Development

To hack on `ultratrace`, you should first [install all required system libraries](#installation).  Then, you can set up a development environment by running

```sh
$ source dev/env.sh
```

To lint/test `ultratrace`, use [`nox`](https://nox.thea.codes/en/stable/):
```sh
$ nox --help
```

To exit the development environment, just run
```sh
$ deactivate
```
