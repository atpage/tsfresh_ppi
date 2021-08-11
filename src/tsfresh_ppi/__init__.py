
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, find_peaks_cwt, ricker
from tsfresh.feature_extraction.feature_calculators import set_property, _roll
from tsfresh.feature_extraction.settings import ComprehensiveFCParameters
#from tsfresh.utilities.string_manipulation import convert_to_output_format

"""These functions return various measures of "peak-to-peak" timing.
Peaks could represent, for example, steps in an accelerometer signal,
or pulses on a PPG, where high standard deviation in peak-to-peak
timing could indicate an irregular gait or heart rhythm.  tsfresh
already provides a *count* of peaks, but doesn't directly provide any
measure of *variability* in timing between the peaks.  This module
adds some measures of variability that are typically used in heart
rhythm analysis."""

############################## Helper functions: ###############################

def get_fc_parameters( method_options = ['normal','tsfresh','cwt'],
                       n_options = [1,3,5,10,15,20,25,50],
                       ms_options = [20,50],
                       include_comprehensive_defaults = True):
    """The `n` parameter depends heavily on the sample rate of the signal.
    Therefore, it will likely be beneficial to customize `n_options`
    for your application.

    The default ms_options are typical for HRV measurement; more
    details here: https://dx.doi.org/10.1136/heart.88.4.378
    """
    if include_comprehensive_defaults:
        params = ComprehensiveFCParameters()
    else:
        params = {}
    standard_params = [{'method': m, 'n': n} for m in method_options for n in n_options]
    extended_params = [{'method': m, 'n': n, 'ms': ms} for m in method_options for n in n_options for ms in ms_options]
    # TODO: rel_height = [0.25, 0.5, 0.75, 1.0] for 'normal' method
    # TODO: height = [0, None]?  0 might work for a wander-corrected signal.
    params[ppi_stdev] = standard_params
    params[ppi_rmssd] = standard_params
    params[ppi_sdsd] = standard_params
    params[ppi_nn] = extended_params
    params[ppi_pnn] = extended_params
    # TODO: ppi_npeaks
    return params

def get_peak_locs(x, method, n, height=None, rel_height=0.5):
    """Find the locations of the peaks in x.  x must be a Pandas Series.
    If x.index is a DatetimeIndex (or at least one level is), then the
    returned peak locations will be times.  Otherwise, they will be
    integers (i.e. row numbers).  Note that in the case where a Series
    has an integer index, the returned integers will represent the
    iloc, not necessarily the loc.
    """
    # TODO: how to handle missed samples/frames with int index?
    # e.g. if index goes [1, 3, 4, 5, 8, 9, 12] and we find peaks at
    # iloc 2 and 5, we'll think that the distance between them is 3
    # (rows), but really it was 5 (samples).  there may be nothing we
    # can do, unless user specifies a "sample #" index level.
    if type(x) != pd.Series:
        raise TypeError
    # Find peaks:
    if method=='normal':
        # this is similar to, but not exactly the same as, the tsfresh
        # `number_peaks` method.
        peak_locs, peak_props = find_peaks(
            x,
            distance = n,
            height = height,  # probably only useful with baseline wander removed

            # TODO?: prominence:
            # prominence = ... 1?  probably depends on signal variance.
            # wlen = ...  TODO?

            # TODO?: peak width:
            # width = ... 10?
            # rel_height = rel_height,
        )
        # TODO?: use prominences as features too?  e.g. mean
        # prominence?  could be a good indicator of recording quality?
    elif method=='tsfresh':
        # this is the same as the tsfresh `number_peaks` method.
        x_reduced = x[n:-n]
        res = None
        for i in range(1, n + 1):
            result_first = (x_reduced > _roll(x, i)[n:-n])
            if res is None:
                res = result_first
            else:
                res &= result_first
            res &= (x_reduced > _roll(x, -i)[n:-n])
        peak_locs = np.where(res)[0]
    elif method=='cwt':
        # this is the same as the tsfresh `number_cwt_peaks` method.
        peak_locs = find_peaks_cwt(
            x,
            widths = np.array(list(range(1, n + 1))),
            wavelet = ricker
            # TODO?:
            # max_distances = ...
            # gap_thresh = ...
            # min_length = ...
            # min_snr = ...
            # noise_percf = ...
            # window_size = ...
        )
    else:
        raise ValueError("method must be 'normal', 'tsfresh', or 'cwt'.")
    # Look for a DatetimeIndex:
    dt_level_name = None
    if type(x.index) == pd.MultiIndex:
        for level in x.index.levels:
            if type(level) == pd.DatetimeIndex:
                dt_level_name = level.name
                break
    elif type(x.index) == pd.DatetimeIndex:
        dt_level_name = x.index.name
    # Convert peak locations to times, if we can:
    if dt_level_name is not None:
        try:
            peak_loc_times = x.index.get_level_values(dt_level_name)[peak_locs]
        except IndexError:
            # we'll get here if peak_locs is empty, for instance.
            raise
            # TODO: anything else/different to do here?
    else:
        # just keep the integer indexing
        peak_loc_times = peak_locs
    return peak_loc_times

# TODO: find a way to prevent running these functions over and over
# for the same inputs.  (see 'combiner' custom feature type, with
# explanation and examples in
# https://tsfresh.readthedocs.io/en/latest/text/how_to_add_custom_feature.html
# and
# https://github.com/blue-yonder/tsfresh/blob/main/tsfresh/feature_extraction/feature_calculators.py)

