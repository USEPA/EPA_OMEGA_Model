"""
credits.py
==========

"""

credit_lifetime_years = 4

class Credit:
    def __init__(self, year_earned=None, value_Mg=None):
        self.year_earned = year_earned
        self.value_Mg = value_Mg
        self.year_consumed = None

    def __repr__(self):
        s = '\n<credit.Credit object at %#x>' % id(self)
        for k in self.__dict__:
            s = s + ', '
            s = s + k + ' = ' + str(self.__dict__[k])
        return s

    def age(self, calendar_year):
        return calendar_year - self.year_earned

    def earn(self, calendar_year):
        self.year_earned = calendar_year

    def consume(self, calendar_year):
        self.year_consumed = calendar_year


class CreditBank:
    def __init__(self):
        """
        """
        self.__credits = Credit()   # so pyreverse can tell what kind of dict
        self.__credits = dict()

    def credits_total_Mg(self, calendar_year):
        total = 0
        for credit_year, credit in self.__credits.items():
            if credit_year >= calendar_year - credit_lifetime_years:
                total = total + credit.value_Mg
        return total

    def credits_expiring(self, calendar_year):
        for credit_year, credit in self.__credits.items():
            if credit_year == calendar_year - credit_lifetime_years:
                return credit
        return 0

    @property
    def credits_valid(self):
        valid_credits = []
        for credit_year in self.__credits:
            if credit_year >= calendar_year - credit_lifetime_years:
                valid_credits.append(self.__credits[credit_year])
        return valid_credits

    def add_history(self, calendar_year, credits_Mg):
        """
        Add credits_Mg to credit history for the given calendar_year

        :param calendar_year:
        :param credits_Mg:
        :return:
        """
        self.__credits[calendar_year] = Credit(calendar_year, credits_Mg)


if __name__ == '__main__':
    print('credits.py')
    calendar_year = 2019

    cb = CreditBank()
    cb.add_history(999, 999)
    cb.add_history(calendar_year - credit_lifetime_years, 4242)
    cb.add_history(calendar_year, -1000)
    print('total credits = %d' % cb.credits_total_Mg(calendar_year))
    print('credits expiring = %s' % cb.credits_expiring(calendar_year))
    vc = cb.credits_valid
    print(vc)