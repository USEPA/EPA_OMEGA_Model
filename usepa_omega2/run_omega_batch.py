from usepa_omega2 import *


class OMEGABatchObject(object):
    def __init__(self, name='', **kwargs):
        self.name = name
        self.output_path = ".\\"
        self.sessions = []
        self.dataframe = []

    def force_numeric_params(self):
        import pandas as pd

        numeric_params = {
            'Cost Curve Affinity Factor',
        }

        for p in numeric_params:
            self.dataframe.loc[p] = pd.to_numeric(self.dataframe.loc[p])

    def read_parameter(self, index_str):
        return self.dataframe.loc[index_str][0]

    def parse_parameter(self, index_str, column_index, verbose=False):
        raw_param = self.dataframe.loc[index_str][column_index]
        params_dict = {'Y': 'Y',
                       'N': 'N',
                       'TRUE': True,
                       'FALSE': False,
                       'Cost Clouds': 'Cost Clouds',
                       'Cost Curves': 'Cost Curves',
                       'Flat': 'Flat',
                       'Footprint': 'Footprint',
                       }

        if type(raw_param) is str:
            if verbose: print('%s = "%s"' % (index_str, raw_param))
            try:
                param = eval(raw_param, {'__builtins__': None}, params_dict)
            except:
                param = raw_param
            return param
        else:
            if verbose: print('%s = %s' % (index_str, raw_param.__str__()))
            return raw_param

    def set_parameter(self, index_str, column_index, value):
        self.dataframe.loc[index_str][column_index] = value

    def parse_column_params(self, column_index, verbose=False):
        fullfact_dimensions = []
        for index_str in self.dataframe.index:
            if type(index_str) is str:
                param = self.parse_parameter(index_str, column_index)
                self.set_parameter(index_str, column_index, param)
                if type(param) is tuple:
                    if verbose: print('found tuple')
                    fullfact_dimensions.append(param.__len__())
                else:
                    fullfact_dimensions.append(1)
            else:
                fullfact_dimensions.append(1)
        if verbose: print('fullfact dimensions = %s' % fullfact_dimensions)
        return fullfact_dimensions

    def parse_dataframe_params(self, verbose=False):
        fullfact_dimensions_vectors = []
        for column_index in range(0, self.dataframe.columns.__len__()):
            fullfact_dimensions_vectors.append(self.parse_column_params(column_index, verbose))
        return fullfact_dimensions_vectors

    def expand_dataframe(self, verbose=False):
        import pyDOE2 as doe
        import numpy as np

        acronyms_dict = {
            'Allow Backsliding': 'ABS',
            'Cost Curve Affinity Factor': 'CAF',
            False: '0',
            True: '1',
        }

        fullfact_dimensions_vectors = self.parse_dataframe_params(verbose=verbose)

        dfx = pd.DataFrame()
        dfx['Parameters'] = self.dataframe.index
        dfx.set_index('Parameters', inplace=True)
        session_params_start_index = np.where(dfx.index == 'Enable Session')[0][0]

        dfx_column_index = 0
        # for each column in dataframe, copy or expand into dfx
        for df_column_index in range(0, self.dataframe.columns.__len__()):
            df_ff_dimensions_vector = fullfact_dimensions_vectors[df_column_index]
            df_ff_matrix = np.int_(doe.fullfact(df_ff_dimensions_vector))
            num_expanded_columns = np.product(df_ff_dimensions_vector)
            # expand variations and write to dfx
            for variation_index in range(0, num_expanded_columns):
                column_name = self.dataframe.loc['Session Name'][df_column_index]
                session_name = column_name
                if num_expanded_columns > 1:  # expand variations
                    column_name = column_name + '_%d' % variation_index
                    dfx[column_name] = np.nan  # add empty column to dfx
                    ff_param_indices = df_ff_matrix[variation_index]
                    num_params = dfx.index.__len__()
                    for param_index in range(0, num_params):
                        param_name = dfx.index[param_index]
                        if type(param_name) is str:  # if param_name is not blank (np.nan):
                            if (dfx_column_index == 0) or (param_index >= session_params_start_index):
                                # copy all data for df_column 0 (includes batchsettings) or just session settings for subsequent columns
                                if type(self.dataframe.loc[param_name][df_column_index]) == tuple:  # index tuple and get this variations element
                                    value = self.dataframe.loc[param_name][df_column_index][ff_param_indices[param_index]]
                                else:
                                    value = self.dataframe.loc[param_name][df_column_index]  # else copy source value
                                dfx.loc[param_name, dfx.columns[dfx_column_index]] = value
                                if df_ff_dimensions_vector[param_index] > 1:
                                    # print(param_name + ' has ' + str(df_ff_dimensions_vector[param_index]) + ' values ')
                                    if acronyms_dict.__contains__(value):
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + acronyms_dict[value]
                                    else:
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + str(value)
                                    # print(session_name)
                    # dfx.loc['Session Name', dfx.columns[dfx_column]] = column_name
                    dfx.loc['Session Name', column_name] = session_name
                else:  # just copy column
                    dfx[column_name] = self.dataframe.iloc[:, df_column_index]
                dfx_column_index = dfx_column_index + 1
        #dfx.fillna('-----', inplace=True)
        self.dataframe = dfx

    def get_batch_settings(self):
        import glob

        self.name           = self.read_parameter('Batch Name')

    def num_sessions(self):
        return len(self.dataframe.columns)

    def add_sessions(self, verbose=True):
        if verbose:
            print()
            print("In Batch '{}':".format(self.name))
        for s in range(0, self.num_sessions()):
            self.sessions.append(OMEGASessionObject("session_{%d}" % s))
            self.sessions[s].parent = self
            self.sessions[s].get_session_settings(s)
            if verbose:
                print("Found Session %s:'%s'" % (s, batch.sessions[s].name))
        if verbose:
            print()


def validate_predefined_input(input_str, valid_inputs):
    if valid_inputs.__contains__(input_str):
        if type(valid_inputs) is dict:
            return valid_inputs[input_str]
        elif type(valid_inputs) is set:
            return True
        else:
            raise Exception('validate_predefined_input(...,valid_inputs) error: valid_inputs must be a set or dictionary')
    else:
        raise Exception('Invalid input "%s", expecting %s' % (input_str, str(valid_inputs)))


