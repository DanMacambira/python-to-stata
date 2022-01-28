import os
import subprocess

def to_dta(stata_path, dataframe=None, output_path=None, file_name=None, force_nums=None, var_labels=None, value_labels=None, log_path=None):
    """
    Export dataframe to Stata silently in the background
    Parameters
    ----------
    stata_path : str
        Full path to the Stata executable on your system, e.g., "C:\Program Files (x86)\Stata14\StataMP-64"
    dataframe :
        Dataframe to pass onto Stata.
    output_path : str
        Path for dta file.
    file name : str
        Name of file.
    force_nums: list of str
        Columns to be converted into num types with Stata's real() command.
        Note, this do file sets all dtypes to be strings in order to protect data types.
    var_labels: dict of str, e.g. {'myvar1': 'mylabel1', 'myvar2': 'mylabel2'}
        Labels to add to variables in Stata
    value_labels: (dict, dict), e.g., (vars, value labels)
        Value labels to add to variables in Stata
    log_path : str
        Full path to save the log files. By default will save in the current working directory
    """

    #### PREP

    # Import dataframe into Stata through temp csv
    global csv, dta
    if dataframe is not None:
        csv = output_path + file_name + '.csv'
        dta = output_path + file_name
        dataframe.to_csv(csv, sep='|', index=True, chunksize=10 ** 7)

    # Stata locals
    params = [csv, dta]

    # Convert string columns to num type columns
    # Add columns found in the vaue_labels
    if value_labels is  None:
        fn = []
    else:
        lab_vars, _ = value_labels
        fn = list(lab_vars.keys())
    if force_nums is not None:
        if isinstance(force_nums, list):
            pass
        else:
            force_nums = [force_nums]
        force_nums = force_nums + fn
        force_nums = [var for var in force_nums if var in dataframe.columns]
        force_nums = list(set(force_nums))
        num_columns = len(force_nums)
        params.append(str(num_columns))
        params.extend(force_nums)

    # Variable Labels
    if var_labels is not None:
        var_labels = {var: var_labels[var] for var in var_labels if var in dataframe.columns}
        labels = [(f'label var {var}', f'{var_labels[var]}') for var in var_labels]
        labels = list(sum(labels, ())) 
        num_columns = len(labels)
        params.append(str(num_columns))
        params.extend(labels)

    # Variable Labels
    if value_labels is not None:
        lab_vars, lab_values = value_labels
        # First add and define the value labels
        values = [(f'label define {var}', f'{lab_values[var]}') for var in lab_values]
        values = list(sum(values, ()))
        values = [w.replace('"', '^') for w in values]
        num_columns = len(values)
        params.append(str(num_columns))
        params.extend(values)
        # Now add them to the desired varaibles
        lab_vars = {var: lab_vars[var] for var in lab_vars if var in dataframe.columns}
        myvars = [(f'label values {var}', f'{lab_vars[var]}') for var in lab_vars]
        myvars = list(sum(myvars, ())) 
        num_columns = len(myvars)
        params.append(str(num_columns))
        params.extend(myvars)


    #### RUN
    print(params)

    # Stata Do File path
    dir_path = os.path.dirname(os.path.realpath(__file__))
    do_file = dir_path + '/csv_to_dta'

    # Form the Stata do command
    cmd = [stata_path, "/e", 'do'] + [do_file] + params
    if log_path is None:
        subprocess.call(cmd)
    else:
        subprocess.call(cmd, cwd=log_path)

    # Delete temp csv file
    if dataframe is not None:
        os.remove(csv)
