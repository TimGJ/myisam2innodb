(Naively) converts tables in a MySQLdump file from MyISAM to 
InnoDB.

#Usage#

$ python3 convertmysqldump.py [--verbose] [--force] input output
$ python3 convertmysqldump.py --help

--verbose option gives debug information
--force will allow overwriting of existing output file