class OMEGASessionObject(object):
    def __init__(self, name, **kwargs):
        self.parent = []
        self.name = name
        self.num  = 0
        self.output_path = ".\\"
        self.enabled = False
        self.settings = []

    def read_parameter(self, index_str):
        return self.parent.dataframe.loc[index_str][self.num]

    def get_session_settings(self, session_num):
        self.num         = session_num
        true_false_dict  = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
        self.enabled     = validate_predefined_input(self.read_parameter('Enable Session'), true_false_dict)
        self.name        = self.read_parameter('Session Name')
        self.output_path = self.read_parameter('Session Output Path')

    def get_io_settings(self):
        print('Getting io settings...')
        self.settings = OMEGARuntimeOptions()

        # setup IOSettings
        if not options.dispy:
            self.settings.IOSettings.OutputPath = self.output_path + "\\"
        else:
            self.settings.IOSettings.OutputPath = self.output_path + "\\" + self.name

        self.settings.IOSettings.MarketDataFile = self.read_parameter('Market Data File')
        self.settings.IOSettings.MarketDataTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.MarketDataFile)

        self.settings.IOSettings.ParametersFile = self.read_parameter('Parameters File')
        self.settings.IOSettings.ParametersTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.ParametersFile)

        self.settings.IOSettings.TechnologiesFile = self.read_parameter('Technologies File')
        self.settings.IOSettings.TechnologiesTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.TechnologiesFile)

        self.settings.IOSettings.ScenariosFile = self.read_parameter('Scenarios File')
        self.settings.IOSettings.ScenariosTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.ScenariosFile)

        self.settings.IOSettings.FC1ImprovementsFile = self.read_parameter('FC1 Improvements File')
        self.settings.IOSettings.FC1ImprovementsTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.FC1ImprovementsFile)

        self.settings.IOSettings.FC2ImprovementsFile = self.read_parameter('FC2 Improvements File')
        self.settings.IOSettings.FC2ImprovementsTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.FC2ImprovementsFile)

        self.settings.IOSettings.FE1SimulatedFile = self.read_parameter('FE1 Simulated File')
        self.settings.IOSettings.FE1SimulatedTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.FE1SimulatedFile)

        self.settings.IOSettings.FE2SimulatedFile = self.read_parameter('FE2 Simulated File')
        self.settings.IOSettings.FE2SimulatedTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.FE2SimulatedFile)

        self.settings.IOSettings.BatteryCostsFile = self.read_parameter('Battery Costs File')
        self.settings.IOSettings.BatteryCostsFileTimestamp = System.IO.File.GetLastWriteTime(self.settings.IOSettings.BatteryCostsFile)

        self.settings.IOSettings.DisableLogWriter = False  #
        self.settings.IOSettings.WriteLogFiles = self.read_parameter('Compliance Logging') == 'GenerateAppliedComplianceLogsOnly'
        self.settings.IOSettings.WriteExtendedLogFiles = self.read_parameter('Compliance Logging') == 'GenerateAppliedAndExtendedComplianceLogs'

    def load_input_files(self):
        print("Loading Market Data (Industry) from {}...".format(self.settings.IOSettings.MarketDataFile))
        self.industry = volpecafe.IO.InputParsers.XlParser.ParseMarketData(self.settings.IOSettings.MarketDataFile)

        print("Loading Parameters from {}...".format(self.settings.IOSettings.ParametersFile))
        self.settings.Parameters = volpecafe.IO.InputParsers.XlParser.ParseParameters(self.settings.IOSettings.ParametersFile)

        print("Loading Technologies from {}...".format(self.settings.IOSettings.TechnologiesFile))
        self.settings.Technologies = volpecafe.IO.InputParsers.XlParser.ParseTechnologies(self.settings.IOSettings.TechnologiesFile)

        print("Loading Scenarios from {}...".format(self.settings.IOSettings.ScenariosFile))
        self.settings.Scenarios = volpecafe.IO.InputParsers.XlParser.ParseScenarios(self.settings.IOSettings.ScenariosFile)

        print("Loading FC1 Improvements from {}...".format(self.settings.IOSettings.FC1ImprovementsFile))
        volpecafe.VehicleSimulation.SimulationDatabase.ReloadSimulationData(self.settings.IOSettings.FC1ImprovementsFile, 0)

        print("Loading FC2 Improvements from {}...".format(self.settings.IOSettings.FC2ImprovementsFile))
        volpecafe.VehicleSimulation.SimulationDatabase.ReloadSimulationData(self.settings.IOSettings.FC2ImprovementsFile, 1)

        print("Loading FE1 Simulated from {}...".format(self.settings.IOSettings.FE1SimulatedFile))
        volpecafe.VehicleSimulation.SimulationDatabase.ReloadSimulationData(self.settings.IOSettings.FE1SimulatedFile, 2)

        print("Loading FE2 Simulated from {}...".format(self.settings.IOSettings.FE2SimulatedFile))
        volpecafe.VehicleSimulation.SimulationDatabase.ReloadSimulationData(self.settings.IOSettings.FE2SimulatedFile, 3)

        print("Loading Battery Costs from {}...".format(self.settings.IOSettings.BatteryCostsFile))
        volpecafe.VehicleSimulation.SimulationDatabase.ReloadSimulationData(self.settings.IOSettings.BatteryCostsFile, 4)

    def get_runtime_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        print('Getting runtime settings...')
        self.settings.OperatingModes.StartYear                = self.read_parameter('Begin technology applicaton starting in')

        self.settings.OperatingModes.ComplianceProgram        = validate_predefined_input(self.read_parameter('Compliance Program to Enforce'), dict({'CAFE':volpecafe.ComplianceProgram.CAFE,'CO2':volpecafe.ComplianceProgram.CO2}))

        self.settings.OperatingModes.MultiYearModeling        = validate_predefined_input(self.read_parameter('Use Multi-Year Modeling'), true_false_dict)
        self.settings.OperatingModes.AllowCreditTrading       = validate_predefined_input(self.read_parameter('Allow Credit Trading'), true_false_dict)
        self.settings.OperatingModes.LastCreditTradingYear    = self.read_parameter('Last Credit Trading Year')

        self.settings.OperatingModes.NoFines                  = validate_predefined_input(self.read_parameter('Force No Fines on All Manufacturers'), true_false_dict)
        self.settings.OperatingModes.Backfill                 = validate_predefined_input(self.read_parameter('Backfill Technologies'), true_false_dict)
        self.settings.OperatingModes.FleetAnalysis            = validate_predefined_input(self.read_parameter('Perform Fleet Analysis Calculations'), true_false_dict)

        self.settings.OperatingModes.DynamicFleetShare        = validate_predefined_input(self.read_parameter('Enable Dynamic Fleet Share and Sales Response'), true_false_dict)

        if validate_predefined_input(self.read_parameter('Sales Response Model Type'), {'NHTSASalesResponse', 'EPASalesResponse'}):
            self.settings.OperatingModes.useNHTSADynamicSalesResponse = self.read_parameter('Sales Response Model Type') == 'NHTSASalesResponse'
            self.settings.OperatingModes.useEPADynamicSalesResponse   = self.read_parameter('Sales Response Model Type') == 'EPASalesResponse'

        self.settings.OperatingModes.EPADynamicSalesResponsePriceElasticity = self.read_parameter('EPA Sales Response Price Elasticity')

        self.settings.OperatingModes.DynamicScrappage                    = validate_predefined_input(self.read_parameter('Enable Dynamic Scrappage'), true_false_dict)
        self.settings.OperatingModes.enableFleetRollupInDynamicScrappage = validate_predefined_input(self.read_parameter('Enable Fleet Rollup in Dynamic Scrappage'), true_false_dict)

        # self.settings.OperatingModes.ConsumerBenefitsScale  = self.read_parameter('Consumer Benefits Scale') / 100.0

        self.settings.OperatingModes.FuelPriceEstimates       = validate_predefined_input(self.read_parameter('AEO Fuel Price Case'), dict({'Low':volpecafe.Estimates.Low, 'Average':volpecafe.Estimates.Average, 'High':volpecafe.Estimates.High}))

        self.settings.OperatingModes.CO2Estimates             = validate_predefined_input(self.read_parameter('CO2 Value'), dict({'Low':volpecafe.Estimates.Low, 'Average':volpecafe.Estimates.Average, 'High':volpecafe.Estimates.High,'Very High':volpecafe.Estimates.VeryHigh}))

        self.settings.OperatingModes.IgnoreYearAvailable      = validate_predefined_input(self.read_parameter('Ignore Technology Year Available'), true_false_dict)
        self.settings.OperatingModes.IgnorePhaseIn            = validate_predefined_input(self.read_parameter('Ignore Technology Phase-In Caps'), true_false_dict)
        self.settings.OperatingModes.IgnoreRefreshRedesign    = validate_predefined_input(self.read_parameter('Ignore Vehicle Refresh/Redesign Schedules'), true_false_dict)

        self.settings.OperatingModes.useMultipleCPUs          = validate_predefined_input(self.read_parameter('Use Multiple CPUs'), true_false_dict)

        if validate_predefined_input(self.read_parameter('Car / Truck Credit Transfers'), {'NHTSASeparateCarTruckFleetCompliance','NHTSATotalCarTruckCreditsOnlyFor_mfrInCompliance','EPATotalCarTruckCreditsForAllComplianceChecks'}):
            self.settings.OperatingModes.useNHTSASeparateCarTruckComplianceCredits  = self.read_parameter('Car / Truck Credit Transfers') == 'NHTSASeparateCarTruckFleetCompliance'
            self.settings.OperatingModes.useNHTSACombinedCarTruckComplianceCredits  = self.read_parameter('Car / Truck Credit Transfers') == 'NHTSATotalCarTruckCreditsOnlyFor_mfrInCompliance'
            self.settings.OperatingModes.useEPACombinedCarTruckComplianceCredits    = self.read_parameter('Car / Truck Credit Transfers') == 'EPATotalCarTruckCreditsForAllComplianceChecks'

        if validate_predefined_input(self.read_parameter('Tech Ranking'), {'NHTSACAFEEfficiencyCalculation','OMEGAEfficiencyCalculation'}):
            self.settings.OperatingModes.useNHTSAEfficiencyCalculations     = self.read_parameter('Tech Ranking') == 'NHTSACAFEEfficiencyCalculation'
            self.settings.OperatingModes.useOMEGATechEfficiencyCalculation  = self.read_parameter('Tech Ranking') == 'OMEGAEfficiencyCalculation'

        self.settings.OperatingModes.useNHTSATruncateCO2CreditValues    = validate_predefined_input(self.read_parameter('NHTSA Efficiency Truncate CO2 Credit Value'), true_false_dict)
        self.settings.OperatingModes.useNHTSAExcludeValueLossTerm       = validate_predefined_input(self.read_parameter('NHTSA Efficiency Exclude Value Loss Term'), true_false_dict)
        self.settings.OperatingModes.useNHTSAValueLossOnlyForMaxHEV     = validate_predefined_input(self.read_parameter('NHTSA Efficiency Value Loss Only For Max HEV'), true_false_dict)

        if validate_predefined_input(self.read_parameter('Advanced Technology Multipliers'), {'ApplyMultipliersToRatedCO2','ApplyMultipliersToRatedCO2AndStandardCO2','EPALogicTBD'}):
            self.settings.OperatingModes.useNHTSAApplyMultipliersToRatedCO2             = self.read_parameter('Advanced Technology Multipliers') == 'ApplyMultipliersToRatedCO2'
            self.settings.OperatingModes.useNHTSAApplyMultipliersToRatedAndStandardCO2  = self.read_parameter('Advanced Technology Multipliers') == 'ApplyMultipliersToRatedCO2AndStandardCO2'
            self.settings.OperatingModes.useEPATechnologyMultipliers                    = self.read_parameter('Advanced Technology Multipliers') == 'EPALogicTBD'

        if validate_predefined_input(self.read_parameter('Upstream Emissions'), {'NoUpstreamAccounting','UpstreamAccounting','EPALogicTBD'}):
            self.settings.OperatingModes.useNHTSANoUpstreamAccounting   = self.read_parameter('Upstream Emissions') == 'NoUpstreamAccounting'
            self.settings.OperatingModes.useNHTSAUpstreamAccounting     = self.read_parameter('Upstream Emissions') == 'UpstreamAccounting'
            self.settings.OperatingModes.useEPAUpstreamAccounting       = self.read_parameter('Upstream Emissions') == 'EPALogicTBD'

        if validate_predefined_input(self.read_parameter('Credit Carryforward / Carryback'), {'NHTSACarryForwardCarryback', 'EPALogicTBD'}):
            self.settings.OperatingModes.useNHTSACarryforwardCarryback  = self.read_parameter('Credit Carryforward / Carryback') == 'NHTSACarryForwardCarryback'
            self.settings.OperatingModes.useEPACarryforwardCarryback    = self.read_parameter('Credit Carryforward / Carryback') == 'EPALogicTBD'

        self.settings.OperatingModes.useScenarioCO2OffsetACLeakageCreditFix = validate_predefined_input(self.read_parameter('Use Scenario CO2 Offset AC Leakage Credit Fix'), true_false_dict)

        if validate_predefined_input(self.read_parameter('Tech Application'), {'AddTechWhileEfficient', 'AddTechWhileNotInCompliance'}):
            self.settings.OperatingModes.useNHTSAAddTechWhileEfficient          = self.read_parameter('Tech Application') == 'AddTechWhileEfficient'
            self.settings.OperatingModes.useEPAAddTechWhileNotInCompliance      = self.read_parameter('Tech Application') == 'AddTechWhileNotInCompliance'

        if validate_predefined_input(self.read_parameter('Lingering Technologies'), {'AllowLingering','NoLingering'}):
            self.settings.OperatingModes.useNHTSAAllowLingering = self.read_parameter('Lingering Technologies') == 'AllowLingering'
            self.settings.OperatingModes.useEPANoLingering      = self.read_parameter('Lingering Technologies') == 'NoLingering'


    def get_postproc_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        print('Getting postproc settings...')
        self.settings.OperatingModes.useReboundCPMrefFix = validate_predefined_input(self.read_parameter('Use Rebound Cost per Mile Fix'), true_false_dict)

        self.settings.OperatingModes.addReboundFuelCostsDriveRefuelSurplusToHistoricEffects = validate_predefined_input(self.read_parameter('Add Rebound Fuel Costs / Drive & Refuel Surplus to Historic Fleet Effects'), true_false_dict)

        if validate_predefined_input(self.read_parameter('Labor Hours'), {'RegCost','TechCost'}):
            self.settings.OperatingModes.useLaborHoursBasedonRegCost  = self.read_parameter('Labor Hours') == 'RegCost'
            self.settings.OperatingModes.useLaborHoursBasedonTechCost = self.read_parameter('Labor Hours') == 'TechCost'

        self.settings.OperatingModes.useMassCoefficientSignFix = validate_predefined_input(self.read_parameter('Mass Safety Coefficient Sign'), dict({'WithoutError':True, 'WithError':False}))

        self.settings.OperatingModes.useDynamicMassSafetyCWThreshold = validate_predefined_input(self.read_parameter('Dynamic Fleet Curb Weight Threshold for Mass Safety'), dict({'DynamicCurbWeightThreshold':True, 'StaticCurbWeightThreshold':False}))

        if validate_predefined_input(self.read_parameter('Portion of Fleet Subject to Mass Safety Effect'), {'ComplianceFleetOnlyFromThresholdCurbWeights','ComplianceFleetOnly','LegacyAndComplianceFleetFromThresholdCurbWeight'}):
            self.settings.OperatingModes.useThresholdCWMassDeltasNoLegacyFleet   = self.read_parameter('Portion of Fleet Subject to Mass Safety Effect') == 'ComplianceFleetOnlyFromThresholdCurbWeights'
            self.settings.OperatingModes.useBaselineVehCWMassDeltasNoLegacyFleet = self.read_parameter('Portion of Fleet Subject to Mass Safety Effect') == 'ComplianceFleetOnly'
            self.settings.OperatingModes.useThresholdCWMassDeltasWithLegacyFleet = self.read_parameter('Portion of Fleet Subject to Mass Safety Effect') == 'LegacyAndComplianceFleetFromThresholdCurbWeight'

        self.settings.OperatingModes.useGliderWeightMR0CalcFix = validate_predefined_input(self.read_parameter('Glider Curb Weight at MR0 Calculation'), dict({'WithoutError':True, 'WithError':False}))

        self.settings.OperatingModes.useHistoricScrappageVehicleStyleSurvivalRateLogFix = validate_predefined_input(self.read_parameter('Use Historic Scrappage Vehicle Style Survival Rate Log Fix'), true_false_dict)

        # self.settings.OperatingModes.useDynamicScrappageSalesForecastInEffectsModel = validate_predefined_input(self.read_parameter('Use Dynamic Scrappage Sales Forecast in Effects Model'), true_false_dict)

        self.settings.OperatingModes.useTwoPassVMTScrappage = validate_predefined_input(self.read_parameter('Use Two-pass VMT and Scrappage Calculattions'), true_false_dict)

        if validate_predefined_input(self.read_parameter('Post-Compliance Years Sales Growth'),
                                     {'DSMFlatSales-EffMdlFleetAnalysisSalesGrowth', 'FlatSalesFromMaxComplianceYear', 'SalesGrowthFromFleetAnalysisSalesForecast', 'EPADynamicSalesModel'}):
            self.settings.OperatingModes.dynamicScrappageUseFlatSalesFromMaxComplianceYear       = self.read_parameter('Post-Compliance Years Sales Growth') == 'DSMFlatSales-EffMdlFleetAnalysisSalesGrowth' or \
                                                                                    self.read_parameter('Post-Compliance Years Sales Growth') == 'FlatSalesFromMaxComplianceYear'
            self.settings.OperatingModes.dynamicScrappageUseSalesGrowthFromFleetAnalysisValues   = self.read_parameter('Post-Compliance Years Sales Growth') == 'SalesGrowthFromFleetAnalysisSalesForecast'
            self.settings.OperatingModes.dynamicScrappageUseEPADynamicSalesModel                 = self.read_parameter('Post-Compliance Years Sales Growth') == 'EPADynamicSalesModel'

            self.settings.OperatingModes.effectsModelUseFlatSalesFromMaxComplianceYear           = self.read_parameter('Post-Compliance Years Sales Growth') == 'FlatSalesFromMaxComplianceYear'
            self.settings.OperatingModes.effectsModelUseSalesGrowthFromFleetAnalysisValues       = self.read_parameter('Post-Compliance Years Sales Growth') == 'DSMFlatSales-EffMdlFleetAnalysisSalesGrowth' or \
                                                                                    self.read_parameter('Post-Compliance Years Sales Growth') == 'SalesGrowthFromFleetAnalysisSalesForecast'
            self.settings.OperatingModes.effectsModelUseEPADynamicSalesModel                     = self.read_parameter('Post-Compliance Years Sales Growth') == 'EPADynamicSalesModel'

        self.settings.OperatingModes.useAnnualFleetGrowthRate       = validate_predefined_input(self.read_parameter('Use Annual Fleet Growth Rate'), true_false_dict)

        self.settings.OperatingModes.annualFleetGrowthRate          = self.read_parameter('Annual Fleet Growth Rate')

        self.settings.OperatingModes.useAnnualVMTGrowthRate         = validate_predefined_input(self.read_parameter('Use Annual VMT Growth Rate'), true_false_dict)

        self.settings.OperatingModes.annualVMTGrowthRate            = self.read_parameter('Annual VMT Growth Rate')

        self.settings.OperatingModes.VMTAdjustFirstAge              = self.read_parameter('VMT Adjust First Age')

        self.settings.OperatingModes.VMTAdjustMinVMT                = self.read_parameter('VMT Adjust Min VMT')

        self.settings.OperatingModes.dynamicScrappageModelMaxYear   = self.read_parameter('Scrappage Model Max Year')

        self.settings.OperatingModes.CPMLoanLengthYears             = self.read_parameter('Cost per Mile Loan Length Years')
        if not self.settings.OperatingModes.CPMLoanLengthYears >= 1:
            print('Cost per Mile Loan Length Years Must be >= 1')
            exit(-1)

        self.settings.OperatingModes.CPMTechCostValuation           = self.read_parameter('Cost per Mile Tech Cost Valuation')
        if not (0<= self.settings.OperatingModes.CPMTechCostValuation <= 1):
            print('Cost per Mile Tech Cost Valuation Must be Between 0 and 1')
            exit(-1)

        self.settings.OperatingModes.CPMFatalityCostValuation       = self.read_parameter('Cost per Mile Fatality Cost Valuation')
        if not (0<= self.settings.OperatingModes.CPMFatalityCostValuation <= 1):
            print('Cost per Mile Fatality Cost Valuation Must be Between 0 and 1')
            exit(-1)

        self.settings.OperatingModes.safetyRiskVMTElasticity = self.read_parameter('Safety Risk VMT Elasticity')
        if not (-1 <= self.settings.OperatingModes.safetyRiskVMTElasticity <= 0):
            print('Safety Risk VMT Elasticity Must be Between -1 and 0')
            exit(-1)
        # self.settings.OperatingModes.safetyRiskVMTElasticity = -self.settings.OperatingModes.safetyRiskVMTElasticity

    def monitor(self, width=10):
        import time

        i = 0
        t = 0
        while self.compliance.Running:
            time.sleep(1)
            t = t + 1
            i = (i + 1) % width
            print('.', end='', flush=True)
            if i == 0:
                try:
                    #print(f"{t}:SN{self.compliance.Progress.Scenario.Index}:{self.compliance.Progress.Manufacturer.ToString()}:MY{self.compliance.Progress.ModelYear.ToString()}")
                    print("%s:%s:SN%d:%s:MY%s" % (self.name, t, self.compliance.Progress.Scenario.Index, self.compliance.Progress.Manufacturer.ToString(), self.compliance.Progress.ModelYear.ToString()))
                except:
                    print('')

        print('')
        if self.compliance.Completed:
            print("Compliance Completed!")

        if self.compliance.Stopped:
            print("*** Compliance Stopped on Error ***", file=sys.stderr)

        print("Elapsed Time %d Seconds" % t)

    def init(self, validate_only=False):
        if not validate_only:
            print("Starting Session '%s' -> %s" % (self.name, self.output_path))
        self.get_io_settings()
        self.get_runtime_settings()
        self.get_postproc_settings()
        if not validate_only:
            self.load_input_files()
            self.compliance = volpecafe.Model.Compliance()  # create new compliance object

    def run(self):
        self.init()

        print("Starting Compliance Run...")
        self.compliance.Start(self.industry, self.settings)

        self.monitor()


