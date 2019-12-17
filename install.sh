#!/usr/bin/env bash

if which brew &> /dev/null; then
    brew install portaudio
else
    echo "Homebrew is not on your PATH. Is it installed?"
    echo "Other package managers are not currently supported"
    exit 1
fi
