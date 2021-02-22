"""
postproc_batch.py
=================

post-process batch results
"""

import pandas as pd

def run_postproc(batch_log, batch_summary_filename):
    """
    Post-process a batch run.  Create summary delta file (session results minus reference session)

    Args:
        batch_log: batch log writer object
        batch_summary_filename: filename of batch summary results to post-process

    Returns:
        Creates a batch summary delta file

    """
    batch_log.logwrite('\nPost-processing batch summary file %s...' % batch_summary_filename)

    # create summary delta file
    batch_delta_filename = batch_summary_filename.replace('results', 'deltas')

    summary_df = pd.read_csv(batch_summary_filename)
    session_names = summary_df['session_name'].unique()

    # define, cache and clear non-delta columns
    non_delta_dict = dict()
    non_delta_columns = ['session_name', 'calendar_year']
    for ndc in non_delta_columns:
        non_delta_dict[ndc] = summary_df[ndc]
        summary_df[ndc] = 0

    # create delta dataframe
    delta_df = summary_df.copy()
    num_rows = delta_df.shape[0]

    num_analysis_years = int(num_rows / len(session_names))

    # sanity check rows per session
    if num_analysis_years * len(session_names) == num_rows:
        for i, row in enumerate(summary_df.iterrows()):
            reference_index = int(i % num_analysis_years)
            delta_df.iloc[i] = summary_df.iloc[i] - summary_df.iloc[reference_index]

        # restore cached values for non-delta columns
        for ndc in non_delta_columns:
            delta_df[ndc] = non_delta_dict[ndc]

        delta_df.to_csv(batch_delta_filename, index=False)
    else:
        batch_log.logwrite('\nUnexpected number of summary rows per session')


if __name__ == '__main__':
    batch_summary_filename = 'C:\dev\GitHub\EPA_OMEGA_Model\\bundle\\2021_02_11_14_31_30_multiple_session_batch\summary_results.csv'