def validate_file(filename):
    if not os.access(filename, os.F_OK):
        print("\n*** Couldn't access {}, check path and filename ***".format(filename), file=sys.stderr)
        exit(-1)


def validate_folder(batch_root, batch_name='', session_name=''):
    dstfolder = batch_root + os.sep
    if not batch_name == '':
        dstfolder = dstfolder + batch_name + os.sep
    if not session_name == '':
        dstfolder = dstfolder + session_name + os.sep

    if not os.access(dstfolder, os.F_OK):
        try:
            os.makedirs(dstfolder, exist_ok=True) # try create folder if necessary
        except:
            print("Couldn't access or create {}".format(dstfolder),file=sys.stderr)
            exit(-1)
    return dstfolder


def get_basename(filename):
    return os.path.basename(filename)


# returns name of file including extension, e.g. /somepath/somefile.txt -> somefile.txt
def get_filenameext(filename):
    return os.path.split(filename)[1]


def network_copyfile(remote_path, srcfile):
    dstfile = remote_path + os.sep + get_basename(srcfile)
    shutil.copyfile(srcfile, dstfile)


# move file out to shared directory and return the filename in that remote context
def relocate_file(remote_path, local_filename):
    network_copyfile(remote_path, local_filename)
    return get_basename(local_filename)


