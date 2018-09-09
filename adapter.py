#!/usr/bin/env python
# standard libraries
import threading
try:
    import Queue as queue
except ImportError:
    import queue
import subprocess, os
import webbrowser
import datetime
import shlex
import sys
import logging
log = logging.getLogger(__name__)

# other libraries
import which_os_am_i_on as is_os
import settings_manager
settings = settings_manager.settings

TEST = False


class KEY:
    CMD = 'cmd'
    ENCODING = 'encoding'

class ProgramFinder(object):

    def __init__(self):
        if KEY.CMD in settings:
            cmd = settings[KEY.CMD]
        else:
            if is_os.windows():
                cmd = self._on_windows()
            elif is_os.linux():
                cmd = self._on_linux()
            elif is_os.mac():
                cmd = self._on_mac()
            else:
                raise ValueError("unknown operating system: "+is_os.os_name)
            settings.setdefault(KEY.CMD, cmd)
        self.cmd = cmd
    
    def _on_windows(self):
        return ['youtube-dl']
        #return ["C:\Users\zu Hause\Downloads\youtube-dl.exe"]
        programpath = self.get_youtubedl_path()
        return ['pythonw', '-u', programpath]

    def _on_linux(self):
        return ['youtube-dl']

    def _on_mac(self):
        return ['youtube-dl']
        raise NotImplemented

    def get_youtubedl_path(self):
        searched_folder_name = os.path.join("youtube-dl", "youtube_dl", "__main__.py")
        environment_variables = ("ProgramFiles", "ProgramFiles(x86)", "ProgramW6432")
        paths = list() # paths to search
        paths.append(os.path.split(__file__)[0])
        for var in environment_variables:
            path = os.environ[var]
            if path!=None and len(path)>0 and path not in paths:
                paths.append(path)
        
        for path in paths:
            trypath = os.path.join(path, searched_folder_name)
            if os.path.isfile(trypath):
                return trypath

    def get_cmd(self):
        return list(self.cmd)
    

def add_flag_if_given(cmd, params, key):
    if params.pop(key, False):
        cmd.append(key)

def add_value_if_given(cmd, params, key):
    val = params.pop(key, None)
    if val!=None:
        cmd.append(key)
        cmd.append(val)

if sys.version_info.major<=2:
    # not tested with unicode
    def split_options(string):
        if isinstance(string, unicode):
            #http://stackoverflow.com/a/11194593
            return [opt.decode('utf-8') for opt in shlex.split(string.encode('utf-8'))]
        elif isinstance(string, str):
            return shlex.split(string)
        else:
            raise TypeError("string should be either unicode or string, not {!r}.".format(type(string)))
else:
    split_options = shlex.split

