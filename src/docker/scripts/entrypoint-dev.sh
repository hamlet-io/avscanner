#!/usr/bin/env bash

#running clamAV process in a background
echo "Starting clamd..."
clamd
echo "Clamd started"
tail -f /dev/null