def sysprint(str):
    import os
    os.system('echo {}'.format(str))


def dispy_node_setup():
    import socket
    sysprint('node {} standing by...'.format(socket.gethostbyname(socket.gethostname())))
    sysprint('.')


def restart_job(job):
    dispy_debug = options.dispy_debug

    job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + ': #' + str(
        job.id['session_num'])

    if retry_count.__contains__(str(job.id)):
        retry_count[str(job.id)] += 1
    else:
        retry_count[str(job.id)] = 0

    if retry_count[str(job.id)] <= 10:
        if dispy_debug: sysprint('#### Retrying job %s ####\n' % job_id_str)
        new_job = dispycluster.cluster.submit(job.id['batch_name'], job.id['batch_path'], job.id['batch_file'],
                                              job.id['session_num'], job.id['session_name'])
        if new_job is not None:
            new_job.id = job.id
            retry_count[str(job.id)] += 1
            if dispy_debug: sysprint('#### Terminated job restarted %s ####\n' % job_id_str)
    else:  # too many retries, abandon job
        if dispy_debug: sysprint('#### Cancelling job %s, too many retry attempts ####\n' % job_id_str)


def job_cb(job):  # gets called for: (DispyJob.Finished, DispyJob.Terminated, DispyJob.Abandoned)
    import dispy
    dispy_debug = options.dispy_debug

    if job is not None:
        job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + ': #' + str(
            job.id['session_num'])
    else:
        job_id_str = 'NONE'

    status = job.status

    if status == dispy.DispyJob.Finished:
        if dispy_debug: sysprint('---- Job Finished %s: %s\n' % (job_id_str, job.result))
        if job.result is False:
            restart_job(job)

    elif status == dispy.DispyJob.Terminated:
        if dispy_debug: sysprint('---- Job Terminated %s \n' % str(job_id_str))
        restart_job(job)

    elif status == dispy.DispyJob.Abandoned:
        if dispy_debug: sysprint('---- Job Abandoned %s : Exception %s\n' % (job_id_str, job.exception))
        restart_job(job)

    else:
        if dispy_debug: sysprint('*** uncaught job callback %s %s ***\n' % (job_id_str, status))

    return


