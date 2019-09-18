
Common Use Cases
================

Running a Performance Neutral Batch
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are several possible approaches to running a set of performance neutral simulations.  All methods share the same basic approach:

1.	Define a performance baseline simulation
2.	Run a set of alternative simulations, sweeping the engine size (or potentially other parameters) across a range
3.	Examine the simulation results and pick out the runs that meet the baseline performance

The performance baseline is defined using the ``PB:`` (Performance Baseline) tag and must be defined prior to performance neutral simulations which use the ``PN:`` (Performance Neutral) tag.  For example:

::

    sim_batch.config_set = {
        ['PKG:BL  + PB:1 + ENG:' GDI_ENGINE ' ... ]
        ['PKG:TDS + PN:1 + ENG:' TDS12_ENGINE ' ... ' || ES_PCT:[75:5:125]']
        };

The above example is abbreviated but demonstrates several points.

* The use of the ``PKG:`` tag to define a quick reference name for each case - ``BL`` for the baseline and ``TDS`` for the turbo-downsized case
* The baseline is defined prior to the performance neutral case
* The performance neutral case sweeps engine size using the ``ES_PCT:`` tag, although it is possible to use other tags
* The ``ES_PCT:`` tag is on the right hand side of the ``'||'`` separator
* The engine names are stored as strings in two workspace variables, ``GDI_ENGINE`` and ``TDS12_ENGINE`` which keeps the config set concise and improves readability

The ``ES`` in the ``ES_PCT:`` tag refers to Engine Scaling, in this case by  percent.  The unique thing about this tag is that ES_PCT:100 would be relative to an engine scaled approximately for performance neutrality, rather than an absolute scale.  The ``REVS_preprocess_sim_case`` script takes an initial guess at performance neutral engine sizing based on the engine's rated power and torque, the transmission and axle ratios, tire size, and roadload improvements, etc.  However, the approximation can't compensate for differences in transmission efficiency or other factors that might affect vehicle performance like torque converter strategy or transmission shift times, hence the need to run a set of simulations, typically both smaller and larger than the nominal sizing.

Multiple baselines may be defined in a single batch, keeping in mind that each baseline precedes its performance neutral cases.

``REVS_postprocess_sim_batch``, the default sim batch post-processing script, implements one possible method for picking out the "winning" performance neutral result from among a set of simulations.  The script finds the unique simulation cases and picks the case that meets or exceeds the baseline performance and has the lowest CO2 result.  Other strategies could be implemented as well, such as picking the smallest engine that meets performance, regardless of CO2.

The default performance criteria is the total performance time, defined as the sum of zero-to-sixty time, thirty-to-fifty time, fifty-to-seventy time and quarter mile time.

A relatively small performance neutral batch may be run on a single machine, simply running the batch as usual and using the default post processing.  For larger batches, we use a multi-pass and parallel simulation approach.  The multi-pass methodology starts with an initial coarse sizing (typically something like 75% / 100% / 125%) then runs one or two more batches with successively narrower and finer scaling increments until the desired level of scaling and performance accuracy has been met.  The multi-pass method can also be applied without the parallel processing as long as appropriate script changes are made.

.. raw:: html

    <style> .red {color:#dd0000; font-weight:bold; font-size:16px} </style>

.. role:: red

:red:`These functions are not in the REVS_Common... maybe they should be?`

Running a Batch with Various Engines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The typical method of running several engines is simply to define the engine names as strings in the workspace then set up simulation cases for each one.  For example:

::

    GDI_ENGINE             = 'ENG:engine_2013_Chevrolet_Ecotec_LCV_2L5_Reg_E10';
    TDS12_ENGINE           = 'ENG:engine_2016_Honda_L15B7_1L5_Tier2';
    TDS12_ENGINE2          = 'ENG:engine_2016_Honda_Turbo_1L5_paper_image';
    TDS21_ENGINE           = 'ENG:engine_future_Ricardo_EGRB_1L0_Tier2';
    TDS11_ENGINE           = 'ENG:engine_2015_Ford_EcoBoost_2L7_Tier2';
    TDS11_ENGINE2          = 'ENG:engine_2013_Ford_EcoBoost_1L6_Tier2';
    ATK2p0_ENGINE          = 'ENG:engine_2014_Mazda_Skyactiv_2L0_Tier2';
    ATK2p0_CEGR_ENGINE     = 'ENG:engine_future_atkinson_CEGR_2L0_tier2';
    TNGA_ENGINE            = 'ES_CYL:6 + ENG:engine_2016_toyota_TNGA_2L5_paper_image';
    ATK2p5_ENGINE          = 'ENG:engine_2016_Mazda_Skyactiv_Turbo_2L5_Tier2';
    ATK2p0_X_ENGINE        = 'ENG:engine_future_Mazda_Skyactiv_X_2L0_paper_image';

    sim_batch.config_set = {
        ['PKG:1a + ' base_config TDS11_ENGINE2 	    ...]
        ['PKG:1b + ' base_config TDS11_ENGINE  	    ...]
        ['PKG:1c + ' base_config TDS12_ENGINE2 	    ...]
        ['PKG:1d + ' base_config TDS12_ENGINE 	    ...]
        ['PKG:1e + ' base_config TDS21_ENGINE 	    ...]
        ['PKG:1f + ' base_config ATK2p0_ENGINE 	    ...]
        ['PKG:1g + ' base_config TNGA_ENGINE 	    ...]
        ['PKG:1h + ' base_config ATK2p5_ENGINE 	    ...]
        ['PKG:1i + ' base_config ATK2p0_X_ENGINE    ...]
        ['PKG:1j + ' base_config ATK2p0_CEGR_ENGINE ...]
    ...
    };

In this abbreviated example, base_config refers to a workspace variable that holds a string of the config tags that all the cases have in common, for example roadload settings, drive cycle selection, fuel type, etc.  Grouping the common settings into a single variable makes it easier to change the setup and improves readability.  Matlab string concatenation does the rest (the use of brackets, [ ], tells Matlab to combine all the separate strings into one).   Another advantage of using workspace variables to hold engine definition strings is illustrated in the ``TNGA_ENGINE`` workspace variable which not only defines the engine but also uses the ``ES_CYL:`` tag to  tell the simulation to run it as a six-cylinder regardless of any engine resizing that may take place, such as during performance neutral sizing.  Breaking a config string down into smaller substrings and workspace variables is a good technique for managing complexity in larger batches.

Generating ALPHA Roadload ABCs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Drive Cycles
^^^^^^^^^^^^

Turnkey Drive Cycles
--------------------

Making Custom Drive Cycles
--------------------------


