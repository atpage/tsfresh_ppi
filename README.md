# tsfresh_ppi

This package provides some peak-to-peak interval (PPI) variability features to augment `tsfresh` [1].
Currently, `tsfresh` will find and count peaks using a couple of different methods.
However, it does not measure the variability in timing between those peaks.

## Installation

Option 1: Clone this repo.  Install prereqs from `requirements.txt`.  Then install the cloned directory, e.g. with `pip3 install -e [repo path]`.

Option 2: Install directly from PyPI (`tsfresh-ppi`).

## Usage

    from tsfresh import extract_features
    from tsfresh_ppi import get_fc_parameters

    my_signal = ...  # some pandas DataFrame

    # The default way to extract features with tsfresh looks something like this:
    features = extract_features(
        my_signal,
        ...
    )

    # This is how to get all of the default tsfresh features, plus default PPI features:
    fc_params_with_ppi = get_fc_parameters()
    features = extract_features(
        my_signal,
        default_fc_parameters = fc_params_with_ppi,
        ...
    )

## References
[1] https://github.com/blue-yonder/tsfresh
