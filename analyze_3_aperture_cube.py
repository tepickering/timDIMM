#!/usr/bin/env python

import sys
import scipy.ndimage as nd
import numpy as np
import pyfits
from matplotlib.pyplot import acorr as acorr
from matplotlib.mlab import detrend_linear as detrend_linear

"""
Define a function to read a FITS image and return the data it contains. The
use of the `memmap=True` argument here is important because the data cubes
generated by the seeing camera are >700 MB in size and can be even larger. It
would be inefficient to load the entire dataset into memory if we're not going
to use it all.
"""

def rfits(file):
    f = pyfits.open(file, memmap=True)
    return f[0].data

"""
Define a function to find spots within an image. This method smooths the image
with a gaussian of width `sigma` and then clips the image by `clip_level` above
the mean. The clipped image is passed to `scipy.ndimage.label` to find regions
of associated flux, i.e. the spots we're looking for. These labels are used in
`scipy.ndimage.center_of_mass` to calculate centroids of the flux within
labeled regions.
"""

def spotfind(im, sigma=1.1, clip_level=6.0):
    mean = np.mean(im)
    sig = np.std(im)
    smooth = nd.gaussian_filter(im, sigma)
    clip = smooth >= (mean + clip_level)
    labels, num = nd.label(clip)
    pos = nd.center_of_mass(im, labels, range(num + 1))
    return num, pos[1:]

"""
Load in an image cube and display the first image. Python uses row-first
indexing so the cube indexing goes as `cube[z, y, x]`.
"""

filename = sys.argv[1]
cube = rfits(filename)

"""
Take an image from the middle of the cube, find the spots in it, and use the
positions to set up the region of interest to analyze for the rest of the cube.
"""

slice = 5000
num, spots = spotfind(cube[slice, :, :], sigma=1.0, clip_level=5.0)
print "Found %d spots." % num
spots = np.array(spots, dtype=[('y', float), ('x', float)])
xcen = spots['x'].mean()
ycen = spots['y'].mean()
xmin = int(xcen - 40)
xmax = int(xcen + 40)
ymin = int(ycen - 40)
ymax = int(ycen + 40)

"""
Now loop through the whole cube and run `spotfind()` on each image. Check to
make sure there are 2 valid spots, sort the resulting spot positions in order
of their X position, and appends the results to an array called `spots`. Notice
the use of `x` and `y` labels when defining the `numpy.array` that contains the
spots for an image. This labeling simplifies how we refer to the data later on.
At the end, convert `spots` to a `numpy.array` for further analysis.
"""

spots = []
nfailed = 0
for im in cube[:, ymin:ymax, xmin:xmax]:
    n, s = spotfind(im, sigma=1.1, clip_level=6.0)
    if n == 3:
        ss = np.array(s, dtype=[('y', float), ('x', float)])
        ss.sort(order='x')
        spots.append(ss)
    else:
        nfailed += 1
print "Failed to find right spots in %d images." % nfailed
SS = np.array(spots)

"""
Define a function to measure the distance between two spots for all
measurements of those spots. It takes as arguments the array containing the
spot centroids and the desired spot indicies.
"""

def spotdist(spots, spot1, spot2):
    return np.hypot(spots['x'][:, spot1] - spots['x'][:, spot2],
                    spots['y'][:, spot1] - spots['y'][:, spot2])


# Measure the distances between the left-most (0), middle (1), and right-most
# (2) spots.

baseline01 = spotdist(SS, 0, 1)
baseline02 = spotdist(SS, 0, 2)
baseline12 = spotdist(SS, 1, 2)

"""
Notice how this plot is much flatter than the plots of the spot coordinates.
The spot distance is a *differential* measure that removes all of the common
motion due to guiding, vibration, etc. If there was no atmosphere, these lines
would be completely flat. However, atmospheric turbulence causes the light from
the star to bend slightly and thus move around as turbulence moves in front of
it. The three different apertures are looking at the same star through slightly
different paths through the atmosphere. The differential motion between these
paths is what we use to characterize the turbulence. Here, the differential
motion is given by the standard deviation of the spot distances.
"""

rms01 = baseline01.std()
rms02 = baseline02.std()
rms12 = baseline12.std()

"""
To convert these variances in the spot distances to a measure of the
turbulence, we need to know some properties of the DIMM system and use a model
for the turbulence.
"""

# this is the pixel scale of the DIMM detector in "/pixel as measured
# using known double stars
pixel_scale = 1.046

# this is the diameter of an aperture in meters
d = 0.05

# these are the distances between the apertures. the long one, r02, was
# measured accurately. the other two weren't, but can bootstrap them from
# the data.
r02 = 0.2
r12 = 0.2 * baseline12.mean()/baseline02.mean()
r01 = 0.2 * baseline01.mean()/baseline02.mean()

# this routine uses tokovinin's modified equation given in 2002, PASP, 114, 1156
def seeing(rms, r, d, scale):
    b = r/d
    l = 0.6e-6
    var = (rms * scale / 206265.0)**2
    K = 0.364 * (1.0 - 0.532 * b**(-1.0/3.0) - 0.024 * b**(-7.0/3.0))
    fwhm = 206265.0 * 0.98 * (d/l)**0.2 * (var/K)**0.6
    return fwhm

seeing01 = seeing(rms01, r01, d, pixel_scale)
seeing02 = seeing(rms02, r02, d, pixel_scale)
seeing12 = seeing(rms12, r12, d, pixel_scale)

print "Seeing value for the first and second spots: %.3f\"" % seeing01
print "Seeing value for the first and third spots: %.3f\"" % seeing02
print "Seeing value for the second and third spots: %.3f\"" % seeing12

"""
The middle value for the first and third spots is the value we'd normally
measure with this mask. Notice, however, that the seeing values that
incorporate the middle aperture, spot 1, are much higher. The aperture
separations involving the middle aperture are half that of the normal pair of
apertures. This could result in both apertures being affected by the same wave
of turbulence at the same time. We can test for this by measuring the
autocorrelation of the spot distance.
"""

# measure the autocorrelation for spots 0 and 1
a01 = acorr(baseline01, normed=True, detrend=detrend_linear, maxlags=100)
ac = a01[1]
ctime = 3.0 * len(ac[ac > 0.5])/2.0
print "Correlation time for baseline 0-1: %.3f ms" % ctime

# measure the autocorrelation for spots 0 and 2
a02 = acorr(baseline02, normed=True, detrend=detrend_linear, maxlags=100)
ac = a02[1]
ctime = 3.0 * len(ac[ac > 0.5])/2.0
print "Correlation time for baseline 0-2: %.3f ms" % ctime

# measure the autocorrelation for spots 1 and 2
a12 = acorr(baseline12, normed=True, detrend=detrend_linear, maxlags=100)
ac = a12[1]
ctime = 3.0 * len(ac[ac > 0.5])/2.0
print "Correlation time for baseline 1-2: %.3f ms" % ctime
