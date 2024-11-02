#!/usr/bin/env python3

import sys

z_color_change = "2.15"  # millimeters, as string to prevent float rounding

with open(sys.argv[1], "r") as file:
    gcode = file.readlines()

with open(sys.argv[1], "w") as file:
    for line in gcode:
        file.write(line)
        if f";Z:{z_color_change}" in line:
            file.write("M600 ; filament change\n")
