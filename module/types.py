
def is_float(value: str):
    """
    Determine whether the given string can be converted into a float or not.
    """
    try:
        float(value)
        return True
    except:
        return False
    
def is_integer(value: str):
    """
    Determine whether the given string can be converted into a integer or not.
    """
    try:
        int(value)
        return True
    except:
        return False