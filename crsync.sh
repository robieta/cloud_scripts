#!/bin/bash
cd "$(dirname "$0")"

# Convenience script for rsyncing files to cloud instances
py_output=`python3 _cssh.py rsync "$@"`
exit_code=$?

if [ $exit_code -eq 255 ]; then
  printf %b "$py_output\n"
  exit 255
fi

if [ $exit_code -eq 1 ]; then
  printf %b "$py_output\n"
  exit 0
fi

printf %b "cmd: $py_output\n"
eval $py_output
