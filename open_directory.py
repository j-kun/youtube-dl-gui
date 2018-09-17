#!/usr/bin/env python
# standard libraries
import os
import subprocess
import logging
log = logging.getLogger(__name__)

# other libraries
import which_os_am_i_on as os_is

def _run_cmd(cmd):
    log.debug("executing {cmd}".format(cmd=cmd))
    return subprocess.Popen(cmd)

if os_is.windows():
    def open_directory(path, select):
        '''select=True: parent directory is opened, path (file or directory) is selected.
           select=False: path (directory) is opened and nothing is selected.'''
        cmd = ["explorer"]
        if select:
            cmd.append("/select,")
        cmd.append(path)
        return _run_cmd(cmd)
    def open_file(path):
        os.startfile(path) # pylint: disable=no-member
elif os_is.linux():
    def open_directory(path, select):
        '''select=True: parent directory is opened, path (file or directory) is selected.
           select=False: path (directory) is opened and nothing is selected.'''
        if select:
            dirpath, filename = os.path.split(path)
        else:
            dirpath = path
        cmd = ["xdg-open", dirpath]
        return _run_cmd(cmd)
    def open_file(path):
        return _run_cmd(("xdg-open", path))
elif os_is.mac():
    #https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man1/open.1.html
    def open_directory(path, select):
        '''select=True: parent directory is opened, path (file or directory) is selected.
           select=False: path (directory) is opened and nothing is selected.'''
        cmd = ["open"]
        if select:
            cmd.append("-R")
        cmd.append("--")
        cmd.append(path)
        return _run_cmd(cmd)
    def open_file(path):
        return _run_cmd(("open", "--", path))
        
else:
    raise ValueError("unknown operating system: "+os_is.os_name)


if __name__=='__main__':
    import os
    
    def get_some_subdirectory(path):
        l = os.listdir(path)
        for fn in l:
            ffn = os.path.join(path, fn)
            if os.path.isdir(ffn):
                if fn[0]!='.':
                    return ffn
    def get_some_file(path):
        l = os.listdir(path)
        for fn in l:
            ffn = os.path.join(path, fn)
            if os.path.isfile(ffn):
                if fn[0]!='.':
                    return ffn
        return get_some_file(get_some_subdirectory(path))

    path = os.path.expanduser("~")
    path = get_some_subdirectory(path)
    path = get_some_subdirectory(path)
    path = get_some_file(path)
    
    print(path)
    open_directory(path, select=True)
