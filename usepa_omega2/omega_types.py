def make_valid_python_identifier(s):
    import re

    s = s.replace(' ', '_')  # personal preference, spaces as underscores instead of deletes

    # Remove invalid characters
    s = re.sub('[^0-9a-zA-Z_]', '', s)

    # Remove leading characters until we find a letter or underscore
    s = re.sub('^[^a-zA-Z_]+', '', s)

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
            print(i, j)
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
