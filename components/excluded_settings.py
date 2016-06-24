"""
Holds the list of settings to be ignored by the sweeper program.
"""

def getExcludedSettings(exclude_test_settings = False):
    """Returns the list of excluded settings"""
    
    # excluded settings: these are always excluded
    excl = """
# lockin amplifier

"""
    
    # test settings: these are excluded if specified
    test = """
# DC Box AD5764 testing settings
test_return_zero
test_return_random
test_accept_float
"""
    
    excl_settings = [setting for setting in excl.splitlines() if (setting and not (setting.startswith('#')))]
    test_settings = [setting for setting in test.splitlines() if (setting and not (setting.startswith('#')))]
    
    if exclude_test_settings:return excl_settings+test_settings
    return excl_settings