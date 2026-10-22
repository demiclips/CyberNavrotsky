import win32gui


def window_enum_callback(id,extra):
    """
    Function that checks which windows are open
    :param id: name\handle of the current window
    """

    if win32gui.IsWindowVisible(id): #checks if the client can see it

        title = win32gui.GetWindowText(id) #get name of the open window

        if title.strip():#prints only ones that have text
            print(title)


if __name__ == "__main__":

    # Start scan: EnumWindows passes each window handle to window_enum_callback
    win32gui.EnumWindows(window_enum_callback,None) #doesnt work without none, extra variable


