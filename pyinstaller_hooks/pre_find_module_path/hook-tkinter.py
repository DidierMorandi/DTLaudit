"""Keep tkinter discoverable; Tcl/Tk data is collected explicitly in DTLaudit.spec."""


def pre_find_module_path(hook_api):
    return None
