#!/bin/sh

function main() {
  echo "Starting clamd..."
  clamd
  echo "Running $@"
  "$@"
}
# echo "Sleeping to prevent exit..."
# while true; do sleep 10s; done
main "$@"
