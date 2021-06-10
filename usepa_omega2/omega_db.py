"""
omega_db.py
===========

"""

print('importing %s' % __file__)

import o2  # import global variables
import omega_log
import file_eye_oh as fileio
import pandas as pd
from sqlalchemy import create_engine

# NOTE:
# INTEGERS get stored in sqlite as byte strings:i.e.:
# >>int.from_bytes(b'\xe4\x07\x00\x00\x00\x00\x00\x00', 'little') equals 2020, so we need to use Numeric if we want
# to be able to easily use them and see them in database dumps, so model_year is Numeric, not Integer
# The only place where Integer works as expected is for primary keys

import sqlalchemy
from sqlalchemy import String, ForeignKey, Enum, Float, Numeric, Integer
from sqlalchemy import func
from sqlalchemy import MetaData, Table, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

SQABase = declarative_base(name='SQABase')


def init_omega_db():
    o2.engine = create_engine('sqlite:///:memory:', echo=False)
    o2.session = Session(bind=o2.engine)
    # !!!SUPER IMPORTANT, OTHERWISE FOREIGN KEYS ARE NOT CHECKED BY SQLITE DEFAULT!!!
    o2.session.execute('pragma foreign_keys=on')


def sql_unpack_result(query_result_tuples, index=0):
    return [r[index] for r in query_result_tuples]


def sql_format_list_str(list_in):
    return str(tuple(list_in)).replace("'", ""). \
        replace('(', '').replace(')', ''). \
        replace('{', '').replace('}', ''). \
        replace('[', '').replace(']', '')


def sql_format_value_list_str(list_in):
    values_str = ''
    for li in list_in:
        if type(li) is not tuple:
            li = (li,)
        values_str = values_str + '%s,' % str(li)
    values_str = values_str.replace(',)', ')')  # remove trailing tuple commas
    values_str = values_str[:-1]
    return values_str


def sql_get_column_names(table_name, exclude=None):
    """
    For creating arguments to SQL expressions that need a list of column names
    :param table_name: name of database table to query
    :param exclude: column name or list of column names to exclude
    :return: comma separated list of column names string
    """

    # get table row data:
    result = o2.session.execute('PRAGMA table_info(%s)' % table_name)

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
    columns_str = sql_format_list_str(columns)  # str(tuple(columns)).replace("'", "").replace('(','').replace(')','')

    # table_columns = [table_name + '.' + c for c in columns]
    # table_columns_str = str(tuple(table_columns)).replace("'", "").replace('(','').replace(')','')

    return columns_str  # , table_columns_str


def sql_valid_name(name_str):
    return name_str.replace(' ', '_').lower()


def dump_omega_db_to_csv(output_folder, verbose=False):
    # validate output folder
    fileio.validate_folder(output_folder)

    o2.session.flush()  # make sure database is up to date

    if verbose:
        omega_log.logwrite('\ndumping %s database to %s...' % (o2.engine.name, output_folder))

    # dump tables to .csv files using pandas!
    for table in o2.engine.table_names():
        if verbose:
            omega_log.logwrite(table)
        sql_df = pd.read_sql("SELECT * FROM %s" % table, con=o2.engine)
        sql_df.to_csv('%s/%s_table.csv' % (output_folder, table), index=False)