# 'cluster_status' callback function. It is called by dispy (client)
# to indicate node / job status changes.
def status_cb(status, node, job):
    # global sim_jobs, terminated_jobs, retry_count, config_case, minimum_batch_size, found_node_list, found_node_matlabs, dispy_debug
    import dispy

    dispy_debug = options.dispy_debug

    # SOMETIMES job comes in as an "int" instead of an object, then it throws an error here... not sure why!
    # SEEMS to be associated with those jobs that run fine but don't finish by adding the "_"
    # NOT all jobs have this problem... keep an eye on this and see if we have the same problem in the cluster...
    if job is not None:
        try:
            job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + ': #' + str(
                job.id['session_num'])
        except:
            sysprint('#### job_id object FAIL ### "%s"\n' % str(job))
            job_id_str = str(job)
            pass
    else:
        job_id_str = 'NONE'

    if status == dispy.DispyJob.Created:
        if dispy_debug: sysprint('++++ Job Created, Job ID %s\n' % job_id_str)

    elif status == dispy.DispyJob.Running:
        if dispy_debug: sysprint('++++ Job Running, Job ID %s\n' % job_id_str)

    elif status == dispy.DispyJob.Finished:
        if dispy_debug: sysprint('++++ status_cb Job Finished %s: %s\n' % (job_id_str, job.result))
        return

    elif status == dispy.DispyJob.Terminated:
        if dispy_debug: sysprint('++++ status_cb Job Terminated %s\n' % job_id_str)
        return

    elif status == dispy.DispyJob.Cancelled:
        if dispy_debug: sysprint('++++ Job Cancelled %s : Exception %s\n' % (job_id_str, job.exception))

    elif status == dispy.DispyJob.Abandoned:
        if dispy_debug: sysprint('++++ status_cb Job Abandoned %s : Exception %s\n' % (job_id_str, job.exception))
        return

    elif status == dispy.DispyJob.ProvisionalResult:
        return

    elif status == dispy.DispyNode.Initialized:
        if dispy_debug: sysprint('++++ Node %s with %s CPUs available\n' % (node.ip_addr, node.avail_cpus))

    elif status == dispy.DispyNode.Closed:
        if dispy_debug: sysprint('++++ Node Closed %s *** \n' % node.ip_addr)

    elif status == dispy.DispyNode.AvailInfo:
        if dispy_debug: sysprint('++++ Node Available %s *** \n' % node.ip_addr)

    else:
        if node is not None:
            if dispy_debug: sysprint('++++ uncaught node status %s %s ***\n' % (node.ip_addr, status))
        else:
            if dispy_debug: sysprint('++++ uncaught job status %s %s ***\n' % (job.id, status))
    return


def dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name, retry_count=0):
    import sys, subprocess
    #call shell command
    pythonpath = sys.exec_prefix
    if pythonpath.__contains__('envs'):
        pythonpath = pythonpath + "\\scripts"
    cmd = '{}\\python "{}\\{}\\run_dse2_batch.py" --bundle_path "{}" --batch_file "{}.csv" --session_num {} --no_validate'.format(pythonpath, network_batch_path_root, batch_name, network_batch_path_root, batch_file, session_num)
    sysprint('.')
    sysprint(cmd)
    sysprint('.')
    subprocess.call(cmd)
    # remove temporary dll folder for this session:
    dllpath = "C:\\Users\\Public\\temp\\%s\\" % (batch_name + '_' + session_name)
    sysprint('Removing ' + dllpath)
    shutil.rmtree(dllpath, ignore_errors=False)

    summary_filename = os.path.join(network_batch_path_root, batch_name, session_name, 'output\\logs\\Summary.txt')

    time.sleep(5) # wait for summary file to finish writing?

    if os.path.exists(summary_filename) and os.path.getsize(summary_filename) > 0:
        f_read = open(summary_filename, "r")
        last_line = f_read.readlines()[-1]
        f_read.close()
        batch_path = os.path.join(network_batch_path_root, batch_name)
        if last_line.__contains__("Standard Compliance Model Completed"):
            os.rename(os.path.join(batch_path, session_name), os.path.join(batch_path, '_' + session_name))
            sysprint('^^^ dispy_run_session Standard Compliance Model Completed, Session %s ^^^' % session_name)
            return True
        elif last_line.__contains__("Standard Compliance Model Stopped"):
            os.rename(os.path.join(batch_path, session_name), os.path.join(batch_path, '#FAIL_' + session_name))
            sysprint('???? Standard Compliance Model Stopped, Session %s ????' % session_name)
            return False
        else:
            sysprint('???? Weird Summary File for Session %s : last_line = "%s" ????' % (session_name, last_line))
            return False
    else:
        sysprint('???? No Summary File for Session %s, path_exists=%d, non_zero=%d ????' % (session_name, os.path.exists(summary_filename), os.path.getsize(summary_filename) > 0))
        if retry_count < 3:
            sysprint('???? Trying Session %s again (attempt %d)... ????' % (session_name, retry_count+1))
            dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name, retry_count=retry_count+1)
        else:
            sysprint('???? Abandoning Session %s... ????' % session_name)
        return False