class Adapter(object):

    MODE = 'mode'
    WORKING_DIRECTORY = 'working-dir'
    METAINFO_ONLY = '--dump-json'
    
    MODE_PLAYLIST = 'mode-playlist'
    MODE_SINGLE_VIDEO = 'mode-single-video'
    PLAYLIST_NO = '--no-playlist'
    PLAYLIST_YES = '--yes-playlist'
    SOURCE_URL = 'src-url'
    AUDIO_ONLY = '--extract-audio'
    AUDIO_FORMAT = '--audio-format'
    FLAG_KEEP_VIDEO = '--keep-video'
    ADDITIONAL_OPTIONS = 'additional-options'
    MARK_WATCHED = '--mark-watched'
    _NO_MARK_WATCHED = '--no-mark-watched'

    VIDEO_FORMAT = '--format'

    FLAG_WRITE_SUBTITLES = '--write-sub'
    FLAG_WRITE_SUBTITLES_AUTO_CREATED = '--write-auto-sub'
    FLAG_ALL_SUBTITLES = '--all-subs'
    SUBTITLE_LANGUAGES = '--sub-lang'
    SUBTITLE_FORMAT = '--sub-form'

    MODE_CUSTOM_COMMAND = 'mode-custom-cmd'
    ARGS = 'args'

    MODE_HELP = 'mode-help'
    MODE_VERSION = 'mode-version'

    FLAG_HELP = '--help'
    FLAG_VERSION = '--version'
    FLAG_UPDATE = '--update'

    FORMATS_AUDIO = ("best", "aac", "vorbis", "mp3", "m4a", "opus", "wav")
    FORMATS_VIDEO = ("mp4", "flv", "ogg", "webm", "mkv", "avi")

    STDOUT = 1
    STDERR = 2

    @classmethod
    def create_new_instance(cls):
        return cls()

    def __init__(self):
        self.program_finder = ProgramFinder()
        self.add_info = True
        self._proc = None

    def is_installed(self):
        self.set_command_print_version()
        try:
            return subprocess.call(self.cmd) == 0
        except FileNotFoundError:
            return False

    def start(self):
        self._queue = queue.Queue()
        cmd = self.cmd #self.process_params(params)
        if TEST: cmd[0] = os.path.join(os.path.split(__file__)[0], "test.py")
        if self.add_info:
            self._queue.put(("cmd: {}\n".format(cmd), self.STDOUT))
        else:
            log.info("cmd: {}".format(cmd))
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        def read_stream(queue, flag, stream):
            for ln in iter(lambda: self._read_line(stream), ''):
                queue.put((ln, flag))
        self._thread_stdout = threading.Thread(target=read_stream, args=[self._queue, self.STDOUT, self._proc.stdout])
        self._thread_stdout.daemon = True
        self._thread_stderr = threading.Thread(target=read_stream, args=[self._queue, self.STDERR, self._proc.stderr])
        self._thread_stderr.daemon = True
        
        self._thread_stderr.start()
        self._thread_stdout.start()

    @staticmethod
    def _read_line(stream):
        #TODO: relies on assumption that linesep is one character only
        #but I can't check whether there is another character to be interpreted
        #relies on assumption that '\r' is sent after update. is that true?
        seps = (b"\n", b"\r")
        line = bytearray()
        while line[-1:] not in seps:
            c = stream.read(1)
            if len(c)==0:
                return ""
            #sys.stdout.write(c)
            #sys.stdout.flush()
            line.extend(c)

        line = line.decode(settings.setdefault(KEY.ENCODING, 'utf-8'))
        return line

    def kill(self):
        self._proc.kill()

    def terminate(self):
        self._proc.terminate()

    def is_finished(self):
        return self._proc.poll()!=None

    def is_running(self):
        if self._proc==None:
            return False
        else:
            return not self.is_finished()

    def get_returncode(self):
        return self._proc.returncode

    def iter_out(self):
        '''iterate over all currently available (line, flag) pairs without blocking'''
        while not self._queue.empty():
            yield self._queue.get()


    def process_params(self, params):
        log.debug(params)
        cns = self # constants name space
        ons = self # options name space
        mode = params.pop(cns.MODE)
        self._handle_all_params = True
        if   mode==cns.MODE_SINGLE_VIDEO:
            cmd = self._process_params_single_video(params)
        elif mode==cns.MODE_CUSTOM_COMMAND:
            cmd = self._process_params_custom_command(params)
        elif mode==cns.MODE_PLAYLIST:
            cmd = self._process_params_playlist(params)
        else:
            raise ValueError("Invalid mode: %r" % (mode,))

        wd = params.pop(cns.WORKING_DIRECTORY)
        if wd != None:
            os.chdir(wd)
        
        #cmd = ['python', '-u', '/home/user/data/creation/source_code_python/youtube-dl-gui/test.py'] 
        self.cmd = cmd

        if self._handle_all_params:
            if len(params)>0:
                raise ValueError("unused arguments: " + ", ".join("%r: %r" % (key, params[key]) for key in params))

    def _process_params_single_video(self, params):
        cns = self # constants name space
        cmd = self._get_default_cmd()
        if params.pop(cns.METAINFO_ONLY, False):
            cmd.append(cns.METAINFO_ONLY)
            cmd.append(cns.PLAYLIST_NO)
            self.add_info = False
            self._handle_all_params = False
            params[cns.MARK_WATCHED] = False
        else:
            self.add_info = True
            params.setdefault(cns.MARK_WATCHED, True)
            # audio:
            if params.pop(cns.AUDIO_ONLY):
                cmd.append(cns.AUDIO_ONLY)
                add_value_if_given(cmd, params, cns.AUDIO_FORMAT)
                add_flag_if_given(cmd, params, cns.FLAG_KEEP_VIDEO)
            # video:
            add_value_if_given(cmd, params, cns.VIDEO_FORMAT)
            # subtitles:
            add_flag_if_given(cmd, params, cns.FLAG_WRITE_SUBTITLES)
            add_flag_if_given(cmd, params, cns.FLAG_WRITE_SUBTITLES_AUTO_CREATED)
            add_value_if_given(cmd, params, cns.SUBTITLE_FORMAT)
            add_value_if_given(cmd, params, cns.SUBTITLE_LANGUAGES)
            # playlist:
            opts = params.pop(cns.ADDITIONAL_OPTIONS, None)
            if not(opts and "playlist" in opts):
                cmd.append(cns.PLAYLIST_NO)
            # additional options:
            if opts:
                for opt in split_options(opts):
                    cmd.append(opt)

        cmd.append(cns.MARK_WATCHED if params.pop(cns.MARK_WATCHED) else cns._NO_MARK_WATCHED)
        source = params.pop(cns.SOURCE_URL)
        if len(source)==0:
            raise ValueError("no source url given")
        cmd.append(source)
        return cmd

    def _process_params_custom_command(self, params):
        cns = self # constants name space
        cmd = "youtube-dl "
        if params.pop(cns.METAINFO_ONLY, False):
            cmd += cns.METAINFO_ONLY + " "
        cmd += params.pop(cns.ARGS)
        return cmd

    def _process_params_playlist(self, params):
        raise NotImplemented

    def _get_default_cmd(self):
        return self.program_finder.get_cmd()

    def set_command_print_help(self):
        cmd = self._get_default_cmd()
        cmd.append(self.FLAG_HELP)
        self.cmd = cmd

    def set_command_print_version(self):
        cmd = self._get_default_cmd()
        cmd.append(self.FLAG_VERSION)
        self.cmd = cmd

    def set_command_update(self):
        cmd = self._get_default_cmd()
        cmd.append(self.FLAG_UPDATE)
        self.cmd = cmd


    @staticmethod
    def open_youtube():
        url = "https://www.youtube.com/"
        webbrowser.open_new(url)

    @staticmethod
    def parse_date(text):
        return datetime.datetime.strptime(text, '%Y%m%d')

    @classmethod
    def is_error(cls, line):
        return 'ERROR' in line
    @classmethod
    def is_warning(cls, line):
        return 'WARNING' in line

    _MSG_DESTINATION = 'Destination:'
    @classmethod
    def is_destination(cls, line, set_destination):
        i = line.find(cls._MSG_DESTINATION)
        if i>=0:
            i += len(cls._MSG_DESTINATION)
            set_destination(line[i:].strip())
            return True
        else:
            return False
        
        

