#idea based on:
#http://victorlin.me/posts/2012/08/26/good-logging-practice-in-python

'''
usage:
======
in main program:
    import logging_setup
    log = logging_setup.getLogger(__name__)

equivalent:
    import logging_setup, logging
    log = logging.getLogger(__name__)

in other files:
    import logging
    log = logging.getLogger(__name__)

dependencies:
=============
metainfo. must specify the following two str constants:
    PATH_CONFIG
    PATH_LOG
'''

# standard libraries
import os
import atexit
import logging, logging.config, json
getLogger = logging.getLogger

# other libraries
import metainfo


# constants
_END_OF_LOG = " end of log ".center(30, '=')

LEVEL_MAX = logging.CRITICAL*10
LEVEL_SENTINEL = logging.WARNING-1 # shall not be printed on stderr
logging.addLevelName(LEVEL_SENTINEL, 'SENTINEL')


# "fake" logger because I can not log as long as the real logger is not setup
class DelayedLogger(object):
    def __init__(self):
        self.entries = list()
    def log(self, level, msg):
        self.entries.append((level, msg))
    def append(self, item):
        # for backward compatibility
        self.entries.append(item)
    def write(self, log):
        for level, msg in self.entries:
            log.log(level, msg)
_log = DelayedLogger()


# create logging configuration file if not existing
FN_LOGGING_JSON = "logging.json"
ffn_log_configuration = metainfo.get_config_ffn(FN_LOGGING_JSON, log=_log)
_log.append((logging.INFO, "log configuration file location: {ffn}".format(ffn=ffn_log_configuration)))


# check whether log file is already in use
class UniqueFilenameCreator(object):
    PATTERN = "_{counter}"
    def __init__(self, desired_file_name):
        self.ffn = desired_file_name
    def create(self):
        if self.is_filename_usable(self.ffn):
            return self.ffn
        _log.log(logging.INFO, "log file {ffn!r} is already in use.".format(ffn=self.ffn))
        i = 1
        path_name, ext = os.path.splitext(self.ffn)
        while True:
            ffn = path_name + self.PATTERN.format(counter=i) + ext
            if self.is_filename_usable(ffn):
                return ffn
            i += 1
    @staticmethod
    def is_filename_usable(ffn):
        if os.path.isfile(ffn):
            with open(ffn, 'rt') as f:
                for ln in f:
                    pass
                if _END_OF_LOG not in ln:
                    # log file is (most likely) in use by other currently running instance
                    return False
        return True


# read logging configuration file
with open(ffn_log_configuration, 'rt') as f:
    print(f.name)
    _log_settings = json.load(f)
    # specify directory for log file if not given
    _fn_log_file = _log_settings['handlers']['log-file']['filename']
    if os.path.isabs(_fn_log_file):
        ffn_log_file = _fn_log_file
        _log_directory = os.path.split(ffn_log_file)[0]
    else:
        _log_directory = metainfo.PATH_LOG
        ffn_log_file = os.path.join(_log_directory, _fn_log_file)
    # create directory for log file if not existing
    if not os.path.isfile(ffn_log_file):
        if not os.path.isdir(_log_directory):
            os.makedirs(_log_directory)
            _log.append((logging.INFO, "created directory for log file: {}".format(_log_directory)))
    # make sure to not use the log file of another currently running instance
    ffn_log_file = UniqueFilenameCreator(ffn_log_file).create()
    _log_settings['handlers']['log-file']['filename'] = ffn_log_file
    _log.append((logging.DEBUG, "log file location: {}".format(ffn_log_file)))
    # configure logging module
    logging.config.dictConfig(_log_settings)
del f
del ffn_log_configuration


# write to log file
_real_log = logging.getLogger(__name__)
_log.write(_real_log)
del _log


# enable/disable log file in log settings (does not take effect until restart)
def get_level_number(level):
    if isinstance(level, int):
        return level
    try:
        return int(level)
    except ValueError:
        return logging.getLevelName(level)
    

def iter_file_handlers(_log_settings):
    handlers = _log_settings['handlers']
    for handler in handlers:
        handler = handlers[handler]
        if 'filename' in handler:
            yield handler

def _is_logfile_enabled(_log_settings):
    for handler in iter_file_handlers(_log_settings):
        if get_level_number(handler['level']) <= LEVEL_MAX:
            return True
    return False
    
is_logfile_enabled = _is_logfile_enabled(_log_settings)
print("is_logfile_enabled: "+str(is_logfile_enabled))

def disable_logfile():
    global is_logfile_enabled
    if not is_logfile_enabled:
        return True
    ffn_log_configuration = metainfo.get_config_ffn(FN_LOGGING_JSON, log=_real_log, create=True)
    with open(ffn_log_configuration, 'rt') as f:
        _log_settings = json.load(f)
    for handler in iter_file_handlers(_log_settings):
        handler['filename'] = "/dev/null"
        handler['level']    = LEVEL_MAX+1
    with open(ffn_log_configuration, 'wt') as f:
        _real_log.info("writing log configuration file (disable logfile): {ffn}".format(ffn=ffn_log_configuration))
        f.write(json.dumps(_log_settings, indent=4, sort_keys=True))
    is_logfile_enabled = False
    return True

def enable_logfile():
    global is_logfile_enabled
    if is_logfile_enabled:
        return True
    ffn_log_configuration = metainfo.get_config_ffn(FN_LOGGING_JSON, log=_real_log, create=True)
    with open(ffn_log_configuration, 'rt') as f:
        _log_settings = json.load(f)
    try:
        handler = _log_settings['handlers']['log-file']
    except KeyError:
        try:
            handler = next(iter_file_handlers(_log_settings))
        except StopIteration:
            return False
    handler['filename'] = os.path.join(metainfo.PATH_LOG, 'youtube-dl-gui.log')
    handler['level']    = logging.DEBUG
    with open(ffn_log_configuration, 'wt') as f:
        _real_log.info("writing log configuration file (enable logfile): {ffn}".format(ffn=ffn_log_configuration))
        f.write(json.dumps(_log_settings, indent=4, sort_keys=True))
    is_logfile_enabled = True
    return True

def set_enable_logfile(value):
    if value:
        enable_logfile()
    else:
        disable_logfile()
    assert is_logfile_enabled == bool(value)


# end log file at end of program
@atexit.register # gui.WindowMain.close is not called for example when program is closed via Keyboard Interrupt
def append_end_of_log_line():
    if os.path.isfile(ffn_log_file):
        _real_log.log(LEVEL_SENTINEL, _END_OF_LOG)


# a function to remove the log file which the controller can call if it wants to
def remove():
    os.remove(ffn_log_file)
    if len(os.listdir(_log_directory))==0:
        print("rmdir  {0!r}".format(_log_directory))
        os.rmdir(_log_directory)