class DispyCluster(object):
    def __init__(self, scheduler):
        import dispy
        self.master_ip = ''
        self.desired_node_list = []
        self.found_node_list = []
        self.sleep_time_secs = 10
        if scheduler is not None:
            self.scheduler_node = scheduler
        else:
            # self.scheduler_node = '204.47.182.182'
            self.scheduler_node = '204.47.184.69'
        if options.dispy_debug:
            self.loglevel = dispy.logger.DEBUG
        else:
            self.loglevel = dispy.logger.INFO
        self.total_cpus = 0
        self.cluster = None

    def find_nodes(self):
        import dispy, socket, time

        print("Finding dispynodes...")
        self.master_ip = socket.gethostbyname(socket.gethostname())
        if options.one_ping_only or options.network:
            # self.desired_node_list = ['204.47.182.182', '204.47.182.60', '204.47.185.53', '204.47.185.67',
            #                           '204.47.184.69', '204.47.184.60', '204.47.184.72', '204.47.184.63',
            #                           '204.47.184.59']
            # self.desired_node_list = ['204.47.182.182', '204.47.182.60', '204.47.185.53', '204.47.185.67']
            self.desired_node_list = ['204.47.184.69', '204.47.184.60', '204.47.184.72', '204.47.184.63',
                                      '204.47.184.59']
        elif options.local:
            self.desired_node_list = self.master_ip  # for local run
        elif options.mazer:
            self.desired_node_list = ['172.16.24.11']
        elif options.doorlag:
            self.desired_node_list = ['172.16.28.28']
        elif options.newman40:
            self.desired_node_list = ['172.16.24.12']
        elif options.dekraker:
            self.desired_node_list = ['172.16.24.10']
        else:
            self.desired_node_list = []  # to auto-discover nodes, only seems to find the local node

        if options.exclusive:
            print('Starting JobCluster...')
            cluster = dispy.JobCluster(dispy_node_setup, nodes=self.desired_node_list, ip_addr=self.master_ip, pulse_interval=60, reentrant=True,
                                   ping_interval=10, loglevel=self.loglevel, port=0, depends=[sysprint])
        else:
            print('Starting SharedJobCluster...')
            cluster = dispy.SharedJobCluster(dispy_node_setup, nodes=self.desired_node_list, ip_addr=self.master_ip, reentrant=True,
                                   loglevel=self.loglevel, depends=[sysprint], scheduler_node=self.scheduler_node, port=0)

        # need to wait for cluster to startup and transfer dependencies to nodes...
        t = 0
        while t < self.sleep_time_secs:
            print('t minus ' + str(self.sleep_time_secs - t))
            time.sleep(1)
            t = t + 1

        info_jobs = []
        self.found_node_list = []
        node_info = cluster.status()
        for node in node_info.nodes:
            self.total_cpus = self.total_cpus + node.cpus
            print('Submitting %s' % node.ip_addr)
            job = cluster.submit_node(node)
            if (job is not None):
                job.id = node.ip_addr
                info_jobs.append(job)
                self.found_node_list.append(node.ip_addr)

        if self.found_node_list == []:
            print('No dispy nodes found, exiting...', file=sys.stderr)
            sys.exit(-1)  # exit, no nodes found

        print('Found Node List: %s' % self.found_node_list)
        print('Found %d cpus' % self.total_cpus)

        cluster.wait()
        cluster.print_status()
        cluster.close()

    def submit_sessions(self, batch_name, batch_path, batch_file, session_list):
        import dispy, socket, time

        if options.exclusive:
            print('Starting JobCluster...')
            self.cluster = dispy.JobCluster(dispy_run_session, nodes=self.found_node_list, ip_addr=self.master_ip, pulse_interval=60, reentrant=True,
                                   ping_interval=10, loglevel=self.loglevel, port=0, depends=[sysprint], cluster_status=status_cb, callback=job_cb)
        else:
            print('Starting SharedJobCluster...')
            self.cluster = dispy.SharedJobCluster(dispy_run_session, nodes=self.found_node_list, ip_addr=self.master_ip, reentrant=True,
                                   loglevel=self.loglevel, depends=[sysprint], scheduler_node=self.scheduler_node, port=0, cluster_status=status_cb, callback=job_cb)

        time.sleep(self.sleep_time_secs)  # need to wait for cluster to startup and transfer dependencies to nodes...

        # process sessions:
        session_jobs = []
        for session_num in session_list:
            print("Processing Session %d: " % session_num, end='')

            if not batch.sessions[session_num].enabled:
                print("Skipping Disabled Session '%s'" % batch.sessions[session_num].name)
                #print('')
            else:
                print("Submitting Session '%s' to Cluster..." % batch.sessions[session_num].name)
                #print('')
                job = self.cluster.submit(batch_name, batch_path, batch_file, session_num, batch.sessions[session_num].name)
                if (job != None):
                    # job.id = (batch_name, batch_path, batch_file, session_num, batch.sessions[session_num].name)
                    job.id = dict({'batch_name':batch_name, 'batch_path':batch_path, 'batch_file':batch_file, 'session_num':session_num, 'session_name':batch.sessions[session_num].name})
                    session_jobs.append(job)
                else:
                    print('*** Job Submit Failed %s ***' % str(job.id), file=sys.stderr)

        print('Waiting for cluster to run sessions...')

        self.cluster.wait()
        self.cluster.print_status()
        self.cluster.close()


