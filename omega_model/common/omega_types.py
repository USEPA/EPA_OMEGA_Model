"""


----

**CODE**

"""
print('importing %s' % __file__)

def make_valid_python_identifier(s):
    import re

    s = s.replace(' ', '_')  # personal preference, spaces as underscores instead of deletes

    # Remove invalid characters
    s = re.sub('[^0-9a-zA-Z_]', '', s)

    # Remove leading characters until we find a letter or underscore
    s = re.sub('^[^a-zA-Z_]+', '', s)

    return s


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


class OMEGAEnum:
    """
    Simple enumerated value class, which acts like a list of strings and also has named properties which contain the
    property name as a string, also acts like a dictionary, just for good measure
    """
    def __init__(self, enum_list):
        self.__value_list = enum_list
        self.__identifier_list = [make_valid_python_identifier(i) for i in self.__value_list]
        self.__dict = dict()
        for i, j in zip(self.__identifier_list, self.__value_list):
            exec("self.%s='%s'" % (i, j))
            self.__dict[i]=j

    def __iter__(self):
        return self.__value_list.__iter__()

    def __getitem__(self, item):
        return self.__dict.__getitem__(item)

    def values(self):
        return self.__dict.values()

    def keys(self):
        return self.__dict.keys()

    def items(self):
        return self.__dict.items()


if __name__ == "__main__":
    import os, traceback

    try:
        test_enum = OMEGAEnum(['foo', 'bar', 'space force!'])

        for i in test_enum:
            print(i)

        print([i for i in test_enum])

        print(test_enum.values())
        print(test_enum.keys())

        for k,v in test_enum.items():
            print(k, v)

        print(test_enum['foo'])
        print(test_enum['space_force'])
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
