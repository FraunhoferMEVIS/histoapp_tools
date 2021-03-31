#!/usr/bin/env python3

# Copyright (c) Fraunhofer MEVIS 2011, Germany. All rights reserved.

# Transforms points based on the transformation in a sqreg file.

import os
import sqlite3

import numpy as np
import scipy.interpolate


def deformation_from_file_no_interp(filepath: str):
    if not os.path.isfile(filepath):
        raise FileNotFoundError("Deformation file does not exist: {}".format(filepath))
    conn = sqlite3.connect(filepath)
    c = conn.cursor()
    c.execute("SELECT * FROM sqreg")
    r = c.fetchone()  # TODO: this only works for z=0 as reference slide
    r = c.fetchone()
    dimsX = r[4]
    dimsY = r[5]
    defX = np.reshape(np.frombuffer(r[2]), (dimsX, dimsY)).T
    defY = np.reshape(np.frombuffer(r[3]), (dimsX, dimsY)).T
    Wdef = np.frombuffer(r[6])
    Wdef = np.reshape(Wdef, (4, 4))
    conn.close()
    return (np.array(defX), np.array(defY), np.array(Wdef), dimsX, dimsY)


def deformation_from_file(filepath: str):
    defX, defY, Wdef, dimsX, dimsY = deformation_from_file_no_interp(filepath)
    gridX = np.arange(0, Wdef[0, 0] * dimsX, Wdef[0, 0])
    gridY = np.arange(0, Wdef[1, 1] * dimsY, Wdef[1, 1])
    defXInterp = scipy.interpolate.RectBivariateSpline(gridX, gridY, defX)
    defYInterp = scipy.interpolate.RectBivariateSpline(gridX, gridY, defY)
    return (defXInterp, defYInterp)


def transform_point(defInterp: tuple, WT: np.array, pts: list[list[int]]):
    tpts = np.zeros((len(pts), 2))
    tptsW = np.zeros((len(pts), 4))

    for i, point in enumerate(pts):
        u = np.zeros(2)
        pW = np.dot(WT, [point[0], point[1], 0, 1])
        u[0] = defInterp[0](pW[0], pW[1])
        u[1] = defInterp[1](pW[0], pW[1])
        pW_t = np.array([0, 0, 0, 1.0])
        pW_t[0] = pW[0] + u[0]
        pW_t[1] = pW[1] + u[1]
        tp = np.linalg.solve(WT, pW_t)
        tptsW[i, :] = pW_t
        tpts[i, :] = tp[0:2]
    return tpts, tptsW


def main():
    """
    Transfor a list of points [x,y] from the reference to the template image.

    points: The input points [[x1, y1], [x2, y2], ...] have to be defined as pixel coordinates on the finest level of the WSI.
    filepath: The deformation ist stored in an sqlite database containing the nonlinear deformation in the .sqreg format.
    pixelsize_mm: The pixelsize is the size of one pixel in mm given at the finest level of the WSI.
    """

    pixelsize_mm = 0.000275  # ADAPT FROM WSI
    points = [[0, 0], [100, 100], [10000, 10000]]  # ADAPT, points at finest WSI-level
    filepath = "/Users/jo/Downloads/3_nonparametric.sqreg"
    interpolated_deformation = deformation_from_file(filepath)

    # worldmatrix of template and reference image (we assume that both are equal, WT=WR)
    WT = np.eye(4)
    WT[0, 0] = pixelsize_mm
    WT[1, 1] = pixelsize_mm
    transformed_points, _transformed_points_world = transform_point(
        interpolated_deformation, WT, points
    )

    print(transformed_points)


if __name__ == "__main__":
    main()
