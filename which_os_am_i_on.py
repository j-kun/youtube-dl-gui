import platform

os_name = platform.system().lower()

def mac():
    return os_name=="darwin"

def linux():
    return os_name=="linux"

def windows():
    return os_name=="windows"


if __name__=='__main__':
    print("is_mac    : {0}".format(mac()))
    print("is_linux  : {0}".format(linux()))
    print("is_windows: {0}".format(windows()))
