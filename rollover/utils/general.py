""" General utility functions, that are kept here for convenience. 
If more functions that can be grouped are added, these may be collected
in a new file instead.

"""


def get_arguments(function, num_first=0):
    """ Given a function, return all its arguments and the mandatory 
    arguments. This can be used to check `**kwargs` type of input. 
    num_first skips the first num_first arguments (that are mandatory)
    
    :param function: The function whose arguments should be obtained
    :type function: class 'function'
    
    :param num_first: How many arguments to skip in the beginning
    :type num_first: int
    
    returns: Lists of all arguments and mandatory arguments
    rtype: list[ list[ str ] ]
    
    """
    
    num_all = function.__code__.co_argcount
    all_arg = function.__code__.co_varnames[num_first:num_all]
    num_def = len(function.__defaults__)
    num_man = len(all_arg) - num_def
    man_arg = all_arg[:num_man] if num_man > 0 else []
    
    return all_arg, man_arg


def extract_function_args(function, arg_dict, num_first=0):
    """ Given a function and a dictionary containing possible arguments, 
    return a new dictionary containing only the arguments accepted by 
    the function (i.e. remove any keywords that are not arguments to the
    function). Doesn't give an error if a mandatory argument is missing.
    
    :param function: The function whose arguments should be obtained
    :type function: class 'function'
    
    :param arg_dict: Dictionary containing possible function arguments
    :type arg_dict: dict
    
    :param num_first: How many arguments to skip in the beginning
    :type num_first: int
    
    :returns: Dictionary with acceptable function arguments
    :rtype: dict
    
    """
    
    all_args, man_args = get_arguments(function, num_first)
    
    return {key: arg_dict[key] for key in arg_dict if key in all_args}
