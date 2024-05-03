#!/bin/sh

cd /
cd home/pi/project
sudo python3 main_headless.py &
sudo python3 safe_shutdown.py &
cd /