"""This module enable direct editing of input keywords in the input 
file. Options not available in CAE can therefore be added via the 
scripting interface.

.. codeauthor:: Knut Andreas Meyer
"""

from __future__ import print_function
import sys, os, inspect
from abaqusConstants import *
import abaqus

from rollover.utils import abaqus_python_tools as apt

def add_at_end_of_cat(keyword_block, string_to_add, category, name):
    """Add `string_to_add` just before the end of the category of type 
    `category` with name `name`. 
    
    :param keyword_block: The Abaqus keywordBlock that contains the 
                          keyword to be written to the input file
    :type keyword_block: KeywordBlock object (Abaqus)
    
    :param string_to_add: The string to add to the input file
    :type string_to_add: str
    
    :param category: The category to search for (E.g. Part, Step)
    :type category: str
    
    :param name: The name of the category to find (E.g. Part1-1, Step-1)
    :type name: str
    
    :returns: None
    :rtype: None

    """
    
    find_strings = ['*' + category, 'name=' + name]
    sie_blocks = keyword_block.sieBlocks
    category_start_line = find_strings_in_iterable(sie_blocks, find_strings)
    add_line_num = find_strings_in_iterable(sie_blocks, ['*End ' + category], 
                                            min_ind=category_start_line) - 1
    
    keyword_block.insert(add_line_num, string_to_add)
    

def add_after(keyword_block, string_to_add, find_strings=None):
    """Add `string_to_add` after the first line in to keyword_block that 
    contains all strings in `find_strings`. 
    
    :param keyword_block: The Abaqus keywordBlock that contains the 
                          keyword to be written to the input file
    :type keyword_block: KeywordBlock object (Abaqus)
    
    :param string_to_add: The string to add to the input file
    :type string_to_add: str
    
    :param find_strings: List of strings that the line prior after which 
                         `string_to_add` should be added must contain. 
                         If `find_strings` = None, add in beginning of 
                         the input file
    :type find_strings: list[ str ]
    
    :returns: None
    :rtype: None
    
    """
    
    if find_strings is None:
        line_num = 0
    else:
        line_num = find_strings_in_iterable(keyword_block.sieBlocks, find_strings)
    
    keyword_block.insert(line_num, string_to_add)


def add_before(keyword_block, string_to_add, find_strings=None):
    """Add `string_to_add` before the first line in to keyword_block 
    that contains all strings in `find_strings`. 
    
    :param keyword_block: The Abaqus keywordBlock that contains the 
                          keyword to be written to the input file
    :type keyword_block: KeywordBlock object (Abaqus)
    
    :param string_to_add: The string to add to the input file
    :type string_to_add: str
    
    :param find_strings: List of strings that the line prior after which
                         `string_to_add` should be added must contain. 
                         If `find_strings` = None, add in beginning of 
                         the input file
    :type find_strings: list[ str ]
    
    :returns: None
    :rtype: None
    
    """
    
    if find_strings is None:
        line_num = len(keyword_block.sieBlocks)
    else:
        line_num = find_strings_in_iterable(keyword_block.sieBlocks, find_strings)-1
    
    keyword_block.insert(line_num, string_to_add)
    

def find_strings_in_iterable(iterable, find_strings, min_ind=0):
    """Find the lowest index >= min_ind of a string in `iterable` that 
    contains all strings in `find_strings`
    
    :param iterable: An iterable object containing strings. Must support 
                    iteration (i.e. :code:`for item in iterable`) and 
                    be subscriptable (i.e. :code:`iterable[3:]`). 
    :type iterable: An iterable of strings
    
    :param find_strings: List of strings that the the item in `iterable`
                         must contain to be found. 
    :type category: list[ str ]
    
    :param min_ind: The index from which the search will start
    
    :returns: None
    :rtype: None
    
    """
    
    for n, line in enumerate(iterable[min_ind:]):
        if all([find_string in line for find_string in find_strings]):
            return n + min_ind
    
    # If no match found, print out problem and raise ValueError
    log_str = 'Could not find a line containing the following strings:'
    for find_string in find_strings:
        log_str = log_str + '\n* "' + find_string + '"'
    
    raise ValueError(log_str)

