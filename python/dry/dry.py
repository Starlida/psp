import numpy as np
from scipy.optimize import minimize_scalar
import pandas as pd
import in_out.gct as gct


def determine_assay_type(prov_code):
    """
    Convert assay_type from string to numpy array and compare to a list of allowable entries.

    Input
        -prov_code: string
    Output
        -assay_type: numpy string array, length=1
    """
    allowed_assay_types = np.array(["PR1", "GR1", "DR1"], dtype=np.str)
    assay_type = np.array(prov_code, dtype=np.str)

    # Check that assay type is one we expect
    if assay_type not in allowed_assay_types:
        error_msg = ("The first entry of the provenance code should be the assay type. " +
                     "Assay type not recognized. assay_type: {}")
        raise Exception(error_msg.format(assay_type))

    return assay_type


def update_prov_code(new_entry, existing_prov_code):
    """
    Append entry to provenance code.

    Input
        -new_entry: string
        -existing_prov_code: numpy string array
    Output
        -updated_prov_code : numpy string array
    """
    updated_prov_code = np.append(existing_prov_code, new_entry)
    return updated_prov_code


def parse_prov_code(prov_code):
    # Not sure when I'll use this, but seems good to keep
    # prov_code = "PR1+L2X+SF8+PF8.5"
    # expected_out = np.array(["PR1", "L2X", "SF8", "PF8.5"], dtype=np.str)
    # actual_out = dry.parse_prov_code(prov_code)
    # self.assertTrue(np.array_equal(actual_out, expected_out),
    #                 "Expected output: {}, Actual output: {}".format(expected_out, actual_out))
    # # Split along + in case there are other entries in the prov_code already
    # prov_code_chunks = np.array(prov_code.split("+"))
    pass


def filter_samples(df, sample_pct_cutoff):
    """
    Remove samples (i.e. columns) with more than sample_pct_cutoff NaN values.

    Input
        -df: pandas dataframe
        -sample_pct_cutoff: number
    Output
        -out_df: pandas dataframe (potentially smaller than original df)
    """
    # Number of NaNs per sample
    num_nans = df.isnull().sum()

    # Number of probes
    num_probes = df.shape[0]

    # Percent NaNs per sample
    pct_nans_per_sample = num_nans.divide(num_probes)

    # Only return samples with fewer % of NaNs than the cutoff
    out_df = df.loc[:, pct_nans_per_sample < sample_pct_cutoff]
    return out_df.values


def filter_probes(df, probe_pct_cutoff, probe_sd_cutoff):
    """
    Remove probes (i.e. rows) with more than probe_pct_cutoff NaN values.
    Also remove probes with standard deviation higher than probe_sd_cutoff.

    Input
        -df: pandas dataframe
        -probe_pct_cutoff: number
    Output
        -out_df: pandas dataframe (potentially smaller than original df)
    """

    # Number of NaNs per probe
    num_nans = df.isnull().sum(axis=1)

    # Number of samples
    num_samples = df.shape[1]

    # Percent NaNs per probe
    pct_nans_per_probe = num_nans.divide(num_samples)

    # Probe standard deviations
    probe_sds = df.std(axis=1)

    # Only return probes with fewer % of NaNs than the cutoff
    # and lower sd than the cutoff
    probes_to_keep = ((pct_nans_per_probe < probe_pct_cutoff) &
                      (probe_sds < probe_sd_cutoff))
    out_df = df.loc[probes_to_keep, :]
    return out_df


def manual_probe_rejection(df):
    """
    Also remove those probes that were manually selected for rejection.
    :param df:
    :return:
    """
    # Extract metadata
    # Only return probes marked TRUE
    pass


def optimize_sample_balance(df, offset_bounds=(-7, 7)):
    """
    For each sample, perform optimization to determine offset. Then, apply offset to data.

    Input
        -df: pandas dataframe
        -offset_bounds: tuple of floats, default=(-7, 7)
    Output
        -df_with_offsets: pandas dataframe
        -optimized_distances: numpy array of length=num_samples
    """
    # Determine the median value for each probe
    probe_medians = df.median(axis=1)

    # Initialize optimization outputs
    num_samples = df.shape[1]
    optimized_offsets = np.zeros(num_samples, dtype=float)
    optimized_distances = np.zeros(num_samples, dtype=float)
    unoptimized_distances = np.zeros(num_samples, dtype=float)
    success_bools = np.zeros(num_samples, dtype=bool)
    # N.B. 0 is the same as False if you specify that dtype is boolean

    # For each sample, perform optimization
    for sample_ind in range(num_samples):
        sample_vals = df.loc[:, sample_ind]

        # Calculate unoptimized distances
        unoptimized_distances[sample_ind] = function_to_optimize(0, sample_vals, probe_medians)

        # Calculate optimized distances
        optimization_result = minimize_scalar(function_to_optimize, args=(sample_vals, probe_medians),
                                              method="bounded", bounds=offset_bounds)

        # Return offset, optimized distance, and a flag indicating if the solution converged
        optimized_offsets[sample_ind] = optimization_result.x
        optimized_distances[sample_ind] = optimization_result.fun
        success_bools[sample_ind] = optimization_result.success

    # If any samples did not converge, display those sample indices
    if ~np.all(success_bools):
        print(("The following samples " +
               "failed to converge during optimization: \n{}").format(df.loc[:, ~success_bools]))
    # TO-DO(lev): Should we still apply these offsets?

    # Apply the optimized offsets
    df_with_offsets = df.add(optimized_offsets)

    # Return the df with offsets applied and the optimized distances
    return df_with_offsets, optimized_distances


def function_to_optimize(offset, values, medians):
    """
    This function computes a sort of variance for each sample.

    Input
        -offset: float
        -values: numpy array of floats
        -medians: numpy array of floats
    Output
        -out: float
    """
    out = sum(np.square((offset + values) - medians))
    return out


def remove_sample_outliers(df, distances, sd_sample_outlier_cutoff):
    """
    Calculate sample outlier cutoff and remove outlier samples.

    Input
        -df: pandas dataframe
        -distances: numpy array of floats
        -sd_sample_outlier_cutoff: float
    Output
        -df: pandas dataframe (potentially smaller than original df)
    """
    cutoff = np.mean(distances) + np.multiply(np.std(distances), sd_sample_outlier_cutoff)

    # Only return samples whose distance metric is lower than the cutoff
    return df[:, distances < cutoff]


def main():
    # gct_obj = gct.GCT("/Users/lev/code/PSP/python/functional_tests/test_p100.gct")
    # print(gct_obj.version)
    # gct_obj.read(row_inds=range(100),col_inds=range(10))
    # data = gct_obj.matrix
    # print(data)

    # if args.optim:
    #     (df, distances) = optimize_sample_balance(df, offset_bounds=(-7, 7))
    # else:
    #     (df, distances) = calculate_unoptim_distances(df)
    #
    # remove_sample_outliers(df, distances, sd_sample_outlier_cutoff=3)
    pass


# if __name__ == '__main__':
#     args = build_parser().parse_args(sys.argv[1:])
#     setup_logger.setup(args.verbose, args.log_file)
#     logger.debug("args:  {}".format(args))
#
#     make_args_abs_paths(args)
#     logger.debug("args after make_args_abs_paths args:  {}".format(args))
#
#     main(args)