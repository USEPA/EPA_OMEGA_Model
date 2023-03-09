import pandas as pd
from csv import reader, writer


def save_file(session_settings, df, save_folder, file_id, effects_log, extension='parquet'):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
        df: the DataFrame to be saved.
        save_folder: a Path instance for the save folder.
        file_id (str): file identifier to be included in the saved filename.
        effects_log: an instance of the EffectsLog class.
        extension (str): entered in runtime_options.csv (either 'csv' or 'parquet' with 'parquet' the default)

    Returns:
        The passed dict_to_save as a DataFrame while also saving that DataFrame to the save_folder.

    Note:
        If saving files as parquet files, they are readable only by Pandas and cannot be read directly by Excel. To
        read the parquet file into Pandas, do the following in the Python Console on your IDE:
        Type 'import pandas as pd' without the quotes.
        Type 'from pathlib import Path' without the quotes.
        Type 'path = Path("path to file")' without the single quotes but with the double quotes around the path; include
        double backslash \\ rather than single backslash.
        Type 'file = "filename.parquet"' without the single quotes but with the double quotes.
        Type 'df = pd.read_parquet(path / file)' without the quotes.
        The DataFrame (df) should contain the contents of the parquet file.

    """
    if 'context' in file_id:
        filepath = save_folder / f'{file_id}.{extension}'
    else:
        filepath = save_folder / f'{session_settings.session_name}_{file_id}.{extension}'

    if extension not in ['csv', 'parquet']:
        effects_log.logwrite(f'Improper extension provided when attempting to save {file_id} file.')
    if extension == 'parquet':
        df.to_parquet(filepath, engine='fastparquet', compression='snappy', index=False)
    else:
        df.to_csv(filepath, index=False)


def add_id_to_csv(filepath, output_file_id_info):
    """

    Args:
        filepath: the Path object to the file.
        output_file_id_info (list): a list of string info to include as output file identifiers.

    Returns:
        Nothing, but reads the appropriate input file, inserts a new first row and saves the output_file_id_info in that
        first row.

    """

    with open(filepath, 'r') as read_file:
        rd = reader(read_file)
        lines = list(rd)
        lines.insert(0, output_file_id_info)

    with open(filepath, 'w',newline='') as write_file:
        wt = writer(write_file)
        wt.writerows(lines)

    read_file.close()
    write_file.close()
