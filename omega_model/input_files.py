"""
documentation

"""
from omega_model import *


class InputFiles(OMEGABase):

    _data = dict() # this dict is updated when class objects are instantiated.

    @staticmethod
    def init_input_files():
        InputFiles._data = dict()
        return InputFiles._data

    @staticmethod
    def update_input_files_dict(template_name, description):
        """

        Parameters:
            template_name (str): target template name
            description (str): target template description (optional)

        Returns:
            Updates InputFiles._data with template name and description information.

        """
        InputFiles._data[template_name] = {'template': template_name,
                                           'description': description,
                                           }
