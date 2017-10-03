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
LEVEL_MAX = logging.CRITICAL*10
LEVEL_SENTINEL = logging.WARNING-1 # shall not be printed on stderr
logging.addLevelName(LEVEL_SENTINEL, 'SENTINEL')

FN_LOGGING_JSON = "logging.json"


# a function which I am missing in the logging library
def get_level_number(level):
    if isinstance(level, int):
        return level
    try:
        return int(level)
    except ValueError:
        return logging.getLevelName(level)


# "fake" logger because I can not log as long as the real logger is not setup
class DelayedLogger(object):
    def __init__(self):
        self.entries = list()
    def log(self, level, msg):
        self.entries.append((level, msg))
    def write(self, log):
        for level, msg in self.entries:
            log.log(level, msg)
        return log


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
                if logfile.END_LINE not in ln:
                    # log file is (most likely) in use by other currently running instance
                    return False
        return True


# read logging configuration file
def read_logging_configuration_file():
    ffn_log_configuration = metainfo.get_config_ffn(FN_LOGGING_JSON, log=_log)
    _log.log(logging.INFO, "log configuration file location: {ffn}".format(ffn=ffn_log_configuration))
    with open(ffn_log_configuration, 'rt') as f:
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
                _log.log(logging.INFO, "created directory for log file: {}".format(_log_directory))
        # make sure to not use the log file of another currently running instance
        ffn_log_file = UniqueFilenameCreator(ffn_log_file).create()
        _log_settings['handlers']['log-file']['filename'] = ffn_log_file
        _log.log(logging.DEBUG, "log file location: {}".format(ffn_log_file))
        # configure logging module
        logging.config.dictConfig(_log_settings)
        logfile.init(_log_settings)


# enable/disable log file in log settings (does not take effect until restart)
class LogFile(object):

    END_LINE = " end of log ".center(30, '=')

    @staticmethod
    def iter_file_handlers(_log_settings):
        handlers = _log_settings['handlers']
        for handler in handlers:
            handler = handlers[handler]
            if 'filename' in handler:
                yield handler

    def init(self, _log_settings):
        self._ffn = _log_settings['handlers']['log-file']['filename']
        
        for handler in self.iter_file_handlers(_log_settings):
            if get_level_number(handler['level']) <= LEVEL_MAX:
                self._is_enabled = True
                return
        self._is_enabled = False
        return

    def get_name(self):
        return self._ffn

    def get_directory(self):
        return os.path.split(self.get_name())[0]

    def is_enabled(self):
        return self._is_enabled
    
    def disable(self):
        if not self._is_enabled:
            return True
        ffn_log_configuration = metainfo.get_config_ffn(FN_LOGGING_JSON, log=_log, create=True)
        with open(ffn_log_configuration, 'rt') as f:
            _log_settings = json.load(f)
        for handler in self.iter_file_handlers(_log_settings):
            handler['filename'] = "/dev/null"
            handler['level']    = LEVEL_MAX+1
        with open(ffn_log_configuration, 'wt') as f:
            _log.log(logging.INFO, "writing log configuration file (disable logfile): {ffn}".format(ffn=ffn_log_configuration))
            f.write(json.dumps(_log_settings, indent=4, sort_keys=True))
        self._is_enabled = False
        return True

    def enable(self):
        if self._is_enabled:
            return True
        ffn_log_configuration = metainfo.get_config_ffn(FN_LOGGING_JSON, log=_log, create=True)
        with open(ffn_log_configuration, 'rt') as f:
            _log_settings = json.load(f)
        try:
            handler = _log_settings['handlers']['log-file']
        except KeyError:
            try:
                handler = next(self.iter_file_handlers(_log_settings))
            except StopIteration:
                return False
        handler['filename'] = os.path.join(metainfo.PATH_LOG, 'youtube-dl-gui.log')
        handler['level']    = logging.DEBUG
        with open(ffn_log_configuration, 'wt') as f:
            _log.log(logging.INFO, "writing log configuration file (enable logfile): {ffn}".format(ffn=ffn_log_configuration))
            f.write(json.dumps(_log_settings, indent=4, sort_keys=True))
        self._is_enabled = True
        return True

    def set_enable(self, value):
        if value:
            self.enable()
        else:
            self.disable()
        assert self._is_enabled == bool(value)


    def append_end_line(self):
        if os.path.isfile(self.get_name()):
            _log.log(LEVEL_SENTINEL, self.END_LINE)


    def remove(self):
        if not self._is_enabled:
            return
        os.remove(self.get_name())
        log_directory = self.get_directory()
        if len(os.listdir(log_directory))==0:
            print("rmdir  {0!r}".format(log_directory))
            os.rmdir(log_directory)


# execute
_log = DelayedLogger()
logfile = LogFile()
read_logging_configuration_file()
_log = _log.write(logging.getLogger(__name__))
atexit.register(logfile.append_end_line) # gui.WindowMain.close is not called for example when program is closed via Keyboard Interrupt
