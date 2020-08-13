#!/usr/bin/env python3

# Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.

# Converts arbitrary images to Histokat-readable bigtiff-files using vips. Use conda "conda env update -f environment.yml" to setup an environment with the correct versions

import pyvips
import sys

def main():
    if len(sys.argv) != 3:
        print("Usage: convert_to_bigtiff.py [input file] [output file]")
    else:
        image = pyvips.Image.new_from_file(sys.argv[1], access='random')
        xres = image.xres
        yres = image.yres
        print("Converting {} with pixel size {}x{}.".format(sys.argv[1],xres,yres))
        if xres == 0 or yres == 0:
            xres=4000
            yres=4000
            print("... setting pixel size to {}x{}.".format(xres,yres))
        image.tiffsave(sys.argv[2], xres=xres, yres=yres, bigtiff=True,pyramid=True,tile=True,compression="jpeg",rgbjpeg=True)

if __name__ == "__main__":
    main()

