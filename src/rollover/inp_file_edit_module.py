# Abaqus input file editing module
# Allows changing options not available in CAE
from __future__ import print_function
import sys, os, inspect
from abaqusConstants import *
import abaqus

# Custom imports (need to append project path to python path)
# __file__ not found when calling from abaqus, 
# used solution from "https://stackoverflow.com/a/53293924":
this_path = os.path.dirname(os.path.abspath(inspect.getfile(lambda: None)))
if not this_path in sys.path:
    sys.path.append(this_path)
    
import abaqus_python_tools as apt

def add_at_end_of_cat(keyword_block, string_to_add, category, name):
    # Add string_to_add before the first line in to keyword_block that contains all strings in 
    # find_strings.
    # Input
    # keyword_block         Abaqus keywordBlock object (access model.keywordBlock)
    # string_to_add         The string to add to the input file
    # category              Category to search for (E.g. Part, Step, etc.)
    # name                  Name for category to find (E.g. Part1-1, Step-1, etc.)
    #
    
    find_strings = ['*' + category, 'name=' + name]
    sie_blocks = keyword_block.sieBlocks
    category_start_line = find_strings_in_iterable(sie_blocks, find_strings)
    add_line_num = find_strings_in_iterable(sie_blocks, ['*End ' + category], 
                                            min_ind=category_start_line) - 1
    
    keyword_block.insert(add_line_num, string_to_add)
    

def add_after(keyword_block, string_to_add, find_strings=None):
    # Add string_to_add after the first line in to keyword_block that contains all strings in 
    # find_strings.
    # Input
    # keyword_block         Abaqus keywordBlock object (access model.keywordBlock)
    # string_to_add         The string to add to the input file
    # find_strings          List of strings that the line prior after which string_to_add should be 
    #                       added must contain. If find_strings=None, add in beginning of input file
    #
    
    if find_strings is None:
        line_num = 0
    else:
        line_num = find_strings_in_iterable(keyword_block.sieBlocks, find_strings)
    
    keyword_block.insert(line_num, string_to_add)


def find_strings_in_iterable(iterable, find_strings, min_ind=0):
    # Return the first position in iterable which contains all strings in the list find_strings
    # Input
    # iterable      An iterable (e.g. list, tuple) containing strings
    # find_strings  A list of strings that all must be in the string in iterable to produce a match
    # min_ind       The minimum index to return. I.e. search from this index and onwards
    
    for n, line in enumerate(iterable[min_ind:]):
        if all([find_string in line for find_string in find_strings]):
            return n + min_ind
    
    # If no match found, print out problem and raise ValueError
    log_str = 'Could not find a line containing the following strings:'
    for find_string in find_strings:
        log_str = log_str + '\n* ' + find_string
    apt.log(log_str)
    
    raise ValueError