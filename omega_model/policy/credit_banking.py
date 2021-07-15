"""

**Routines to load initial GHG credits (in CO2e Mg), provide access to credit banking data, and handle credit
transactions, along the lines of Averaging, Bank and Trading (ABT)**

Not all features of ABT are implemented (notably, explicit between-manufacturer Trading).  Credits can be earned,
used to pay debits (model year compliance deficits) and/or may expire unused.

See Also:
    The ``manufacturers`` module and ``postproc_session.plot_manufacturer_compliance()`` for credit plotting routines.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents GHG credits that are available to manufacturers in the compliance analysis years.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,ghg_credit_history,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,model_year,manufacturer_id,balance_Mg
        2019,2016,USA Motors,151139573

Data Column Name and Description

:calendar_year:
    Calendar year of the data, e.g. the analysis base year

:model_year:
    The model year of the available credits, determines remaining credit life

:manufacturer_id:
    Identifies the credit owner, consistent with the data loaded by the ``manufacturers`` module

:balance_Mg:
    Model year credit remaining balance in the calendar year (CO2e Mg)

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

credit_max_life_years = 5  #: credit max life, in years, a.k.a. credit carry-foward
debit_max_life_years = 3  #: debit max life, in years, a.k.a. credit carry-back

_input_template_name = 'ghg_credit_history'
_input_template_version = 0.2
_input_template_columns = {'calendar_year', 'model_year', 'manufacturer_id', 'balance_Mg'}


class CreditInfo(OMEGABase):
    """
    **Stores GHG credit info (i.e. remaining balance, remaining years)**

    Used by GHG_credit_bank.get_credit_info() to return a list of non-expired credit and debit data

    """
    def __init__(self, remaining_balance_Mg, remaining_years):
        """
        Create GHG_credit_info object

        Args:
            remaining_balance_Mg (numeric): remaining credit balance, CO2e Mg
            remaining_years (numeric): remaining years of life before expiration
        """
        self.remaining_balance_Mg = remaining_balance_Mg
        self.remaining_years = remaining_years


class CreditBank(OMEGABase):
    """
    **Provides objects and methods to handle credit transactions and provide credit bank information.**

    Each manufacturer will use its own unique credit bank object.

    """
    def __init__(self, filename, manufacturer_id, verbose=False):
        """

        Initialize credit bank data from input file, call after validating ghg_credits template.

        Args:
            filename (str): name of input file containing pre-existing credit info
            manufacturer_id (str): name of manufacturer, e.g. 'USA Motors'
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """

        if verbose:
            omega_log.logwrite('\nInitializing credit bank from %s...' % filename)

        # read in the data portion of the input file
        self.credit_bank = pd.read_csv(filename, skiprows=1)

        self.credit_bank[self.credit_bank['manufacturer_id'] == manufacturer_id]
        self.credit_bank = self.credit_bank.rename({'balance_Mg': 'beginning_balance_Mg'}, axis='columns')
        self.credit_bank['ending_balance_Mg'] = self.credit_bank['beginning_balance_Mg']
        self.credit_bank['age'] = self.credit_bank['calendar_year'] - self.credit_bank['model_year']

        self.transaction_log = pd.DataFrame()

    @staticmethod
    def validate_ghg_credits_template(filename, verbose):
        """
        Validate GHG credit input file template.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template errors, or empty list on success.

        """
        template_errors = validate_template_version_info(filename, _input_template_name, _input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            template_errors = validate_template_columns(filename, _input_template_columns, _input_template_columns,
                                                        verbose=verbose)

        return template_errors

    @staticmethod
    def create_credit(calendar_year, manufacturer_id, beginning_balance_Mg):
        """
        Create a new GHG credit data structure.

        Args:
            calendar_year (numeric): calendar year of credit creation
            manufacturer_id (str): manufacturer name, e.g. 'USA Motors'
            beginning_balance_Mg (numeric): starting balance of credit in CO2e Mg

        Returns:
            DataFrame of new (age zero) credit info

        """
        new_credit = dict()
        new_credit['calendar_year'] = calendar_year
        new_credit['model_year'] = calendar_year
        new_credit['manufacturer'] = manufacturer_id
        new_credit['beginning_balance_Mg'] = beginning_balance_Mg
        new_credit['ending_balance_Mg'] = beginning_balance_Mg
        new_credit['age'] = 0
        new_credit = pd.DataFrame(new_credit, columns=new_credit.keys(), index=[0])
        return new_credit

    @staticmethod
    def create_credit_transaction(credit):
        """
        Create an empty (no value, no destination) credit transaction.

        Args:
            credit (Series): see GHG_credit_bank.create_credit()

        Returns:
            DataFrame of new, empty, credit transaction

        """
        new_credit_transaction = dict()
        new_credit_transaction['calendar_year'] = credit['calendar_year']
        new_credit_transaction['model_year'] = credit['model_year']
        new_credit_transaction['manufacturer'] = credit['manufacturer']
        new_credit_transaction['credit_value_Mg'] = None
        new_credit_transaction['credit_destination'] = None
        new_credit_transaction = pd.DataFrame(new_credit_transaction, columns=new_credit_transaction.keys(), index=[0])
        return new_credit_transaction

    def get_credit_info(self, calendar_year):
        """
        Get lists of valid (non-expired) credits and debits for the given year.

        Args:
            calendar_year (numeric): calendar year to query for credits and debits

        Returns:
            Tuple of lists of ``GHG_credit_info`` objects ([current_credits], [current_debits])

        """
        current_credits = []
        this_years_credits = self.credit_bank[self.credit_bank['calendar_year'] == calendar_year]

        # apply lifetime rules
        ghg_credits = this_years_credits[this_years_credits['ending_balance_Mg'] >= 0]
        if not ghg_credits.empty:
            for _, credit in ghg_credits.iterrows():
                if credit['age'] <= credit_max_life_years:
                    current_credits.append(
                        CreditInfo(credit['ending_balance_Mg'], credit_max_life_years - credit['age'] + 1))

        current_debits = []

        # apply lifetime rules
        ghg_debits = this_years_credits[this_years_credits['ending_balance_Mg'] < 0]
        if not ghg_debits.empty:
            for _, debit in ghg_debits.iterrows():
                if debit['age'] <= debit_max_life_years:
                    current_debits.append(
                        CreditInfo(debit['ending_balance_Mg'], debit_max_life_years - debit['age'] + 1))

        return current_credits, current_debits

    def get_expiring_credits_Mg(self, calendar_year):
        """
        Get value of expiring credits in CO2e Mg for the given year.

        Args:
            calendar_year (numeric): calendar year to get expiring credits from

        Returns:
            Value of expiring credits in CO2e Mg

        """
        expiring_credits_Mg = 0
        this_years_credits = self.credit_bank[self.credit_bank['calendar_year'] == calendar_year]

        # apply lifetime rules
        ghg_credits = this_years_credits[this_years_credits['ending_balance_Mg'] >= 0]
        if not ghg_credits.empty:
            for _, credit in ghg_credits.iterrows():
                if credit['age'] == credit_max_life_years:
                    expiring_credits_Mg = credit['ending_balance_Mg']

        return expiring_credits_Mg

    def get_expiring_debits_Mg(self, calendar_year):
        """
        Get value of expiring debits in CO2e Mg for the given year.

        Args:
            calendar_year (numeric): calendar year to get expiring debits from

        Returns:
            Value of expiring debits in CO2e Mg

        """

        expiring_debits_Mg = 0
        this_years_credits = self.credit_bank[self.credit_bank['calendar_year'] == calendar_year]

        # apply lifetime rules
        ghg_debits = this_years_credits[this_years_credits['ending_balance_Mg'] < 0]
        if not ghg_debits.empty:
            for _, debit in ghg_debits.iterrows():
                if debit['age'] >= debit_max_life_years:
                    expiring_debits_Mg += debit['ending_balance_Mg']

        return expiring_debits_Mg

    def update_credit_age(self, calendar_year):
        """
        Take each credit in the ``credit_bank`` and age it by one year then apply lifetime limits to drop
        expired credits and zero-value credits and debits.

        Credits and debits with zero balance are dropped silently after age zero.

        Expiration takes the form of entries in the ``transaction_log``.

            * Expiring credits with non-zero balances are marked as 'EXPIRATION' transactions and then dropped
            * Expiring debits with non-zero balances are marked as 'PAST_DUE' transactions and are not dropped

        Result is an updated ``credit_bank`` and an updated ``transaction_log``, as needed

        Args:
            calendar_year (numeric): calendar year to update credits in

        """

        # grab last years
        last_years_credits = self.credit_bank[self.credit_bank['calendar_year'] == calendar_year - 1].copy()

        # last_years_credits = last_years_credits.loc[last_years_credits['credit_transfer_action'] != 'EXPIRATION']
        last_years_credits['age'] = last_years_credits['age'] + 1
        last_years_credits['calendar_year'] = calendar_year
        last_years_credits['beginning_balance_Mg'] = last_years_credits['ending_balance_Mg']

        # apply lifetime rules
        ghg_credits = last_years_credits[last_years_credits['ending_balance_Mg'] >= 0]
        if not ghg_credits.empty:
            for idx, credit in ghg_credits.iterrows():
                # log the death of non-zero value credits
                if ((credit['age'] > 0) and (credit['ending_balance_Mg'] == 0)) or \
                        credit['age'] > credit_max_life_years:
                    if credit['ending_balance_Mg'] > 0:
                        t = self.create_credit_transaction(credit)
                        t['credit_value_Mg'] = credit['ending_balance_Mg']
                        t['credit_destination'] = 'EXPIRATION'
                        self.transaction_log = pd.DataFrame.append(self.transaction_log, t)
                    last_years_credits = last_years_credits.drop(idx)

        ggh_debits = last_years_credits[last_years_credits['beginning_balance_Mg'] < 0]
        if not ggh_debits.empty:
            for idx, debit in ggh_debits.iterrows():
                if (debit['age'] > 0) and (debit['ending_balance_Mg'] == 0):
                    # silently drop zero-value debits after age 0
                    last_years_credits = last_years_credits.drop(idx)
                elif debit['age'] > debit_max_life_years:
                    # mark past due debits
                    t = self.create_credit_transaction(debit)
                    t['credit_value_Mg'] = debit['ending_balance_Mg']
                    t['credit_destination'] = 'PAST_DUE'
                    self.transaction_log = pd.DataFrame.append(self.transaction_log, t)

        self.credit_bank = pd.DataFrame.append(self.credit_bank, last_years_credits)

    def handle_credit(self, calendar_year, manufacturer_id, beginning_balance_Mg):
        """
        Handle mandatory credit (and default debit) behavior.

        If the manufacturer's compliance state in the given year is over-compliance, ``beginning_balance_Mg`` will
        be positive (> 0).  In this case past under-compliance (debits) **MUST** be paid before banking any excess.
        Debits are paid starting with the oldest first and working forwards until they are all paid or the full value
        of the current credit has been paid out, whichever comes first.

        If the manufacturer's compliance state in the given year is under-compliance, ``beginning_balance_Mg`` will
        be negative (< 0).  In this case, the payment of debits is up to the programmer, there are no mandatory
        debit payment requirements.  As implemented, fresh debits are immediately paid by any available banked credits,
        so a debit will only be carried if it can't be paid in full at the time of its creation.

        Result is an updated ``credit_bank`` and an updated ``transaction_log``, as needed (via the ``pay_debit()``
        method).

        Note:

            It's possible to conceive of many different credit/debit strategies (once mandatory credit behavior has been
            handled).  In the case of OMEGA, strategic over- and under-compliance will eventually be handled by the
            year-over-year compliance tree which will allow a search of various "earn and burn" credit paths.  As such,
            it's important to leave the implentation of such schemes out of this method and the default handling here
            allows for that.

        Args:
            calendar_year (numeric): calendar year of credit creation
            manufacturer_id (str): manufacturer name, e.g. 'USA Motors'
            beginning_balance_Mg (numeric): starting balance of credit (or debit) in CO2e Mg

        """
        new_credit = self.create_credit(calendar_year, manufacturer_id, beginning_balance_Mg)
        self.credit_bank = pd.DataFrame.append(self.credit_bank, new_credit, ignore_index=True)
        new_credit = self.credit_bank.iloc[-1].copy()  # grab credit as a Series

        this_years_credits = self.credit_bank[self.credit_bank['calendar_year'] == calendar_year].copy()

        # if credit is positive, see if there any debts to be paid
        if new_credit['ending_balance_Mg'] > 0:
            debits = this_years_credits[this_years_credits['ending_balance_Mg'] < 0]
            if not debits.empty:
                for _, debit in debits.iterrows():
                    if debit['ending_balance_Mg'] < 0:
                        if new_credit['ending_balance_Mg'] > 0:
                            self.pay_debit(new_credit, debit, this_years_credits)

        # if credit is negative, see if there are any credits that can pay it
        elif new_credit['ending_balance_Mg'] < 0:
            debit = new_credit
            credits = this_years_credits[this_years_credits['ending_balance_Mg'] >= 0]
            if not credits.empty:
                for _, credit in credits.iterrows():
                    if debit['ending_balance_Mg'] < 0:
                        if credit['ending_balance_Mg'] > 0:
                            self.pay_debit(credit, debit, this_years_credits)

        self.credit_bank[self.credit_bank['calendar_year'] == calendar_year] = this_years_credits  # update bank

    def pay_debit(self, credit, debit, this_years_credits):
        """
        Pay a debit with a credit, create a transaction in the ``transaction_log`` and update manufacter model year
        compliance status (in CO2e Mg).

        Other than expiration, paying debits is the only way credits can be consumed.

        Result is an updated ``transaction_log`` and ``ManufacturerAnnualData`` for the model years involved in the
        transaction.

        See Also:

            ``manufacturer_annual_data.ManufacturerAnnualData.update_model_year_cert_co2e_Mg()``

        Args:
            credit (Series): source credit to pay from
            debit (Series): destination debit to pay
            this_years_credits (DataFrame): DataFrame containing the valid, non-expired credits and debits in the
                current year.

        """
        from producer.manufacturer_annual_data import ManufacturerAnnualData
        transaction_amount_Mg = min(abs(debit['ending_balance_Mg']), credit['ending_balance_Mg'])
        t = self.create_credit_transaction(credit)
        t['credit_value_Mg'] = transaction_amount_Mg
        t['credit_destination'] = debit['model_year']
        credit['ending_balance_Mg'] -= transaction_amount_Mg
        debit['ending_balance_Mg'] += transaction_amount_Mg
        self.transaction_log = pd.DataFrame.append(self.transaction_log, t)
        this_years_credits.loc[credit.name] = credit  # update credit
        this_years_credits.loc[debit.name] = debit  # update debit
        ManufacturerAnnualData.update_model_year_cert_co2e_Mg(debit['model_year'], debit['manufacturer'], -transaction_amount_Mg)
        ManufacturerAnnualData.update_model_year_cert_co2e_Mg(credit['model_year'], credit['manufacturer'], +transaction_amount_Mg)


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)
        # override reg_classes from __init__.py:
        importlib.import_module('omega_model').reg_classes = omega_globals.options.RegulatoryClasses.reg_classes

        from producer.manufacturers import Manufacturer
        from producer.manufacturer_annual_data import ManufacturerAnnualData
        from producer.vehicles import VehicleFinal
        from producer.vehicle_annual_data import VehicleAnnualData
        from consumer.market_classes import MarketClass

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=omega_globals.options.verbose)

        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
                                                          omega_globals.options.vehicle_onroad_calculations_file,
                                                          verbose=omega_globals.options.verbose)

        # credit_bank = CreditBank('demo_inputs/ghg_debits.csv', 'USA Motors')
        # credit_bank.update_credit_age(2020)
        # credit_bank.handle_credit(2020, 'USA Motors', 0.55)
        # credit_bank.credit_bank.to_csv('../out/__dump/debit_bank.csv', index=False)
        # credit_bank.transaction_log.to_csv('../out/__dump/debit_bank_transactions.csv', index=False)

        credit_bank = CreditBank(omega_globals.options.ghg_credits_file, 'USA Motors')

        import random

        for year in range(2020, 2030):
            print(year)
            credit_bank.update_credit_age(year)
            credit_bank.handle_credit(year, 'USA Motors', random.gauss(0, 1))

        import common.file_io as file_io

        # validate output folder
        file_io.validate_folder(omega_globals.options.database_dump_folder)

        credit_bank.credit_bank.to_csv(omega_globals.options.database_dump_folder + '/credit_bank.csv', index=False)
        credit_bank.transaction_log.to_csv(omega_globals.options.database_dump_folder + '/credit_bank_transactions.csv', index=False)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
