#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converts tables defined as MyISAM in to InnoDB in a
MySQLdump file. 

This requires a script, rather than simply using a command
line tool like sed or awk. This is because both these tools
operate on a stream and line basis, and have no knowledge
of lines which have gone before. Plus, of course, awk
and sed don't exist in the Microsoft world. 

The reason we can't use (say) a very simple sed script
is that although we may wish to convert our own tables from
MyISAM to InnoDB there are some tables in the default
MySQL schema which we should leave well alone.

Because there is no guarantee of the format of the 
MySQLdump file and because (for reasons of memory)
we can only go forwards through it line by line, 
each line is subject to a number of case-insensitive 
reguluar expression searches. This makes the script 
tediously slow on large dumpfiles, and so it is probably
best run in batch mode (for which it is designed).

(Operationally, the master database would only have to
be offline whilst the MySQLdump operation was completed)
"""

import logging
import argparse
import os.path
import sys
import re
import enum


def ProcessArguments():
    """
    Process the command line arguments returning an argparse namepsace
    or None if the parse didn't work.
    """
    parser = argparse.ArgumentParser(description='Convert MySQLdump MyISAM tables to InnoDB')
    parser.add_argument('--verbose', help='Verbose output', action='store_true')
    parser.add_argument('--force',   help='Overwrite existing output file', action = 'store_true')
    parser.add_argument('input',     help='Input MySQLdump file')
    parser.add_argument('output',    help='Input MySQLdump file')
    try:
        args = parser.parse_args()
    except SystemExit:
        print('Error processing command line arguments')
        sys.exit()
    return args

def SetupLogging(verbose):
    """
    Set up the logging options. Done in a separate procedure for the sake
    of neatness and readabilty than for any other reason.
    """
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level = level, format='%(asctime)s:%(levelname)-7s: %(message)s')


def ProcessFiles(infile, outfile, excluded):
    """
    Process the input file writing the output as we go. We do this line
    by line as the dump file might be too masive to fit comfortably in 
    memory. Eeh. It's just like the old days of having twin tape drives.
    
    Excluded is a list of databases we DO NOT want to convert from
    MyISAM to InnoDB
    """

    database_re = re.compile(r'(^CREATE DATABASE.*`)(\w+)(`.*$)', re.IGNORECASE)
    table_re    = re.compile(r'(^CREATE TABLE.*`)(\w+)(`.*$)', re.IGNORECASE)
    myisam_re   = re.compile(r'MyISAM', re.IGNORECASE)
    
    database   = None # Name of the most recently discovered DB
    isexcluded = True # Is the database in the excluded list
    preserved  = 0    # Number of lines preserved
    changed    = 0    # Number of lines changed
    
    for n, line in enumerate(infile):
        founddb = database_re.search(line)
        if founddb:
            database   = founddb.groups()[1]
            isexcluded = database.upper() in excluded
            logging.info('Line {:,}: Found database {:} (excluded = {})'.format(
                    n+1, database, 'Yes' if isexcluded else 'No'))

        foundtable = table_re.search(line)
        if foundtable:
            table   = foundtable.groups()[1]
            isexcluded = database.upper() in excluded
            logging.info('Line {:,}: Found table {:})'.format(
                    n+1, table))
            
        if not isexcluded and myisam_re.search(line):
            newline = myisam_re.sub('InnoDB', line)
            logging.info('Line {:,}: Changing {}.{} `{}` -> `{}`'.format(n+1, 
                          database, table, line.rstrip(), newline.rstrip()))
            outfile.write(newline)
            changed +=1
        else:
            outfile.write(line)
            preserved += 1
    logging.info('Read {:,} lines. {:,} lines changed, {:,} lines preserved'.format(n+1, changed, preserved))
            

if __name__ == '__main__':

    args = ProcessArguments()
    SetupLogging(args.verbose)
    logging.debug('Converting {} to {}. Forcible = {}'.format(
            args.input, args.output, 'Yes' if args.force else 'No'))

    excluded = ['mysql'] # Default list of databases which we don't change
    # Open input for reading...
    
    if os.path.exists(args.output) and not args.force:
        logging.error('File {} already exists. (Use the --force option, Luke)'.format(
                args.output))
    else:
        with open(args.input) as infile, open(args.output, 'w') as outfile:
            logging.debug('Opened {} for reading'.format(args.input))
            logging.debug('Opened {} for writing'.format(args.output))
            ProcessFiles(infile, outfile, [e.upper() for e in excluded])
