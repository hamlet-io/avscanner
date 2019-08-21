#!/usr/bin/env bash

clamd
python processor/worker/virus_scanner/__init__.py
