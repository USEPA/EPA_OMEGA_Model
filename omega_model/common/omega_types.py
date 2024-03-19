"""
**Custom general datatypes for use in OMEGA.**

----

**CODE**

"""
import copy
import pandas as pd

print('importing %s' % __file__)

import re


def make_valid_python_identifier(s):
    """
    Creates a valid python identifier from a source string (by removing invalid characters).

    Args:
        s (str): the source string to make a valid identifier from

    Returns:
        A valid python identifier based on the source string

    """
    s = s.replace(' ', '_')  # personal preference, spaces as underscores instead of deletes

    # Remove invalid characters
    s = re.sub('[^0-9a-zA-Z_]', '', s)

    # Remove leading characters until we find a letter or underscore
    s = re.sub('^[^a-zA-Z_]+', '', s)

    return s


class OMEGABase:
    """
    Defines a base class with common behaviors for all OMEGA objects.

    Example of representation strings and printing via ``__repr__`` and ``__str__`` methods:

    ::

        class ExampleOMEGAClass(OMEGABase):
        def __init__(self):
            self.first_attribute = 0
            self.second_attribute = 1

        >>>example_object = ExampleOMEGAClass()
        >>>example_object
        <OMEGA2 ExampleOMEGAClass object at 0x7f91d03975e0>

        >>>print(example_object)
        <OMEGA2 ExampleOMEGAClass object at 0x7f91d03975e0>
        first_attribute = 0
        second_attribute = 1

    """
    @classmethod
    def get_class_attributes(cls, attribute_list):
        """
        Get a list of class attributes.

        Args:
            cls (class): the class to get attributes from
            attribute_list ([strs]): a list of attribute names

        Returns:
            A list containing the values of the requested attributes

        .. automethod:: __repr__
        .. automethod:: __str__

        """
        return [cls.__dict__[attr] for attr in attribute_list]

    def get_object_attributes(self, attribute_list):
        """
        Get a list of object attributes.

        Args:
            self (object): the object to get attributes from
            attribute_list ([strs]): a list of attribute names

        Returns:
            A list containing the values of the requested attributes

        """
        return [self.__getattribute__(attr) for attr in attribute_list]

    def __repr__(self):
        """
        Generate a representation string for the object.

        Returns:
            A string representation of the object.

        """
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        """
        Generate a string of object attributes, so objects have a default print behavior.

        Returns:
            A string with a listing of object attributes and values.

        """
        s = self.__repr__() + '\n'
        attributes = sorted(list(self.__dict__.keys()))
        for k in attributes:
            s = s + k + ' = ' + str(self.__dict__[k]).replace('\n', ' ') + '\n'
        return s

    def to_dataframe(self, types=None):
        """
        Generate a dataframe of object attributes as numeric values or strings

        Returns:
            A dataframe representation of the object

        """
        attributes = sorted(list(self.__dict__.keys()))

        df = pd.DataFrame(columns=attributes)
        df['__repr__'] = [self.__repr__()]

        for k in attributes:
            if types is None or type(self.__dict__[k]) in types:
                s = str(self.__dict__[k]).replace('\n', ' ')
                if s.isnumeric():
                    df[k] = self.__dict__[k]
                else:
                    df[k] = s

        return df

    def to_csv(self, filename, transpose=True, *args, **kwargs):
        """
        Save object as comma-separated values file.

        Args:
            filename (str): name of file
            transpose (bool): tranpose dataframe if ``True``
            *args: optional positional arguments to pandas DataFrame.to_csv()
            **kwargs: optional keyword arguments to pandas DataFrame.to_csv()

        """
        df = self.to_dataframe()

        if transpose:
            df = df.transpose()

        df.to_csv(filename, *args, columns=sorted(df.columns), **kwargs)

    def to_dict(self, types=None):
        """
        Generate a dict of object attributes

        Returns:
            A dict representation of the object

        """
        if types:
            d = dict()
            for k in sorted(list(self.__dict__.keys())):
                if type(self.__dict__[k]) in types:
                    d[k] = self.__dict__[k]
        else:
            d = self.__dict__.copy()

        return d

    def to_namedtuple(self):
        """
        Generate a named tuple of object attributes

        Returns:
            A namedtuple representation of the ojbect

        """
        from collections import namedtuple

        attributes = [a for a in sorted(list(self.__dict__.keys())) if not a.startswith('_')]

        ObjNamedtuple = namedtuple('%s_namedtuple' % type(self).__name__, attributes)

        nt_dict = dict()
        for k in attributes:
            nt_dict[k] = self.__dict__[k]

        return ObjNamedtuple(**nt_dict)

    def copy(self):
        """
        Copy object

        Returns:
            Copy of the current object

        """
        return copy.copy(self)

    def deepcopy(self):
        """
        Deep copy object

        Returns:
            Deep copy of the current object

        """
        return copy.deepcopy(self)


class OMEGAEnum(OMEGABase):
    """
    Simple enumerated value class, which acts like a list of strings, has named attributes which contain the
    attribute name as a string, also acts like a dictionary.

    Example

    ::

        # define an OMEGAEnum
        reg_classes = OMEGAEnum(['car', 'truck'])

        # named attribute behavior
        >>>reg_classes.car
        'car'

        # dict-like behavior
        >>>reg_classes['car']
        'car'

        >>>reg_classes.keys()
        dict_keys(['car', 'truck'])

        >>>reg_classes.values()
        dict_values(['car', 'truck'])

        >>>reg_classes.items()
        dict_items([('car', 'car'), ('truck', 'truck')])

        # list-like behavior
        >>>[rc for rc in reg_classes]
        ['car', 'truck']

    """
    def __init__(self, enum_list):
        """
        Create OMEGAEnum object from list of values.

        Args:
            enum_list (list): list of enumeration values

        """
        self.__value_list = enum_list
        self.__identifier_list = [make_valid_python_identifier(i) for i in self.__value_list]
        self.__dict = dict()
        for i, j in zip(self.__identifier_list, self.__value_list):
            exec("self.%s='%s'" % (i, j))
            self.__dict[i] = j

    def __iter__(self):
        """
        Implements iterable behavior so class acts like list.

        Returns:
            Iterator

        """
        return self.__value_list.__iter__()

    def __getitem__(self, item):
        """
        Implements dict-like behavior, as in dict['item'], so class acts like a dict.

        Args:
            item (hashable): key value

        Returns:
            value associated with item

        """
        return self.__dict.__getitem__(item)

    def values(self):
        """
        Implement values() function, like a dict.

        Returns:
            A list of values

        """
        return self.__dict.values()

    def keys(self):
        """
        Implement keys() function, like a dict.

        Returns:
            A list of keys

        """
        return self.__dict.keys()

    def items(self):
        """
        Implement items() function, like a dict.

        Returns:
            A list of key-value pairs (2-tuples)

        """
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

        for k, v in test_enum.items():
            print(k, v)

        print(test_enum['foo'])
        print(test_enum['space_force'])
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