class runtime_options(object):
    def __init__(self):
        self.validate_batch = True
        self.local = True
        self.network = False
        self.exclusive = False
        self.bundle_path_root = ''
        self.batch_file = ''
        self.batch_path = ''
        self.session_path = ''
        self.session_num = []
        self.bundle = False
        self.dispy = False
        self.dispy_debug = False
        # self.mazer = False
        # self.doorlag = False
        # self.newman40 = False
        # self.dekraker = False
        self.one_ping_only = False
        self.no_sim = False
        self.verbose = False
        self.scheduler = '204.47.182.182'


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run an OMEGA compliance batch available on the network on one or more dispyNodes')
    parser.add_argument('--no_validate', action='store_true', help='Skip validating batch file')
    parser.add_argument('--no_sim', action='store_true', help='Skip running simulations')
    parser.add_argument('--exclusive', action='store_true', help='Run exclusive job, do not share dispynodes')
    parser.add_argument('--bundle_path', type=str, help='Path to folder visible to all nodes')
    parser.add_argument('--batch_file', type=str, help='Path to session definitions visible to all nodes')
    parser.add_argument('--session_num', type=int, help='ID # of session to run from batch')
    parser.add_argument('--bundle', action='store_true', help='True = gather and copy all source files to bundle_path')
    parser.add_argument('--dispy', action='store_true', help='True = run sessions on dispynode(s)')
    parser.add_argument('--dispy_ping', action='store_true', help='True = ping dispynode(s)')
    parser.add_argument('--dispy_debug', action='store_true', help='True = enable verbose dispy debug messages)')
    parser.add_argument('--verbose', action='store_true', help='True = enable verbose omega_batch messages)')
    parser.add_argument('--scheduler', type=str, help='Override default dispy scheduler IP address',default= None)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--local', action='store_true', help='Run only on local machine, no network nodes')
    group.add_argument('--network', action='store_true', help='Run on local machine and/or network nodes')

    args = parser.parse_args()

    options = runtime_options()
    options.validate_batch          = not args.no_validate
    options.exclusive               = args.exclusive
    options.bundle_path_root        = args.bundle_path
    options.batch_file              = args.batch_file
    options.local                   = args.local
    options.network                 = args.network
    options.session_num             = args.session_num
    options.bundle                  = args.bundle or args.dispy # or (options.bundle_path_root is not None)
    options.dispy                   = args.dispy
    options.dispy_debug             = args.dispy_debug
    options.one_ping_only           = args.dispy_ping
    options.no_sim                  = args.no_sim
    options.verbose                 = args.verbose
    options.scheduler               = args.scheduler

    # get batch info
    import sys, os, socket, shutil
    import pandas as pd
    from datetime import datetime
    import numpy as np

    if options.one_ping_only:
        dispycluster = DispyCluster(options.scheduler)
        dispycluster.find_nodes()
        print("*** ping complete ***")
    else:
        batch = OMEGABatchObject()
        if options.batch_file.__contains__('.csv'):
            batch.dataframe = pd.read_csv(options.batch_file, index_col=0)
        else:
            batch.dataframe = pd.read_excel(options.batch_file, index_col=0, sheet_name="Sessions")
        batch.dataframe.replace(to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False}, inplace=True)
        batch.dataframe.drop('Type', axis=1, inplace=True, errors='ignore') # drop Type column, no error if it's not there
        batch.expand_dataframe(verbose=options.verbose)
        batch.force_numeric_params()
        batch.get_batch_settings()
        batch.add_sessions(verbose=options.verbose)

        import copy
        expanded_batch = copy.deepcopy(batch)
        expanded_batch.name = os.path.splitext(os.path.basename(options.batch_file))[0] + '_expanded' + os.path.splitext(options.batch_file)[1]

        #remote_batchfile = batch.name + '.csv'
        #batch.dataframe.to_csv(remote_batchfile)
        #exit(0)

        if options.bundle:
            batch.dataframe.loc['Batch Name'][0] = batch.name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_") + batch.name

        # validate session files
        validate_folder(options.bundle_path_root)
        options.batch_path = validate_folder(options.bundle_path_root, batch_name=batch.name)

        if options.validate_batch:
            # validate shared (batch) files
            validate_file(options.batch_file)
            validate_folder(batch.dll_path) # do I need this?

            import clr
            sys.path.insert(0, os.getcwd())
            clr.AddReference('System.IO')
            for dll in batch.dll_list:
                clr.AddReference(dll)

            import System.IO
            import Volpe.Cafe as volpecafe

            for s in range(0, batch.num_sessions()):
                session = batch.sessions[s]
                print("\nValidating Session %d ('%s') Files..." % (s, session.name))
                validate_file(session.read_parameter('Market Data File'))
                validate_file(session.read_parameter('Parameters File'))
                validate_file(session.read_parameter('Technologies File'))
                validate_file(session.read_parameter('Scenarios File'))
                validate_file(session.read_parameter('FC1 Improvements File'))
                validate_file(session.read_parameter('FC2 Improvements File'))
                validate_file(session.read_parameter('FE1 Simulated File'))
                validate_file(session.read_parameter('FE2 Simulated File'))
                validate_file(session.read_parameter('Battery Costs File'))
                print('Validating Session %d Parameters...' % s)
                session.init(validate_only=True)

        print("\n*** validation complete ***")

        # copy files to network_batch_path
        if options.bundle:
            print('Bundling Source File...')
            # copy this file to batch folder
            relocate_file(options.batch_path, __file__)

            # write a copy of the expanded, validated batch to the source batch_file directory:
            if options.batch_file.__contains__('.csv'):
                expanded_batch.dataframe.to_csv(os.path.dirname(options.batch_file) + '\\' + expanded_batch.name)
            else:
                expanded_batch.dataframe.to_excel(os.path.dirname(options.batch_file) + '\\' + expanded_batch.name, "Sessions")

            print('Bundling dlls...')
            batch.dataframe.loc['DLL Path'][0] = options.batch_path
            # copy dlls to batch folder
            for dll in batch.dll_list:
                relocate_file(options.batch_path, dll)

            # copy session inputs to session folder(s) for active session(s)
            for s in range(0, batch.num_sessions()):
                if batch.sessions[s].enabled:
                    print('Bundling Session %d Files...' % s)
                    session = batch.sessions[s]
                    options.session_path = validate_folder(options.bundle_path_root, batch_name=batch.name, session_name=session.name)
                    batch.dataframe.loc['Session Output Path'][session.num]     = options.session_path + os.sep + 'output'
                    batch.dataframe.loc['Market Data File'][session.num]        = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('Market Data File'))
                    batch.dataframe.loc['Parameters File'][session.num]         = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('Parameters File'))
                    batch.dataframe.loc['Technologies File'][session.num]       = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('Technologies File'))
                    batch.dataframe.loc['Scenarios File'][session.num]          = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('Scenarios File'))
                    batch.dataframe.loc['FC1 Improvements File'][session.num]   = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('FC1 Improvements File'))
                    batch.dataframe.loc['FC2 Improvements File'][session.num]   = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('FC2 Improvements File'))
                    batch.dataframe.loc['FE1 Simulated File'][session.num]      = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('FE1 Simulated File'))
                    batch.dataframe.loc['FE2 Simulated File'][session.num]      = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('FE2 Simulated File'))
                    batch.dataframe.loc['Battery Costs File'][session.num]      = options.session_path + os.sep + relocate_file(options.session_path, session.read_parameter('Battery Costs File'))

        import time
        time.sleep(10) # wait for files to fully transfer...

        os.chdir(options.batch_path)

        remote_batchfile = batch.name + '.csv'
        batch.dataframe.to_csv(remote_batchfile)

        # print("Remote Batchfile = " +  remote_batchfile)
        # print("Bundle batch path root = " + options.bundle_path_root)
        # print("Batch path = " + options.batch_path)
        print("Batch name = " + batch.name)

        if options.session_num is None:
            session_list = range(0, batch.num_sessions())
        else:
            session_list = [options.session_num]

        if not options.no_sim:
            if options.dispy: # run remote job on cluster
                retry_count = dict()    # track retry attempts for terminated or abandoned jobs

                dispycluster = DispyCluster(options.scheduler)
                dispycluster.find_nodes()
                dispycluster.submit_sessions(batch.name, options.bundle_path_root, options.batch_path + batch.name, session_list)
                print("*** batch complete ***")
            else: # run from here
                batch = OMEGABatchObject()
                batch.dataframe = pd.read_csv(remote_batchfile, index_col=0)
                batch.dataframe.replace(to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False},
                                        inplace=True)
                batch.dataframe.drop('Type', axis=1, inplace=True, errors='ignore') # drop Type column, no error if it's not there
                batch.get_batch_settings()
                batch.add_sessions(verbose=False)

                # copy dlls to local folder to avoid clr.AddReference fail
                if options.session_num is None:
                    suffix = ''
                else:
                    suffix = '_' + batch.sessions[options.session_num].name

                dllpath = "C:\\Users\\Public\\temp"
                validate_folder(dllpath)
                if not batch.name == '':
                    dllpath = dllpath + "\\%s" % (batch.name + suffix)
                validate_folder(dllpath)
                batch.dll_path = dllpath
                for dll in batch.dll_list:
                    relocate_file(batch.dll_path, dll)

                import clr
                sys.path.insert(0, os.getcwd())
                clr.AddReference('System.IO')
                for dll in batch.dll_list:
                    clr.AddReference(batch.dll_path + os.sep + get_filenameext(dll))

                import System.IO
                import Volpe.Cafe as volpecafe

                # process sessions:
                for s_index in session_list:
                    print("Processing Session %d:" % s_index, end='')

                    if not batch.sessions[s_index].enabled:
                        print("Skipping Disabled Session '%s'" % batch.sessions[s_index].name)
                        print('')
                    else:
                        batch.sessions[s_index].run()

                # try to get rid of temporary dll directory
                shutil.rmtree(dllpath, ignore_errors=True)

    sys.exit(0)
