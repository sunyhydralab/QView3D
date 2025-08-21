def tabs(tab_change: int = 0):
    """Function to manage indentation levels for code blocks."""
    global tab_num
    if 'tab_num' not in globals():
        tab_num = 0
    tab_num += tab_change
    return "\t" * tab_num