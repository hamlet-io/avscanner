#!/usr/bin/env bash

# Always refresh av on startup
freshclam -v -u clamav
clamd
python processor/worker/virus_scanner/__init__.py
