#!/usr/bin/env python3

# Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.

# Downloads image patches from a webserver and sequentially writes them into a bigtiff file.
# Note that libvips is required and can be installed using "apt install libvips" (Ubuntu) or "brew install vips" (Mac OS)

from curses import meta
import io
import json

import numpy as np
import pyvips
import requests
import tqdm
from PIL import Image
import math
Image.MAX_IMAGE_PIXELS = None

# adapt as needed
baseurl="https://histoapp.mevis.fraunhofer.de"
patch_size = 16000
project="project"
image="frontend__29_29-Ki67__3_nonparametric.sqreg"
level=4
z=0
userCredentials=('user','password')

def setupBigTiff(project, imageName, level):
    metadata = requests.get('{}/api/v1/projects/{}/images/{}'.format(baseurl, project, imageName), auth = userCredentials).json()
    try:
        serverLevel = len(metadata["voxelsizes"])-level-1
    except KeyError:
        if metadata['status'] == "unauthenticated":
            raise Exception("Username or password seems to be wrong.")
    extent = [math.ceil(d/(2**level)) for d in metadata["extent"]]
    voxelsize = [metadata["voxelsizes"][serverLevel]['x'], metadata["voxelsizes"][serverLevel]['y']]
    imagefile = pyvips.Image.black(extent[0],extent[1],bands=3)
    print("Downloading {} at resolution {}x{}...".format(imageName,extent[0],extent[1]))
    return imagefile, serverLevel, extent, voxelsize

def getPatch(project, image, level, z, startPx, endPx, imagefile):
    url = '{}/api/v1/projects/{}/images/{}/region/{}/start/{}/{}/{}/size/{}/{}'.format(baseurl, project, image, level, startPx[0], startPx[1], z, endPx[0]-startPx[0], endPx[1]-startPx[1])
    result = requests.get(url, auth = userCredentials)
    try:
        image = Image.open(io.BytesIO(result.content))
    except Exception as e:
        print(url)
        print(result)
        print(result.content)
        raise(e)
    imgNP =  np.array(image)
    image.close()
    w, h, channels = imgNP.shape
    imgNP = imgNP.reshape(w * h * channels)
    vips_patch = pyvips.Image.new_from_memory(imgNP.data, h, w, bands=channels, format="uchar")
    imagefile = imagefile.insert(vips_patch, startPx[0], startPx[1])
    return imagefile

def main():
    imagefile, serverLevel, extent, voxelsize = setupBigTiff(project, image, level)
    voxelsize = (1.0/(np.array(voxelsize)/1000000)).tolist() # µm/pixel to pixel/mm
    for y in tqdm.trange(0, extent[1], patch_size, desc="Rows   "):
        for x in tqdm.trange(0, extent[0], patch_size, desc="Columns", leave=False):
            startPx=(x,y)
            endPx=(extent[0] if x+patch_size > extent[0] else x+patch_size, extent[1] if y+patch_size > extent[1] else y+patch_size)
            if endPx[0] > extent[0]: endPx[0]
            imagefile = getPatch(project, image, level, z, startPx, endPx, imagefile)

    imagefile.tiffsave("{}_{}_{}.tif".format(image,level,z), xres=voxelsize[0], yres=voxelsize[1], tile=True, pyramid=True, compression="jpeg", bigtiff=True, rgbjpeg=False)

if __name__ == "__main__":
    main()

