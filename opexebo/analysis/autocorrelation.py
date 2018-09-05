"""
Calculate 2D spatial autocorrelation

Calculates 2D autocorrelation (autocorrelogram) of a firing map.

"""

from opexebo import general
import numpy as np

def autocorrelation(map):
    """Calculate 2D spatial autocorrelation of a firing map.

    Arguments:
    map: NxM matrix, firing map. map is not necessary a numpy array. May
         cnontain NaNs.

    Returns:
    Resulting correlation matrix, which is a 2D numpy array.
    """

    # overlap_amount is a parameter that is intentionally not exposed to
    # the outside world. This is because too many users depend on it and we
    # do not what everyone to use their own overlap value.
    # Should be a value in range [0, 1]
    overlap_amount = 0.8
    slices = []

    if not isinstance(map, np.ndarray):
        map = np.array(map)

    # make sure there are no NaNs in the map
    map = np.nan_to_num(map)

    # get full autocorrelgramn
    aCorr = general.normxcorr2_general(map)

    # we are only interested in a portion of the autocorrelogram. Since the values
    # on edges are too noise (due to the fact that very small amount of elements
    # are correlated).
    for i in range(map.ndim):
        new_size = np.round(map.shape[i] + map.shape[i] * overlap_amount)
        if new_size % 2 == 0:
            new_size = new_size - 1
        offset = aCorr.shape[i] - new_size
        offset = np.round(offset/2 + 1)
        d0 = int(offset-1)
        d1 = int(aCorr.shape[i] - offset + 1)
        slices.append(slice(d0, d1))

    return aCorr[slices]
