"""

**SQLite/SQLAlchemy Database Functionality.**

Routines to initialize the database, create a connection,
and other handle database utilities.

----

**CODE**

"""

print('importing %s' % __file__)

# import o2  # import global variables
from common import omega_globals, omega_log
import pandas as pd
from sqlalchemy import create_engine

# NOTE:
# INTEGERS get stored in sqlite as byte strings:i.e.:
# >>int.from_bytes(b'\xe4\x07\x00\x00\x00\x00\x00\x00', 'little') equals 2020, so we need to use Numeric if we want
# to be able to easily use them and see them in database dumps, so model_year is Numeric, not Integer
# The only place where Integer works as expected is for primary keys

# noinspection PyUnresolvedReferences
import sqlalchemy
# noinspection PyUnresolvedReferences
from sqlalchemy import MetaData, Table, Column, String, ForeignKey, Enum, Float, Integer, func, Boolean
from sqlalchemy.ext.declarative import declarative_base
# noinspection PyUnresolvedReferences
from sqlalchemy.orm import relationship, Session

from decimal import Decimal
import sqlalchemy.types as types


class _StringNumeric(types.TypeDecorator):
    """
    Decorator Class to store "numeric" values (e.g. integers) as strings in the database.

    """
    impl = types.String
    cache_ok = True  # for SQLAlchemy >= 1.4 request caching

    def load_dialect_impl(self, dialect):
        """
        Get the SQL dialect implementation descriptor

        Args:
            dialect (SQLAlchemy Dialect):

        Returns:
            The implementation type descriptor of

        """
        return dialect.type_descriptor(types.VARCHAR(100))

    def process_bind_param(self, value, dialect):
        """
        Generate string representation of ``value``.

        Args:
            value (numeric): the numeric value to be converted to a string
            dialect: unused

        Returns:
            The string representation of ``value``.

        """
        return str(value)

    def process_result_value(self, value, dialect):
        """
        Returns the ``Decimal`` value of ``value``.

        Args:
            value (str): the string to convert to ``Decimal``
            dialect: unused

        Returns:
            The ``Decimal`` value of ``value``.

        """
        return Decimal(value)


# Use Numeric a.k.a StringNumeric for integer values stored as strings (e.g. model_year)
Numeric = _StringNumeric

SQABase = declarative_base(name='DeclarativeMeta')  #: base class for SQLAlchemy-based classes


def init_omega_db(verbose):
    """
    Create SQLite database engine (in memory) and associated session, set omega_globals variables (engine, session).
    Set up any necessary database options.

    Args:
        verbose (bool): if True then echo SQL commands to the console

    """
    omega_globals.engine = create_engine('sqlite:///:memory:', echo=verbose)
    omega_globals.session = Session(bind=omega_globals.engine)
    # !!!SUPER IMPORTANT, OTHERWISE FOREIGN KEYS ARE NOT CHECKED BY SQLITE DEFAULT!!!
    omega_globals.session.execute('pragma foreign_keys=on')


def sql_unpack_result(query_result_tuples, index=0):
    """
    Unpack a database query result (list of tuples).

    Args:
        query_result_tuples: List of tuples to unpack
        index (int): tuple index to build result list from

    Returns:
        List of query results by tuple index, e.g. ``[r[index] for r in query_result_tuples]``

    """
    return [r[index] for r in query_result_tuples]


def _sql_format_list_str(list_in):
    """
    Reformat a list of strings, delete single quotes and braces.

    Args:
        list_in: list to reformat

    Returns:
        String version of list, without single quotes and braces.

    """
    return str(tuple(list_in)).replace("'", ""). \
        replace('(', '').replace(')', ''). \
        replace('{', '').replace('}', ''). \
        replace('[', '').replace(']', '')


def _sql_format_value_list_str(list_in):
    """
    Convert a list of strings to a comma-separated list of tuples.

    Args:
        list_in: list of strings to convert

    Returns:
        List of strings as a comma-separated list of tuples.

    """
    values_str = ''
    for li in list_in:
        if type(li) is not tuple:
            li = (li,)
        values_str = values_str + '%s,' % str(li)
    values_str = values_str.replace(',)', ')')  # remove trailing tuple commas
    values_str = values_str[:-1]
    return values_str


def _sql_get_column_names(table_name, exclude=None):
    """
    For creating arguments to SQL expressions that need a list of column names.
    Args:
        table_name: name of database table to query
        exclude: column name or list of column names to exclude

    Returns:
        Comma-separated list of column names string.

    """
    # get table row data:
    result = omega_globals.session.execute('PRAGMA table_info(%s)' % table_name)

    # make list of column names:
    columns = [r[1] for r in result.fetchall()]

    # remove excluded column names
    if exclude:
        if type(exclude) is not list:
            columns.remove(exclude)
        else:
            for e in exclude:
                columns.remove(e)

    # create string with no quotes or parentheses
    columns_str = _sql_format_list_str(columns)  # str(tuple(columns)).replace("'", "").replace('(','').replace(')','')

    # table_columns = [table_name + '.' + c for c in columns]
    # table_columns_str = str(tuple(table_columns)).replace("'", "").replace('(','').replace(')','')

    return columns_str  # , table_columns_str


def _sql_valid_name(name_str):
    """
    Convert a string to a valid SQLite column name.

    Args:
        name_str (str): input string

    Returns:
        Input string with spaces replaced by underscores.

    """
    return name_str.replace(' ', '_').lower()


def dump_omega_db_to_csv(output_folder, verbose=False):
    """
    Dump database tables to .csv files in an output folder.

    Args:
        output_folder (str): name of output folder
        verbose (bool): enable additional console and logfile output if True

    """
    import common.file_io as file_io

    # validate output folder
    file_io.validate_folder(output_folder)

    omega_globals.session.flush()  # make sure database is up to date

    if verbose:
        omega_log.logwrite('\ndumping %s database to %s...' % (omega_globals.engine.name, output_folder))

    # dump tables to .csv files using pandas!
    for table in omega_globals.engine.table_names():
        dump_table_to_csv(output_folder, table, '%s_table' % table,  verbose)


def dump_table_to_csv(output_folder, table, filename, verbose):
    """
    Dump database table to .csv file in an output folder.

    Args:
        output_folder (str): name of output folder
        table (str): name of table to dump
        filename (str): name of the .csv file
        verbose (bool): enable additional console and logfile output if True

    Returns:
        DataFrame used to generate the .csv file

    """
    if verbose:
        omega_log.logwrite(table)
    sql_df = pd.read_sql("SELECT * FROM %s" % table, con=omega_globals.engine)
    sql_df.to_csv('%s/%s.csv' % (output_folder, filename), index=False)

    return sql_df
