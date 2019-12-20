#!/usr/bin/env bash

if which brew &> /dev/null; then
    brew install portaudio ffmpeg libav
elif which apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install \
        portaudio19-dev libportaudio2 \
        ffmpeg \
        libav-tools
else
    echo "Your package manager is not currently supported."
    echo "Currently supported managers are: brew, apt."
    exit 1
fi
