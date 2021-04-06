"""
Attempt at Averaging, Banking and (not) Trading emissions credits
"""

print('importing %s' % __file__)

from usepa_omega2 import *

input_template_name = 'ghg_credit_history'

credit_max_life_years = 5
debit_max_life_years = 3

input_template_version = 0.1
input_template_columns = {'calendar_year', 'model_year', 'manufacturer', 'balance_Mg'}


class GHG_credit_bank(OMEGABase):

    def __init__(self, filename, manufacturer_name, verbose=False):
        # call init after validating ghg_credits template
        if verbose:
            omega_log.logwrite('\nInitializing credit bank from %s...' % filename)

        # read in the data portion of the input file
        self.credit_bank = pd.read_csv(filename, skiprows=1)

        self.credit_bank[self.credit_bank['manufacturer'] == manufacturer_name]
        self.credit_bank = self.credit_bank.rename({'balance_Mg':'beginning_balance_Mg'}, axis='columns')
        self.credit_bank['ending_balance_Mg'] = self.credit_bank['beginning_balance_Mg']
        self.credit_bank['age'] = self.credit_bank['calendar_year'] - self.credit_bank['model_year']

        self.transaction_log = pd.DataFrame()

    @staticmethod
    def validate_ghg_credits_template(filename, verbose):
        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            template_errors = validate_template_columns(filename, input_template_columns, input_template_columns,
                                                        verbose=verbose)

        return template_errors

    @staticmethod
    def create_credit():
        new_credit = dict()
        new_credit['calendar_year'] = None
        new_credit['model_year'] = None
        new_credit['manufacturer'] = None
        new_credit['beginning_balance_Mg'] = None
        new_credit['ending_balance_Mg'] = None
        new_credit['age'] = None
        new_credit = pd.DataFrame(new_credit, columns=new_credit.keys(), index=[0])
        return new_credit

    @staticmethod
    def create_credit_transaction(credit):
        new_credit_transaction = dict()
        new_credit_transaction['calendar_year'] = credit['calendar_year']
        new_credit_transaction['model_year'] = credit['model_year']
        new_credit_transaction['manufacturer'] = credit['manufacturer']
        new_credit_transaction['credit_value_Mg'] = None
        new_credit_transaction['credit_destination'] = None
        new_credit_transaction = pd.DataFrame(new_credit_transaction, columns=new_credit_transaction.keys(), index=[0])
        return new_credit_transaction

    def get_expiring_credits_Mg(self, calendar_year):
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
                        t = GHG_credit_bank.create_credit_transaction(credit)
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
                    t = GHG_credit_bank.create_credit_transaction(debit)
                    t['credit_value_Mg'] = debit['ending_balance_Mg']
                    t['credit_destination'] = 'PAST_DUE'
                    self.transaction_log = pd.DataFrame.append(self.transaction_log, t)

        self.credit_bank = pd.DataFrame.append(self.credit_bank, last_years_credits)

    def handle_credit(self, calendar_year, manufacturer, beginning_balance_Mg):
        new_credit = GHG_credit_bank.create_credit()
        new_credit['calendar_year'] = calendar_year
        new_credit['model_year'] = calendar_year
        new_credit['manufacturer'] = manufacturer
        new_credit['beginning_balance_Mg'] = beginning_balance_Mg
        new_credit['ending_balance_Mg'] = beginning_balance_Mg
        new_credit['age'] = 0
        self.credit_bank = pd.DataFrame.append(self.credit_bank, new_credit, ignore_index=True)
        new_credit = self.credit_bank.iloc[-1].copy()  # grab credit as a series

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
        transaction_amount = min(abs(debit['ending_balance_Mg']), credit['ending_balance_Mg'])
        t = GHG_credit_bank.create_credit_transaction(credit)
        t['credit_value_Mg'] = transaction_amount
        t['credit_destination'] = debit['model_year']
        credit['ending_balance_Mg'] -= transaction_amount
        debit['ending_balance_Mg'] += transaction_amount
        self.transaction_log = pd.DataFrame.append(self.transaction_log, t)
        this_years_credits.loc[credit.name] = credit  # update credit
        this_years_credits.loc[debit.name] = debit  # update debit


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        credit_bank = GHG_credit_bank('test_inputs/ghg_debits.csv', 'USA Motors')
        credit_bank.update_credit_age(2020)
        credit_bank.handle_credit(2020, 'USA Motors', 0.55)
        credit_bank.credit_bank.to_csv('../out/__dump/debit_bank.csv', index=False)
        credit_bank.transaction_log.to_csv('../out/__dump/debit_bank_transactions.csv', index=False)

        credit_bank = GHG_credit_bank('test_inputs/ghg_credits.csv', 'USA Motors')
        import random
        for year in range(2020,2030):
            print(year)
            credit_bank.update_credit_age(year)
            credit_bank.handle_credit(year, 'USA Motors', random.gauss(0, 1))
        credit_bank.credit_bank.to_csv('../out/__dump/credit_bank.csv', index=False)
        credit_bank.transaction_log.to_csv('../out/__dump/credit_bank_transactions.csv', index=False)
        # else:
        #     for l in init_fail:
        #         print(l)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
