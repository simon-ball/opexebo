"""Provide function for calculating a Border Score"""

import numpy as np
from scipy.ndimage import distance_transform_edt
import opexebo.defaults as default


def border_coverage(fields, **kwargs):
    '''
    Calculate border coverage for detected fields.
    
    STATUS : EXPERIMENTAL
    
    This function calculates firing map border coverage that is further
    used in calculation of a border score.

    TODO
    I havefollowed the approach used in BNT, but I want to double check whether there 
    is a better way to do this - it only tells you that *a* field (it doesn't tell 
    you which one) has coverage of *a* border (it doesn't tell you which one)).


    It seems like there should be a better way of doing this
    (e.g. return a vector of coverage, i.e. a value for each border checked, and 
    return an index of the best field for each border, or something similar)

    Parameters
    ----------
    fields : dict or list of dicts
        One dictionary per field. Each dictionary must contain the keyword "field_map"
    **kwargs
        arena_shape : str
            accepts: ("square", "rectangle", "rectangular", "rect", "s", "r")
                    ("circ", "circular", "circle", "c")
                    ("linear", "line", "l")
            Rectangular and square are equivalent. Elliptical or n!=4 polygons
            not currently supported. Defaults to Rectangular
        search_width : int
            rate_map and fields_map have masked values, which may occur within the region of border 
            pixels. To mitigate this, we check rows/columns within search_width pixels of the border
            If no value is supplied, default 8
        walls : str
            Definition of walls along which the border score is calculated. Provided by
            a string which contains characters that stand for walls:
                      T - top wall (we assume the bird-eye view on the arena)
                      R - right wall
                      B - bottom wall
                      L - left wall
            Characters are case insensitive. Default value is 'TRBL' meaning that border
            score is calculated along all walls. Any combination is possible, e.g.
            'R' to calculate along right wall, 'BL' to calculate along two walls, e.t.c.

    Returns
    -------
    coverage    : float
        Border coverage, ranges from 0 to 1.

    See also
    --------
    BNT.+analyses.placefield
    BNT.+analyses.borderScore
    BNT.+analyses.borderCoverage
    opexebo.analysis.placefield
    opexebo.analysis.borderscore
        
    Copyright (C) 2019 by Simon Ball

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.
    '''

    # Extract keyword arguments or set defaults
    sw = kwargs.get('search_width', default.search_width)
    walls = kwargs.get('walls', default.walls)
    shape = kwargs.get("arena_shape", default.shape)
    if shape.lower() in default.shapes_square:
        DO_A_THING()
    elif shape.lower() in default.shapes_circle:
        DO_A_THING()
    elif shape.lower() in default.shapes_linear:
        DO_A_THING()
    else:
        raise NotImplementedError(f"Arena shape '{shape}' not implemented")

    # Check that the wall definition is valid
    _validate_wall_definition(walls)
    walls = walls.lower()
    
    if isinstance(fields, dict):
        # Deal with the case of being passed a single field, instead of a list of fields
        fields = [fields]
    elif type(fields) not in (list, tuple, np.ndarray):
        raise ValueError(f"You must supply either a dictionary, or list of dictionaries, of fields. You provided type '{type(fields)}'")

    # Check coverage of each field in turn
    coverage = 0
    for field in fields:
        fmap = field['field_map'] # binary image of field: values are 1 inside field, 0 outside
        if "l" in walls:
            aux_map = fmap[:,:sw].copy()
            c = _wall_field_rect(aux_map)
            if c > coverage:
                coverage = c

        if "r" in walls:
            aux_map = fmap[:, -sw:].copy()
            aux_map = np.fliplr(aux_map) # Mirror image to match the expectations in _wall_field, i.e. border adjacent to left-most column
            c = _wall_field_rect(aux_map)
            if c > coverage:
                coverage = c

        # since we are dealing with data that came from a camera
        #'bottom' is actually at the top of the matrix fmap
        # i.e. in a printed array (think Excel spreadheet), [0,0] is at top-left.
        # in a figure (think graph) (0,0) is at bottom-left

        # Note: because I use rotations instead of transposition, this yields 
        # arrays that are upside-down compared to Vadim's version, 
        # BUT the left/right is correct.
        if "b" in walls:
            aux_map = fmap[:sw, :].copy()
            aux_map = np.rot90(aux_map) # Rotate counterclockwise - top of image moves to left of image
            c = _wall_field_rect(aux_map)
            if c > coverage:
                coverage = c

        if "t" in walls:
            aux_map = fmap[-sw:, :].copy()
            aux_map = np.fliplr(np.rot90(aux_map)) # rotate 90 deg counter clockwise (bottom to right), then mirror image
            c = _wall_field_rect(aux_map)
            if c > coverage:
                coverage = c
    return coverage


