#!/usr/bin/env python3

# Downloads image patches from a webserver and sequentially writes them into a bigtiff file.
# Note that libvips is required and can be installed using "apt install libvips" (Ubuntu) or "brew install vips" (Mac OS)

import numpy as np
import requests
from PIL import Image
import io, json, tqdm
import pyvips

# adapt as needed
baseurl="https://histoapp.mevis.fraunhofer.de"
patch_size = 8192
project="project"
image="frontend__29_29-Ki67__3_nonparametric.sqreg"
level=4
z=0
userCredentials=('user','password')

def setupBigTiff(project, imageName, level):
    metadata = requests.get('{}/api/v1//projects/{}/images/{}'.format(baseurl, project, imageName), auth = userCredentials).json()
    serverLevel = len(metadata["voxelsizes"])-level-1
    extent = metadata["ml_extent"][level]
    imagefile = pyvips.Image.black(extent[0],extent[1],bands=3)
    print("Downloading {} at resolution {}x{}...".format(imageName,extent[0],extent[1]))
    return imagefile, serverLevel, extent

def getPatch(project, image, level, z, startPx, endPx, imagefile):
        result = requests.get('{}/api/v1/projects/{}/images/{}/region/{}/{}/start/{}/{}/end/{}/{}'.format(baseurl, project, image, level, z, startPx[0], startPx[1], endPx[0]-1, endPx[1]-1), auth = userCredentials)
        image = Image.open(io.BytesIO(result.content))
        imgNP =  np.array(image)
        image.close()
        w, h, channels = imgNP.shape
        imgNP = imgNP.reshape(w * h * channels)
        vips_patch = pyvips.Image.new_from_memory(imgNP.data, h, w, bands=channels, format="uchar")
        imagefile = imagefile.draw_image(vips_patch, startPx[0], startPx[1])
        return imagefile

def main():
    imagefile, serverLevel, extent = setupBigTiff(project, image, level)

    for y in tqdm.trange(0, extent[1], patch_size, desc="Rows   "):
        for x in tqdm.trange(0, extent[0], patch_size, desc="Columns", leave=False):
            startPx=(x,y)
            endPx=(extent[0] if x+patch_size > extent[0] else x+patch_size, extent[1] if y+patch_size > extent[1] else y+patch_size)
            if endPx[0] > extent[0]: endPx[0]
            imagefile = getPatch(project, image, serverLevel, z, startPx, endPx, imagefile)

    imagefile.tiffsave("{}_{}_{}.tif".format(image,level,z), tile=True, pyramid=True, compression="jpeg", bigtiff=True, rgbjpeg=True)

if __name__ == "__main__":
    main()

