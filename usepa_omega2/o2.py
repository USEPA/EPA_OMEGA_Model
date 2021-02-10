"""
o2.py
=====
"""


print('importing %s' % __file__)


class OMEGABase:
    # define common behaviors for all OMEGA objects
    @classmethod
    def get_class_attributes(cls, attribute_list):
        """

        Args:
            cls: the class to get attributes from
            attribute_list: a list of attribute names

        Returns: a list containing the values of the requested attributes

        """
        return [cls.__dict__[attr] for attr in attribute_list]

    def get_object_attributes(self, attribute_list):
        """

        Args:
            self: the object to get attributes from
            attribute_list: a list of attribute names

        Returns: a list containing the values of the requested attributes

        """
        return [self.__getattribute__(attr) for attr in attribute_list]

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = self.__repr__() + '\n'
        attributes = list(self.__dict__.keys())
        attributes.sort()
        for k in attributes:
            s = s + k  + ' = ' + str(self.__dict__[k]).replace('\n', ' ') + '\n'
        return s


# globals to be populated at runtime:
options = None
engine = None
session = None
