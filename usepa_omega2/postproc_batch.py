"""
postproc_batch.py
=================

post-process batch results
"""


def run_postproc(batch_log, batch_summary_filename):
    batch_log.logwrite('\nPost-processing batch summary file %s...' % batch_summary_filename)

    # TODO: create summary delta file here
    batch_delta_filename = batch_summary_filename.replace('results','delta')
