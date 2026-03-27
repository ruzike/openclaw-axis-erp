#!/bin/bash
# Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
sleep 2
# Fluxbox
DISPLAY=:99 fluxbox &
sleep 2
# x11vnc (localhost only)
x11vnc -display :99 -nopw -listen localhost -localhost -xkb -forever > /var/log/x11vnc.log 2>&1 &
