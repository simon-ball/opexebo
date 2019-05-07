'''
Provides function to calculate the angular occupancy, i.e. the frequency with 
which the animal looked in each direction

Closely based on code from Horst's initial imaging pipeline, tidied up and pythonised by Simon

(C) 2019 Horst Oberhaus, Simon Ball
'''
import numpy as np
from scipy.ndimage.filters import gaussian_filter1d

def angularoccupancy(head_angle,**kwargs):
    '''
    Calculate angular occupancy from tracking angle and kwargs over (0,2*pi)
    
    Parameters
    ----------
    head_angle : numpy array
        Head angle in radians
    **kwargs : 
        bins_angular : int
            how many bins? default: 180
        sigma_angle : float
            Sigma of Gaussian smoothing kernel
            If this keyword is ommitted, then no smoothing
        
    Returns
    -------
    masked_histogram : numpy masked array
        Angular histogram, masked (where no tracking data) and smoothed (with gaussian kernel)
    bins_angle : numpy array
        Histogram edges in radians
    '''
    bins_angle = kwargs.get('bins_angle', 180)

    
    angle_histogram, bins_angle = np.histogram(head_angle, bins=bins_angle, range=(0,2*np.pi))
    angle_histogram = np.array(angle_histogram,dtype=float)
    angle_histogram_unfiltered = angle_histogram
    if 'sigma_angle' in kwargs:
        sigma_angle = kwargs.get('sigma_angle')
        angle_histogram = gaussian_filter1d(angle_histogram, sigma=sigma_angle, mode='nearest')
    masked_angle_histogram = np.ma.masked_where(angle_histogram_unfiltered==0, angle_histogram)

    return masked_angle_histogram, bins_angle