def _wall_field_rect(wfmap):
    '''Evaluate what fraction of the border area is covered by a single field in
    a rectangular or square arena

    Border coverage is provided as two values: 
        covered : the sum of the values across all sites immediately adjacent 
            to the border, where the values are calculated from the distance of
            those sites to the firing field, excluding NaN, inf, and masked values
        norm    : the number of non nan, inf, masked values considered in the 
            above sum

    The border area is defined by wfmap - this is the subsection of the binary 
    firing map of a  single field that lies within search_width of a border. 
    wfmap is must be of size NxM where
        N : arena_size / bin_size
        M : search_width
    and where the 0th column (wfmap[:,0], len()=N) repsents the sites closest 
    to the border

    wfmap: has value 1 inside the field and 0 outside the field
    '''
    if type(wfmap) != np.ma.MaskedArray:
        wfmap = np.ma.asanyarray(wfmap)
    N = wfmap.shape[0]
    wfmap[wfmap>1] = 1 # Just in case a still-labelled map has crept in
    inverted_wfmap = 1-wfmap 
    distance = distance_transform_edt(np.nan_to_num(inverted_wfmap.data, copy=True)) # scipy doesn't recognise masks
    distance = np.ma.masked_where(wfmap.mask, distance) # Preserve masking
    # distance_transform_edt(1-map) is the Python equivalent to (Matlab bwdist(map))
    # Cells in map with value 1 go to value 0
    # Cells in map with value 0 go to the geometric distance to the nearest value 1 in map

    adjacent_sites = distance[:,0]
    # Identify sites which are NaN, inf, or masked
    # Replace them with the next cell along the row, closest to the wall, that is not masked, nan, or inf
    adjacent_sites.mask += np.isnan(adjacent_sites.data)
    if adjacent_sites.mask.any():
        for i, rep in enumerate(adjacent_sites.mask):
            if rep:
                for j, val in enumerate(distance[i,:]):
                    if not distance.mask[i,j] and not np.isnan(val):
                        adjacent_sites[i] = val
                        adjacent_sites.mask[i] = False
                        break
    covered = np.ma.sum(adjacent_sites==0)
    contributing_cells = N - np.sum(adjacent_sites.mask) # The sum gives the number of remaining inf, nan or masked cells

    coverage = covered / contributing_cells

    return coverage

def _wall_field_circ(wfmap):
    '''
    Evaluate what fraction of the border area is covered by a single field in a
    circular arena
    '''
    raise NotImplementedError


def _validate_wall_definition(walls):
    '''Parse the walls argument for invalid entry'''
    if not isinstance(walls, str):
        raise ValueError("Wall definition must be given as a string, e.g." \
                         "'trbl'. %s is not a valid input." % str(walls))
    elif len(walls) > 4:
        raise ValueError("Wall definition may not exceed 4 characters. String"\
                         " '%s' contains %d characters." % (walls, len(walls)))
    elif len(walls) == 0:
        raise ValueError("Wall definition must contain at least 1 character"\
                         "from the set [t, r, b, l]")
    else:
        walls = walls.lower()
        for char in walls:
            if char.lower() not in ["t","r","b","l"]:
                raise ValueError("Character %s is not a valid entry in wall"\
                                 "definition. Valid characters are [t, r, b, l]" % char)
