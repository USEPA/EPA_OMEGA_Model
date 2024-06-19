"""

**OMEGA LD effects and MD effects join controller to generate LMDV effects.**

----

**CODE**

"""
from omega_effects.lmdv_join.join_main import join_results
from omega_effects.lmdv_join.employment_analysis_costs import EmploymentAnalysisCosts


def join_controller(set_paths, batch_settings, effects_log):
    """

    Args:
        set_paths: An instance of the SetPaths class.
        batch_settings: An instance of the BatchSettings class.
        effects_log: An instance of the EffectsLog class.

    Returns:
        Nothing, but it joins ld and md results into lmdv results and saves files to the run folder.

    """
    effects_log.logwrite(f'\nJoining ld and md sessions into lmdv effects')

    # join files _______________________________________________________________________________________________________
    join_results(set_paths, batch_settings, 'safety_effects_summary', effects_log)
    join_results(set_paths, batch_settings, 'safety_effects_by_body_style_summary', effects_log)
    join_results(set_paths, batch_settings, 'physical_effects_annual', effects_log)
    join_results(set_paths, batch_settings, 'physical_effects_annual_action_minus_no_action', effects_log)
    join_results(set_paths, batch_settings, 'cost_effects_annual', effects_log)
    join_results(set_paths, batch_settings, 'benefits_annual', effects_log)
    join_results(set_paths, batch_settings, 'safety_effects_legacy_vs_analysis', effects_log)
    join_results(set_paths, batch_settings, 'physical_effects_legacy_vs_analysis', effects_log)
    if batch_settings.net_benefit_ghg_scope in ['global', 'both']:
        join_results(set_paths, batch_settings, 'social_effects_global_ghg_annual', effects_log)
    if batch_settings.net_benefit_ghg_scope in ['domestic', 'both']:
        join_results(set_paths, batch_settings, 'social_effects_domestic_ghg_annual', effects_log)

    # employment analysis costs ________________________________________________________________________________________
    if batch_settings.run_employment_analysis_costs:
        employment_analysis_costs = EmploymentAnalysisCosts()
        employment_analysis_costs.employment_analysis_costs_for_batch(
            set_paths, batch_settings, 'vehicles', effects_log
        )
