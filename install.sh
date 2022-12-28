#!/usr/bin/env bash

if which brew &> /dev/null; then
    brew install portaudio ffmpeg libav
elif which apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install python3 ffmpeg \
        portaudio19-dev libportaudio2 wxpython-tools
elif which dnf &> /dex/null; then
	sudo dnf up
	sudo dnf in python3-devel ffmpeg-devel \
		portaudio-devel python3-wxpython4
else
    echo "Your package manager is not currently supported."
    echo "Currently supported managers are: brew, apt, dnf."
    exit 1
fi
