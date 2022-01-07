clear all
set more off
set matsize 11000
set linesize 250
set rmsg on
set trace off

* Locals from Python Code
local fname `1' // Name of input data to use
local sname `2' // Name of output save file for fstats
local num_columns `3' // Number of columns to convert
local num_columns = int(`num_columns')

* Import csv
import delimited `fname', delimiter("|") stringcols(_all)
capture drop v1

* Save order
ds
local order `r(varlist)'

* Convert string data into nums
if `num_columns' > 0 {
	local m = 4
	forval i = 1/`num_columns' {
		gen col = real(``m'')
		drop ``m''
		rename col ``m''
		local ++m
	}
}

* Add labels to variables
local num_labels ``m''
local num_labels = `num_labels'/2
if `num_labels' > 0 {
	local var = `m'+1
	forval i = 1/`num_labels' {
		local lab = `var'+1
		local my_str = `"``var''"' + " " + char(34) + `"``lab''"' + char(34)
		`my_str'
		local ++var
		local ++var
	}
}

* Save dta
order `order'
save `sname'.dta, replace

exit