def peaklocs_to_ppis(peak_locs):
    """peak_locs is a 1D array/series of peak locations, which may be
    represented as times or integers.  We'll convert it to the
    distance between peaks, which may be timedeltas or number of
    samples.
    """
    if len(peak_locs) < 2:
        return np.array([])
    ppis = peak_locs[1:] - peak_locs[:-1]
    return ppis

############################# Feature calculators: #############################

@set_property("fctype", "simple")
@set_property("input", "pd.Series")
def ppi_npeaks(x, method, n):
    """
    Number of peaks.

    :param x: the time series to calculate the feature of
    :type x: pandas.Series
    :param method: how to find peaks ('cwt' or 'normal')
    :type method: string
    :param n: peak width parameter
    :type n: int
    :return: the value of this feature
    :return type: int
    """
    # TODO: this is not useful yet, because tsfresh already computes
    # this.  but adding more parameters will make it different.
    try:
        peak_locs = get_peak_locs(x, method, n)
    except:
        return np.nan
    return len(peak_locs)

@set_property("fctype", "simple")
@set_property("input", "pd.Series")
def ppi_stdev(x, method, n):
    """
    Standard deviation in peak-to-peak intervals.

    :param x: the time series to calculate the feature of
    :type x: pandas.Series
    :param method: how to find peaks ('cwt' or 'normal')
    :type method: string
    :param n: peak width parameter
    :type n: int
    :return: the value of this feature
    :return type: float
    """
    try:
        peak_locs = get_peak_locs(x, method, n)
    except:
        return np.nan
    if len(peak_locs) < 3:
        return np.nan
    ppis = peaklocs_to_ppis(peak_locs)
    if type(ppis) == pd.TimedeltaIndex:
        ppis = ppis.total_seconds()
    return np.std(ppis)

@set_property("fctype", "simple")
@set_property("input", "pd.Series")
def ppi_rmssd(x, method, n):
    """
    Root mean square of successive differences between adjacent peak-to-peak intervals.

    :param x: the time series to calculate the feature of
    :type x: pandas.Series
    :param method: how to find peaks ('cwt' or 'normal')
    :type method: string
    :param n: peak width parameter
    :type n: int
    :return: the value of this feature
    :return type: float
    """
    try:
        peak_locs = get_peak_locs(x, method, n)
    except:
        return np.nan
    if len(peak_locs) < 3:
        return np.nan
    ppis = peaklocs_to_ppis(peak_locs)
    if type(ppis) == pd.TimedeltaIndex:
        ppis = ppis.total_seconds()
    differences = ppis[1:] - ppis[:-1]
    diff_sq = differences**2
    mean_diff_sq = np.mean(diff_sq)
    result = mean_diff_sq**0.5
    return result

@set_property("fctype", "simple")
@set_property("input", "pd.Series")
def ppi_sdsd(x, method, n):
    """
    Standard deviation of the successive differences between adjacent peak-to-peak intervals.

    :param x: the time series to calculate the feature of
    :type x: pandas.Series
    :param method: how to find peaks ('cwt' or 'normal')
    :type method: string
    :param n: peak width parameter
    :type n: int
    :return: the value of this feature
    :return type: float
    """
    try:
        peak_locs = get_peak_locs(x, method, n)
    except:
        return np.nan
    if len(peak_locs) < 3:
        return np.nan
    ppis = peaklocs_to_ppis(peak_locs)
    if type(ppis) == pd.TimedeltaIndex:
        ppis = ppis.total_seconds()
    differences = ppis[1:] - ppis[:-1]
    return np.std(differences)

@set_property("fctype", "simple")
@set_property("input", "pd.Series")
def ppi_nn(x, method, n, ms):
    """The number of pairs of successive peak-to-peak intervals that
    differ by more than `ms` ms in the case of a DatetimeIndex, or by
    `ms` samples otherwise.

    :param x: the time series to calculate the feature of
    :type x: pandas.Series
    :param method: how to find peaks ('cwt' or 'normal')
    :type method: string
    :param n: peak width parameter
    :type n: int
    :param ms: minimum difference in successive peak-to-peak intervals
    :type ms: float
    :return: the value of this feature
    :return type: int
    """
    try:
        peak_locs = get_peak_locs(x, method, n)
    except:
        return np.nan
    if len(peak_locs) < 3:
        return np.nan
    ppis = peaklocs_to_ppis(peak_locs)
    if type(ppis) == pd.TimedeltaIndex:
        ppis = ppis.total_seconds()
        ms = ms / 1000.0
    count = np.sum(ppis > ms)
    return count

@set_property("fctype", "simple")
@set_property("input", "pd.Series")
def ppi_pnn(x, method, n, ms):
    """
    The proportion of nn(peak_locs, ms) divided by total number of peak-to-peak intervals.

    :param x: the time series to calculate the feature of
    :type x: pandas.Series
    :param method: how to find peaks ('cwt' or 'normal')
    :type method: string
    :param n: peak width parameter
    :type n: int
    :param ms: minimum difference in successive peak-to-peak intervals, ms
    :type ms: float
    :return: the value of this feature
    :return type: float
    """
    try:
        peak_locs = get_peak_locs(x, method, n)
    except:
        return np.nan
    if len(peak_locs) < 3:
        return np.nan
    num_ppis = len(peak_locs) - 1
    over = ppi_nn(x, method, n, ms)
    result = float(over) / num_ppis
    return result

################################################################################

# TODO: more metrics from https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5422439/
# and https://www.ahajournals.org/doi/10.1161/01.CIR.93.5.1043
# and https://doi.org/10.1152/ajpheart.00421.2020, which is update to first one?