if __name__=='__main__':
    import Tkinter as tk
    class GUI(tk.Tk):
        
        TAG_ERROR = 'error'

        POLL_INTERVAL_IN_MS = 100
        
        def __init__(self, adapter):
            tk.Tk.__init__(self)
            self.title("test")
            self.adapter = adapter
            
            self.text = tk.Text(self)
            self.text.pack(expand=True, fill=tk.BOTH)
            self.text.tag_configure(self.TAG_ERROR, background='#ff9f9f')
            
            frame = tk.Frame(self)
            frame.pack(side=tk.BOTTOM)
            self.button_start = tk.Button(frame, text='start', command=self.click_start)
            self.button_start.pack(side=tk.LEFT)
            self.button_kill = tk.Button(frame, text='kill', state=tk.DISABLED, command=self.click_kill)
            self.button_kill.pack(side=tk.LEFT)

        def click_start(self):
            adapter = self.adapter
            adapter.start()
            self._poll_read(adapter)
            self.button_kill.configure(state=tk.NORMAL)
            self.button_start.configure(state=tk.DISABLED)

        def click_kill(self):
            adapter = self.adapter
            self.kill_in(adapter, 2)

        def kill_in(self, adapter, deadline, listener=None):
            """ask subprocess to terminate and kill it in deadline seconds if it has not terminated by then."""
            self.after_cancel(self._after_id_poll_read)
            adapter.terminate() # tell the subprocess to exit

            # kill subprocess if it hasn't exited after a countdown
            def kill_after(countdown):
                if not adapter.is_finished():
                    countdown -= 1
                    if countdown < 0: # do kill
                        adapter.kill() # more likely to kill on *nix
                        notify = lambda: self.write_err("killed.\n")
                    else:
                        self._read(adapter)
                        self.after(self.POLL_INTERVAL_IN_MS, kill_after, countdown)
                        return # continue countdown
                else:
                    notify = lambda: self.write_err("terminated with returncode {}.\n".format(adapter.get_returncode()))
                self._read(adapter)
                notify()
                self.clean_up()
                if listener!=None:
                    listener()
            kill_after(countdown=int(deadline*1000/self.POLL_INTERVAL_IN_MS))

        def _read(self, adapter):
            for ln, flag in adapter.iter_out():
                if flag==adapter.STDOUT:
                    self.write_out(ln)
                else:
                    self.write_err(ln)

        def _poll_read(self, adapter):
            self._read(adapter)
            if adapter.is_finished():
                self._poll_finished(adapter)
            else:
                self._after_id_poll_read = self.after(self.POLL_INTERVAL_IN_MS, self._poll_read, adapter)

        def _poll_finished(self, adapter):
            returncode = adapter.get_returncode()
            self.clean_up()
            if returncode==0:
                self.write_out("finished.\n")
            else:
                self.write_err("finished with returncode {}.\n".format(returncode))

        def clean_up(self):
            self.button_start.configure(state=tk.NORMAL)
            self.button_kill.configure(state=tk.DISABLED)

        def write_out(self, msg):
            print(msg)
            self.text.insert(tk.END, msg)

        def write_err(self, msg):
            print("ERROR: "+msg)
            self.text.insert(tk.END, msg, (self.TAG_ERROR,))

    a = Adapter()
    a.cmd = ['python', 'test.py']
    g = GUI(a)
    g.mainloop()
