"""
omega_db.py
===========


"""

import file_eye_oh as fileio

import pandas as pd

from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

SQABase = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=True)


def dump_database_to_csv(engine, output_folder):
    # validate output folder
    fileio.validate_folder(output_folder)

    # dump tables to .csv files using pandas!
    for table in engine.table_names():
        print(table)
        sql_df = pd.read_sql("SELECT * FROM %s" % table, con=engine)
        sql_df.to_csv('%s/%s.csv' % (output_folder, table), index=False)
