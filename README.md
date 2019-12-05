# UltraTrace
This is a tool for [currently] manual annotation of UTI (Ultrasound Tongue Imaging) data.

## Screenshot
![Screenshot](screenshot.png)

## Installation

## Use

```bash
$ python3 -m ultratrace /path/to/data
```

### Data format

The minimum data required for UltraTrace to run is at least one ultrasound file and at least one audio file (supported formats listed below).  Annotation files store timing of the ultrasound frames as well as any linguistic information of use (words, segments, etc.).  Corresponding ultrasound, audio, and annotation files should have the same base name (everything except the extension), and may be symlinked or stored in subdirectories.  (The naming convention for AAA-exported data is a little different.)

#### Supported formats
* ultrasound: DICOM (.dicom, .dcm), AAA-exported scanline data (.ult)
* audio: .wav, .flac
* annotation: .TextGrid

### Themes

The theme should just look right on Mac.

#### Setting the theme on linux

Use pip3 to install ttkthemes.

Add the following line to your `~/.Xresources` file:

```
*TtkTheme: arc
```

You may select something other than clam for your theme.  Currently, the main options are something like this: `arc`, `plastik`, `clearlooks`, `elegance`, `radiance`, `equilux`, `black`, `smog`, `scidblue`, etc.  See the [ttkthemes documentation](https://ttkthemes.readthedocs.io/) for more information.

Otherwise it'll fall back to `*TtkTheme`, and if that's not specified in `~/.Xresources`, it'll fall back to `clam`.
