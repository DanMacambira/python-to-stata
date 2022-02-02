clear all
set more off
set matsize 11000
set linesize 250
set rmsg on
set trace off

* Locals from Python Code
local param_name `1' // What am I asking Stata to do
di "`param_name'"
local fname `2' // Name of input data to use
local sname `3' // Name of output save file
local num_columns `4'
local num_columns = int(`num_columns')
di "`num_columns'"
local m = 5 // Where to start loops

* Log
log using dta_to_dta_`param_name'.log, replace

* Import dta
use `sname', clear
	
** Save order
ds
local order `r(varlist)'



** Transformations

* Convert string data into nums
if strpos("`param_name'", "force_nums") {
di "``m''"
di "`num_columns'"
	forval i = 1/`num_columns' {
		gen col = real(``m'')
		drop ``m''
		rename col ``m''
		local ++m
	}
}

* Add labels to variables
else if strpos("`param_name'","var_labels") {
	local num_labels = `num_columns'/2
	local var = `m'
	forval i = 1/`num_labels' {
		local lab = `var'+1
		local my_str = `"``var''"' + " " + char(34) + `"``lab''"' + char(34)
		`my_str'
		local ++var
		local ++var
		local ++m
		local ++m
	}
}

* Define and apply value labels
else if strpos("`param_name'", "value_labels") {
	local num_labels = `num_columns'/2
	local var = `m'
	forval i = 1/`num_labels' {
		local lab = `var'+1
		local lab = subinstr("``lab''", "^", char(34),.)
		di "`var' : ``var''"
		di `"test: `lab'"'
		local my_str = `"``var'' `lab'"'
		di `"`my_str'"'
		`my_str'
		local ++var
		local ++var
		local ++m
		local ++m
	}

	local num_labels ``m''
	local num_labels = `num_labels'/2
	di "`num_labels'"
	local ++m
	local var = `m'
	forval i = 1/`num_labels' {
		local lab = `var'+1
		local lab = subinstr("``lab''", "^", char(34),.)
		di "`var' : ``var''"
		di `"test: `lab'"'
		local my_str = `"``var'' `lab'"'
		di `"`my_str'"'
		`my_str'
		local ++var
		local ++var
		local ++m
		local ++m
	}
}

* Save dta
order `order'
save `sname'.dta, replace

exit
