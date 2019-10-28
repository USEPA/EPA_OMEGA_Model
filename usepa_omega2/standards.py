"""
standards.py
============

calculate emissions standards based on vehicle attributes or other program elements

"""

lifetime_vmt_miles = {'Car': 195264, 'Truck': 225865}

class standards:
    def __init__(self):
        name = 'footprint-based car/truck standards'

    def calc(self, calendar_year, elements_dict):
        """
        calculate emissions standards in Mg based on factors in the elements_dict such as footprint, vehicle class, etc

        :param calendar_year: calendar year to calculate standards for
        :param elements_dict: dictionary of desired attributes or program elements
        :return:
        """
