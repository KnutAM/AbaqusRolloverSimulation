""" Module for loading and saving using json. Simplifies syntax and 
removes unicode strings (converts to regular strings)

.. codeauthor:: Knut Andreas Meyer
"""

import json, sys

def save(filename, contents):
    """Save contents to filename with the json file format
    
    :param filename: The name of the file to be saved
    :type filename: str
    
    :param contents: Dictionary to be saved to json
    :type contents: dict
    
    :returns: None
    :rtype: None

    """
    with open(filename, 'w') as fid:
        json.dump(contents, fid, indent=4)


def read(filename):
    """Load contents from filename with the json file format
    
    For Python 2, unicode strings within the loaded dictionary are 
    converted to regular strings. (In Python 3 unicode is str)
    
    :param filename: The name of the file to be loaded
    :type filename: str
    
    :returns: Dictionary to be saved to json
    :rtype contents: dict

    """
    with open(filename, 'r') as fid:
        contents = json.load(fid)
    
    if sys.version_info.major == 3:
        return contents
    else:
        return u_to_str_in_dict(contents)
    
    
def u_to_str_in_dict(dict_to_convert):
    """Convert unicode entries a dictionary
    
    Unicode strings within the loaded dictionary are converted to 
    regular strings. This is only required for Python 2.
    
    :param filename: The name of the file to be loaded
    :type filename: str
    
    :returns: Dictionary to be saved to json
    :rtype contents: dict

    """
    if sys.version_info.major == 3:
        return dict_to_convert
        
    new_dict = {}
    for key in dict_to_convert:
        if isinstance(dict_to_convert[key], unicode):
            new_dict[key] = str(dict_to_convert[key])
        elif isinstance(dict_to_convert[key], dict):
            new_dict[key] = u_to_str_in_dict(dict_to_convert[key])
        else:
            new_dict[key] = dict_to_convert[key]
    
    return new_dict
