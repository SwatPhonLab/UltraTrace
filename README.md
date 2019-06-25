# UltraTrace
This is a tool for [currently] manual annotation of UTI (Ultrasound Tongue Imaging) data.

## Screenshot
![Screenshot](screenshot.png)

## Installation

## Use

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
