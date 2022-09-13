#!/usr/bin/env bash

if which brew &> /dev/null; then
    brew install python3 portaudio ffmpeg libav
    python -m ensurepip --upgrade
    pip install -r requirements.txt
    python3 setup.py install
elif which apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install python3 portaudio19-dev libportaudio2 ffmpeg libav-tools build-essential
    python3 -m ensurepip --upgrade
    sudo touch /usr/local/bin/ultratrace
    pip install -r requirements.txt
    sudo python3 setup.py install
elif which dnf &> /dev/null; then
    sudo dnf up
    sudo dnf in python3 portaudio ffmpeg gcc-c++
    sudo dnf group install "Development Tools"
    python3 -m ensurepip --upgrade
    sudo touch /usr/local/bin/ultratrace
    pip install -r requirements.txt
    sudo python3 setup.py install
else
    echo "Your package manager is not currently supported."
    echo "Currently supported managers are: brew, apt, dnf."
    exit 1
fi
