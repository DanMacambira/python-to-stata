import os
import subprocess
import pandas as pd
import numpy as np

def to_dta(stata_path, dataframe=None, output_path=None, file_name=None, force_nums=None, var_labels=None, value_labels=None, log_path=None):
    """
    Export dataframe to Stata silently in the background.
    
    In block mode (when there are more than 38 user arguments), the function will automatically 
    create log files in the output_path.

    Parameters
    ----------
    stata_path : str
        Full path to the Stata executable on your system, e.g., "C:\Program Files (x86)\Stata14\StataMP-64"
    dataframe : pd.DataFrame
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

    ## Dictionary and fucntion to deal with Stata's max argument limit in batch mode 
    d = {}
    def split_for_stata_max_limit(num_params, param_name, param):
        """
        Split list of parameters to deal with max argument limit and update dictionary

        Parameters
        ----------
        num_params : int
            Number of parameters in list
        param_name : str
            Name of parameter for dictionary
        param : lst
            List of parameters to be split
        """
        if num_params > 38:
            block_size = num_params
            i = 2
            while block_size > 38:
                new_params = [x.tolist() for x in np.array_split(param, i)]
                block_size = len(new_params[0])
                i += 2
            keys = [f'{param_name}_block{x+1}' for x in range(i)]
            values = [[str(len(lst))] + lst for lst in new_params]
            d.update(dict(zip(keys, values)))
        else:
            values = [str(len(param))] + param
            d.update({f'{param_name}': values})

    ## Main

    # Import dataframe into Stata through temp csv
    global csv, dta
    csv = output_path + file_name + '.csv'
    dta = output_path + file_name
    dataframe.to_csv(csv, sep='|', index=True, chunksize=10 ** 7)

    # Core params
    params = [csv, dta]

    # Convert string columns to num type columns
    # Add columns found in the vaue_labels
    if value_labels is None:
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
        force_nums = [var.lower() for var in force_nums if var in dataframe.columns]
        force_nums = list(set(force_nums))
        force_nums_cols = len(force_nums)
        params.append(str(force_nums_cols))
        params.extend(force_nums)
    else:
        force_nums_cols = 0
        force_nums = []
    tup_force_nums = (force_nums_cols, force_nums, 'force_nums')

    # Variable Labels
    if var_labels is not None:
        var_labels = {var.lower(): var_labels[var] for var in var_labels if var in dataframe.columns}
        labels = [(f'label var {var}', f'{var_labels[var]}') for var in var_labels]
        labels = list(sum(labels, ())) 
        labels_cols = len(labels)
        params.append(str(labels_cols))
        params.extend(labels)
    else:
        labels_cols = 0
        labels = []
    tup_labels = (labels_cols, labels, 'var_labels')

    # Variable Labels
    if value_labels is not None:
        lab_vars, lab_values = value_labels
        # First add and define the value labels
        values = [(f'label define {var.lower()}', f'{lab_values[var]}') for var in lab_values]
        values = list(sum(values, ()))
        values = [w.replace('"', '^') for w in values]
        values_cols = len(values)
        params.append(str(values_cols))
        params.extend(values)
        # Now add them to the desired varaibles
        lab_vars = {var: lab_vars[var] for var in lab_vars if var in dataframe.columns}
        myvars = [(f'label values {var.lower()}', f'{lab_vars[var]}') for var in lab_vars]
        myvars = list(sum(myvars, ())) 
        myvars_cols = len(myvars)
        params.append(str(myvars_cols))
        params.extend(myvars)
    else:
        values_cols = 0
        values = []
        myvars_cols = 0
        myvars = []
    tup_values = (values_cols, values, 'lab_values')
    tup_myvars = (myvars_cols, myvars, 'lab_vars')


    ## Check if params are too long
    if len(params) > 41:
        all_params = [tup_force_nums, tup_labels, tup_values, tup_myvars]
        for param_cols,param,param_name in all_params:
            split_for_stata_max_limit(num_params = param_cols,
                                      param_name = param_name,
                                      param = param)
        bl_params = [csv, dta]

        # Merge label values and variables
        l = {key: d[key] for key in d if key in [tup_values[-1], tup_myvars[-1]]}
        labels = list(l.values())[0] + list(l.values())[1]
        d.update({'value_labels': labels})
        d = {key: d[key] for key in d if key not in [tup_values[-1], tup_myvars[-1]]}
        blocked_params = [(block, d[block]) for block in d]
        blocked_params = [(prn, p) for (prn, p) in blocked_params if p[0] != '0']
    else:
        blocked_params = ()


    #### RUN

    # Stata Do File path
    dir_path = os.path.dirname(os.path.realpath(__file__))
    do_file_csv_to_dta = dir_path + '/csv_to_dta'
    do_file_dta_to_dta = dir_path + '/dta_to_dta'
    cmd = [stata_path, "/e", 'do'] + [do_file_csv_to_dta] + params

    try: 

        ## Form the Stata do command
        ## Run Stata based on number of params and log file
        if not d:
            if log_path is None:
                subprocess.check_output(cmd, shell=True)
            else:
                subprocess.check_output(cmd, cwd=log_path, shell=True)
        else:
            print('Passing Blocks')
            cmd_init = [stata_path, "/e", 'do'] + [do_file_csv_to_dta] + bl_params
            if log_path is None:
                subprocess.check_output(cmd_init, shell=True)
            else:
                subprocess.check_output(cmd_init, cwd=log_path, shell=True)
            for param_name,block in blocked_params:
                print(f'Block: {param_name} - {block}\n')
                cmd = [stata_path, "/e", 'do'] + [do_file_dta_to_dta] + [param_name] + bl_params + block
                if log_path is None:
                    subprocess.check_output(cmd, shell=True)
                else:
                    subprocess.check_output(cmd, cwd=log_path, shell=True)

    except subprocess.CalledProcessError as e:
        print(f'Command Line Process failed - return code: {e.returncode}.\n')
    else:
        # Delete temp csv file
        if dataframe is not None:
            os.remove(csv)
    finally:
        print(f'Number of params passed to Stata: {len(params)}')
