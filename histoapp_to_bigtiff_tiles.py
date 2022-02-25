#!/usr/bin/env python3

# Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.

# Downloads image patches from a webserver and sequentially writes them into a bigtiff file.
# Note that libvips is required and can be installed using "apt install libvips" (Ubuntu) or "brew install vips" (Mac OS)

from curses import meta
from fileinput import filename
import io
import json
from urllib import response

import numpy as np
import pyvips
import requests
import tqdm
from PIL import Image
import math

import shutil
import os



Image.MAX_IMAGE_PIXELS = None

# adapt as needed
baseurl="https://histoapp.mevis.fraunhofer.de"
patch_size = 8000
project="project"
image="image.sqreg"
level=4
z=1
userCredentials=('user','pass')

def setupBigTiff(project, imageName, level):
    metadata = requests.get('{}/api/v1/projects/{}/images/{}'.format(baseurl, project, imageName), auth = userCredentials).json()
    try:
        serverLevel = len(metadata["voxelsizes"])-level-1
    except KeyError:
        if metadata['status'] == "unauthenticated":
            raise Exception("Username or password seems to be wrong.")
    extent = [math.ceil(d/(2**level)) for d in metadata["extent"]]
    voxelsize = [metadata["voxelsizes"][serverLevel]['x'], metadata["voxelsizes"][serverLevel]['y']]
    # imagefile = pyvips.Image.black(extent[0],extent[1],bands=3)
    print("Downloading {} at resolution {}x{}...".format(imageName,extent[0],extent[1]))
    return serverLevel, extent, voxelsize

def getPatch(project, image, level, z, startPx, endPx, patch_number):
    url = '{}/api/v1/projects/{}/images/{}/region/{}/start/{}/{}/{}/size/{}/{}'.format(baseurl, project, image, level, startPx[0], startPx[1], z, endPx[0]-startPx[0], endPx[1]-startPx[1])
    response = requests.get(url, auth = userCredentials)
    filename = os.path.join("tmp","{:04d}.jpg".format(patch_number))
    try:
        os.mkdir("tmp")
    except FileExistsError:
        pass
    except Exception as e:
        raise(e)
    try:
        with open(filename, 'wb') as f:
            # result.raw.decode_content = True
            f.write(response.content)

    except Exception as e:
        print(url)
        print(response)
        print(response.content)
        raise(e)
    return filename

def main():
    serverLevel, extent, voxelsize = setupBigTiff(project, image, level)
    voxelsize = (1.0/(np.array(voxelsize)/1000000)).tolist() # µm/pixel to pixel/mm
    patch_number = 0
    tiles=[]
    rows = math.ceil(extent[0]/ patch_size)
    for y in tqdm.trange(0, extent[1], patch_size, desc="Rows   "):
        for x in tqdm.trange(0, extent[0], patch_size, desc="Columns", leave=False):
            startPx=(x,y)
            endPx=(extent[0] if x+patch_size > extent[0] else x+patch_size, extent[1] if y+patch_size > extent[1] else y+patch_size)
            if endPx[0] > extent[0]: endPx[0]
            tile_filename = getPatch(project, image, level, z, startPx, endPx, patch_number)
            tiles.append(tile_filename)
            patch_number = patch_number + 1

    # save tiles to file
    vips_tiles = [pyvips.Image.new_from_file(f) for f in tiles]
    im = pyvips.Image.arrayjoin(vips_tiles, across=rows)
    im.tiffsave("{}_{}_{}.tif".format(image,level,z), xres=voxelsize[0], yres=voxelsize[1], tile=True, pyramid=True, compression="jpeg", bigtiff=True, rgbjpeg=False)
    # im.write_to_file("{}_{}_{}.jpg".format(image,level,z))

if __name__ == "__main__":
    main()

