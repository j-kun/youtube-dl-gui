#!/usr/bin/env python3
# ===== libraries =====
import logging_setup
log = logging_setup.getLogger(__name__)

# standard
try:
    # Python 2
    import Tkinter as tk
    import tkFileDialog
    import tkMessageBox
    import tkFont
    import ttk
except:
    # Python 3
    import tkinter as tk
    from tkinter import filedialog, messagebox, font
    tkFileDialog = filedialog
    tkMessageBox = messagebox
    tkFont = font
    from tkinter import ttk
import os, sys
try:
    from gi.repository import GLib
except ImportError:
    import os.path
import json
import time

# other
import locales
_ = locales._
import which_os_am_i_on
import open_directory
import tkinter_extensions as tkx
import tkinter_constants as tkc
import metainfo
import settings_manager
settings = settings_manager.settings

# ===== documentation =====
r"""
This is a graphical user interface for youtube-dl.
You can download youtub-dl from
http://youtube-dl.org/

Please keep in mind, that some of youtube-dl's features
depend on the libav project. If it is not already installed
you can download it for windows from:
http://builds.libav.org/windows/
(i.e. release-gpl/libav-11.3-win64.7z)
unzip it (i.e. with 7zip, http://www.7-zip.org/)
move it whereever you want (i.e. C:\Program Files)
and add libav\usr\bin to PATH variable
(Systemsteuerung > System und Sicherheit > System > Erweiterte Systemeinstellungen > Erweitert > Umgebungsvariablen...)
"""

# ===== ideas for improvement =====
#TODO: focus
#TODO: no permission to remove log on Windows (cause it's open?)
#      => disable log file by default
#TODO: what if logfile is disabled?
#TODO: tkx.SelectableLabel too small for kana

#TODO? filename (not really necessary, just click open and hit F2)
#TODO: direct support for playlists
#TODO: download available subtitle information and set menu accordingly
#TODO: tooltips for shortcuts
#TODO: padding based on https://developer.gnome.org/hig/stable/visual-layout.html.en
#TODO: option to save description
#TODO: Ctrl+f in help


# ===== constants =====
class KEY:
    # data
    DESTINATION_PATH = 'path-destination'
    AUDIO_FORMAT  = 'audio-format'
    AUDIO_FORMATS = 'audio-formats'
    EXTRACT_AUDIO = 'audio-extract'
    KEEP_VIDEO = 'video-keep'
    AUTO_PASTE_ON_STARTUP = 'startup-paste-clipboard-to-source-url'
    SHOW_DEBUG_MENU = 'debug-menu-enabled'
    VIDEO_FORMAT_EXPLICIT = 'video-format-explicit'
    VIDEO_FORMAT  = 'video-format'
    VIDEO_FORMATS = 'video-formats'
    SUBTITLES_FOR_VIDEO = 'subtitles'
    SUBTITLES_FOR_AUDIO = 'subtitles-for-audio-only'
    SUBTITLES_DEPEND_ON_AUDIO_ONLY = 'subtitles-depend-on-audio-only'
    SUBTITLE_LANGUAGES = 'subtitle-languages'
    SUBTITLE_LANGUAGES_AUTO_CREATED = 'subtitle-languages-auto-created'
    COPY_TO_CLIPBOARD_ON_STARTUP = 'startup-copy-to-clipboard'
    ADDITIONAL_OPTIONS = 'additional-options'
    ADDITIONAL_OPTIONS_ENABLED = 'additional-options-enabled'
    AUTO_REMOVE_LOG_AT_CLOSE = 'auto-remove-log-at-close'
    POLL_INTERVAL_IN_MS_FOR_METAINFO = 'poll-interval-for-metainfo-in-milli-seconds'
    POLL_INTERVAL_IN_MS_FOR_DOWNLOAD = 'poll-interval-for-download-in-milli-seconds'

    # geometry
    WIDTH_SOURCE_URL = 'width-source-url'
    WIDTH_WORKING_DIR = 'width-working-dir'
    WIDTH_CMD_ARGS = 'width-cmd-args'
    HEIGHT_CMD_ARGS = 'height-cmd-args'
    WIDTH_VIDEO_FORMAT = 'width-video-format'
    WIDTH_SUBTITLE_LANGUAGES = 'width-subtitle-languages'

    # internal
    CHECK_BACKEND = 'check-backend'


#TODO: move to other file. adapter?
def get_default_destination_directory(settings):
    path = settings.get(KEY.DESTINATION_PATH, None)
    if path not in (None, ""):
        if os.path.isdir(path):
            return path
    try:
        path = GLib.get_user_special_dir(GLib.USER_DIRECTORY_DESKTOP)
    except NameError:
        path = os.path.expanduser("~")
    settings[KEY.DESTINATION_PATH] = path
    return path


class Icon:
    _DIR = os.path.join(os.path.split(__file__)[0], "symbols")
    _EXT = '.xbm'
    BROWSE   = os.path.join(_DIR, "browse_thick"+_EXT)
    PASTE    = os.path.join(_DIR, "paste_thick"+_EXT)
    LIKE     = os.path.join(_DIR, "like_thin"+_EXT)
    DISLIKE  = os.path.join(_DIR, "dislike_thin"+_EXT)
    RATING   = os.path.join(_DIR, "rating_empty"+_EXT)
    COUNT    = os.path.join(_DIR, "count2"+_EXT)
    DOWNLOAD = os.path.join(_DIR, "download"+_EXT)

FN_SHORTCUTS = 'shortcuts.py'


# ===== general context menus =====
class CONTEXT_MENU:
    ID_COPY = 'copy'
    LABEL_COPY = _('copy')

    ID_PASTE = 'paste'
    LABEL_PASTE = _('paste')

def on_contextmenu_open(self):
    self.contextmenu.set_entry_enabled(CONTEXT_MENU.ID_COPY, self.selection_present())
    self.contextmenu.set_entry_enabled(CONTEXT_MENU.ID_PASTE, self.can_paste())

tkx.ScrolledText.default_contextmenu = (
    (CONTEXT_MENU.ID_COPY, CONTEXT_MENU.LABEL_COPY, tkx.ScrolledText.text_copy_selection),
    (CONTEXT_MENU.ID_PASTE, CONTEXT_MENU.LABEL_PASTE, tkx.ScrolledText.text_paste)
)
tkx.ScrolledText.default_on_contextmenu_open = on_contextmenu_open
tkx.ScrolledText.default_on_readonly_enabled = lambda self: self.contextmenu.entry_disable(CONTEXT_MENU.ID_PASTE)
tkx.ScrolledText.default_on_readonly_disabled = lambda self: self.contextmenu.set_entry_enabled(CONTEXT_MENU.ID_PASTE, self.can_paste())

tkx.AutoScrolledText.default_contextmenu = (
    (CONTEXT_MENU.ID_COPY, CONTEXT_MENU.LABEL_COPY, tkx.AutoScrolledText.text_copy_selection),
    (CONTEXT_MENU.ID_PASTE, CONTEXT_MENU.LABEL_PASTE, tkx.AutoScrolledText.text_paste)
)
tkx.AutoScrolledText.default_on_contextmenu_open = on_contextmenu_open
tkx.AutoScrolledText.default_on_readonly_enabled = lambda self: self.contextmenu.entry_disable(CONTEXT_MENU.ID_PASTE)
tkx.AutoScrolledText.default_on_readonly_disabled = lambda self: self.contextmenu.set_entry_enabled(CONTEXT_MENU.ID_PASTE, self.can_paste())

tkx.Entry.default_contextmenu = (
    (CONTEXT_MENU.ID_COPY, CONTEXT_MENU.LABEL_COPY, tkx.Entry.text_copy_selection),
    (CONTEXT_MENU.ID_PASTE, CONTEXT_MENU.LABEL_PASTE, tkx.Entry.text_paste)
)
tkx.Entry.default_on_contextmenu_open = on_contextmenu_open

tkx.LabelSelectable.default_contextmenu = (
    (CONTEXT_MENU.ID_COPY, CONTEXT_MENU.LABEL_COPY, tkx.LabelSelectable.text_copy_selection),
)
tkx.LabelSelectable.default_on_contextmenu_open = lambda self: self.contextmenu.set_entry_enabled(CONTEXT_MENU.ID_COPY, self.selection_present())


# ===== main window =====
class WindowMain(tk.Tk):

    STATE_UNCHECKED = "unchecked"
    STATE_SUCCESS = "successful"
    STATE_ERROR = "error"

    class ApplicationMenus(tkx.Menu):
        def __init__(self, root):
            tkx.Menu.__init__(self, root)
            root.configure(menu=self)

            m = self.add_named_cascade("backend", label=_("youtube-dl"))
            m.add_named_command("version", label=_("version"), command=root.open_window_cli_version)
            m.add_named_command("update", label=_("update"), command=root.perform_update)
            m.add_named_command("help", label=_("help"), command=root.open_window_cli_help)

            m = self.add_named_cascade("frontend", label=_("frontend"))
            m.add_named_command("save_settings", label=_("save settings"), command=lambda: root.save_settings(force=True))
            m.add_named_command("edit_settings", label=_("edit settings"), command=root.open_settings)
            m.add_named_command("edit_shortcuts", label=_("edit shortcuts"), command=lambda: open_directory.open_file(metainfo.get_config_ffn(FN_SHORTCUTS, create=True)))
            m.add_named_command("reload_settings", label=_("reload settings"), command=root.reload_settings)
            def cmd_update_settings(value):
                old_value = settings[settings_manager.KEY.UPDATE_SETTINGS]
                settings[settings_manager.KEY.UPDATE_SETTINGS] = value
                #TODO: do I really want this to behave different from auto_remove_log? That checkbox is not saved when changed.
                if old_value!=value:
                    #if tkMessageBox.askyesno(_("Save Settings?"), _("You have disabled auto save settings. If you do not save the settings explicitly this setting will not be remembered. Do you want to save the settings now?")):
                    settings_manager.save_settings(
                        settings=settings,
                        force=True,
                        ask_overwrite_handler=lambda: tkMessageBox.askyesno(
                            title=_("Save Settings?"),
                            message=_("You have opened the settings in an external editor. If you have changed the settings there and proceed those changes will be overwritten. Do you want to save disabling auto save settings?"),
                            default=tkMessageBox.NO,
                            icon=tkMessageBox.WARNING,
                        )
                    )
            m.add_named_command("reset_settings", label=_("reset settings..."), command=lambda: WindowResetSettings(root))
            m.add_named_checkbutton("update_settings", label=_("auto save settings"), command=cmd_update_settings)
            
            
##            m = self.add_named_cascade("language", label=_("language"))
##            m.add_named_command("en", label=_("English"))
##            m.add_named_command("de", label=_("Deutsch"))
##            self.menu_language.entry_disable("en")
##            self.menu_language.entry_disable("de")
            
            m = self.add_named_cascade("debug", label=_("debug"), visible=False)
            m.add_named_command("save_metainfo", label=_("save metainfo"), command=lambda: root.save_metainfo(raw=False), state=tkc.STATE_DISABLED)
            m.add_named_command("save_raw_metainfo", label=_("save raw metainfo"), command=lambda: root.save_metainfo(raw=True))
            m.add_separator()
            m.add_named_checkbutton("enable_log_file", label=_("write log file"), command=logging_setup.logfile.set_enable, value=logging_setup.logfile.is_enabled())
            m.add_named_checkbutton("auto_remove_log", label=_("auto remove log"), command=lambda value: settings.__setitem__(KEY.AUTO_REMOVE_LOG_AT_CLOSE,value))
            m.add_named_command("open_log_settings", label=_("open log file settings"), command=lambda: open_directory.open_file(metainfo.get_config_ffn(logging_setup.FN_LOGGING_JSON, create=True)))
            m.add_named_command("open_log", label=_("open log file"), command=lambda: open_directory.open_file(logging_setup.logfile.get_name()))
            m.add_named_command("save_log_as", label=_("save log as ..."), command=root.save_log_as)
        

    class FrameMain(tk.Frame):
        
        def __init__(self, master):
            tk.Frame.__init__(self, master)
            self.root = master
            root = self

            self.var_working_directory = tk.StringVar()

            # search youtube
            frame = root
            self.button_search_youtube = tk.Button(frame, command = self.root.adapter.open_youtube)
            self.button_search_youtube.pack()

            # tabs
            self.tabs = ttk.Notebook(root)
            self.tabs.pack(expand=True, fill=tk.BOTH)

            # ----- tab: single video -----
            tab = tk.Frame(self.tabs)
            self.tabs.add(tab)
            self.tab_single_video = tab


            frame = tk.Frame(tab)
            frame.pack(fill=tk.X) #(expand=True, fill=tk.BOTH)

            # input source
            row = 0
            col = 0
            self.label_source = tk.Label(frame)
            self.label_source.grid(row=row, column=col, sticky=tk.W)
            col += 1
            
            self.entry_source = tkx.Entry(frame)
            self.entry_source.bind("<Return>", self.update_metainfo)
            self.entry_source.var = tk.StringVar()
            self.entry_source.config(textvariable=self.entry_source.var)
            self.entry_source.var.trace('w', lambda a,b,c: self.root.invalidate_meta_info())
            self.entry_source.grid(row=row, column=col, sticky=tk.W+tk.E)
            tk.Grid.columnconfigure(frame, col, weight=1)
            col += 1

            self.button_source_clear_and_paste = tkx.Button(frame, command=self.source_clear_and_paste, imagepath=Icon.PASTE)
            #self.button_source_clear_and_paste[tkc.TEXT] = "p"
            self.button_source_clear_and_paste.grid(row=row, column=col)
            tkx.add_tooltip(self.button_source_clear_and_paste)
            col += 1

            # input working directory
            row += 1
            col = 0
            self.label_dest_dir = tk.Label(frame)
            self.label_dest_dir.grid(row=row, column=col, sticky=tk.W)
            col += 1
            
            self.entry_dest_dir = tkx.Entry(frame, textvariable=self.var_working_directory)
            self.entry_dest_dir.grid(row=row, column=col, sticky=tk.W+tk.E)
            col += 1

            self.button_dest_dir_search = tkx.Button(frame, command=self.dest_select_directory, imagepath=Icon.BROWSE)
            #self.button_dest_dir_search[tkc.TEXT] = "s"
            self.button_dest_dir_search.grid(row=row, column=col)
            tkx.add_tooltip(self.button_dest_dir_search)
            col += 1

            # audio, video & subtitles
            frame = tk.Frame(tab)
            frame.pack(fill=tk.X)
            # checkbox audio only
            frame_ver = tk.Frame(frame)
            frame_ver.pack(side=tk.LEFT, anchor=tk.N)
            frame_hor = tk.Frame(frame_ver)
            frame_hor.pack(fill=tk.X)

            self.checkbox_audio_only = tkx.Checkbutton(frame_hor, command=self.update_video_enable)
            self.checkbox_audio_only.pack(side=tk.LEFT)

            self.label_audio_format = tk.Label(frame_hor)
            self.label_audio_format.pack(side=tk.LEFT)

            self.menubtn_format_audio = tkx.Menubutton(frame_hor)
            self.menubtn_format_audio.pack(side=tk.LEFT)
            self.checkbox_audio_only.add_slave(self.menubtn_format_audio)

            frame_hor = tk.Frame(frame_ver)
            frame_hor.pack(fill=tk.X)
            tkx.Indentation(frame_hor).pack(side=tk.LEFT)
            self.checkbox_keep_video = tkx.Checkbutton(frame_hor, command=self.update_video_enable)
            self.checkbox_keep_video.pack(side=tk.LEFT)
            self.checkbox_audio_only.add_slave(self.checkbox_keep_video)

            # video format
            frame_hor = tk.Frame(frame_ver)
            frame_hor.pack(anchor=tk.W, fill=tk.X)
            self.checkbox_video_format = tkx.Checkbutton(frame_hor)
            self.checkbox_video_format.pack(side=tk.LEFT)
            self.menubtn_video_format = tkx.Menubutton(frame_hor)
            self.menubtn_video_format.pack(side=tk.LEFT, fill=tk.X)
            self.checkbox_video_format.add_slave(self.menubtn_video_format)

            tk.Frame(frame, width=12).pack(side=tk.LEFT)

            # subtitles
            self.SUBTITLES_OFF = 'off'
            self.SUBTITLES_ON = 'write'
            self.SUBTITLES_AUTO_CREATED = 'write-auto-created'
            self.var_subtitles_for_video = tk.StringVar()
            self.var_subtitles_for_video.trace(tkc.TRACE_WRITE, self.update_subtitle_language_enable)
    
            frame_grid = tk.Frame(frame)
            frame_grid.pack(side=tk.LEFT, anchor=tk.N, fill=tk.X)
            # (off)
            self.radiobox_subtitles_off = ttk.Radiobutton(frame_grid, value=self.SUBTITLES_OFF)
            self.radiobox_subtitles_off.grid(row=0, column=0, sticky=tk.W)
            # (on)
            self.radiobox_subtitles_on  = ttk.Radiobutton(frame_grid, value=self.SUBTITLES_ON)
            self.radiobox_subtitles_on.grid(row=1, column=0, sticky=tk.W)
            self.entry_subtitle_languages = tkx.Entry(frame_grid)
            self.entry_subtitle_languages.grid(row=1, column=1, sticky=tk.W)
            # (auto-created)
            self.radiobox_subtitles_auto_created  = ttk.Radiobutton(frame_grid, value=self.SUBTITLES_AUTO_CREATED)
            self.radiobox_subtitles_auto_created.grid(row=2, column=0, sticky=tk.W)
            self.entry_subtitle_languages_auto_created = tkx.Entry(frame_grid)
            self.entry_subtitle_languages_auto_created.grid(row=2, column=1, sticky=tk.W)

            # additional command line options
            self.frame_cl_options = tkx.DetailsFrame(tab)
            self.frame_cl_options.pack(anchor=tk.W, fill=tk.X)
            self.entry_cl_options = tkx.Entry(self.frame_cl_options) #TODO: typewriter
            self.entry_cl_options.pack(anchor=tk.W, expand=True, fill=tk.X)

            # info frame
            row += 1
            self.frame_info = self.FrameInfo(tab, self.root)
            self.frame_info.pack(expand=True, fill=tk.BOTH)
            #self.frame_info.grid(row=row, column=0, columnspan=col, sticky=tk.W+tk.N+tk.E+tk.S)
            #frame.rowconfigure(row, weight=1)


            # ----- tab: custom command -----
            tab = ttk.Frame(self.tabs)
            self.tabs.add(tab)
            self.tab_custom_command = tab

            # working directory
            frame = tk.Frame(tab)
            frame.pack(fill=tk.X)
            
            self.label_working_dir = tk.Label(frame)
            self.label_working_dir.pack(side = tk.LEFT)
            
            self.entry_working_dir = tkx.Entry(frame, textvariable=self.var_working_directory)
            self.entry_working_dir.pack(side=tk.LEFT, expand=True, fill=tk.X)

            self.button_working_dir_search = tkx.Button(frame, command=self.dest_select_directory, imagepath=Icon.BROWSE)
            #self.button_working_dir_search[tkc.TEXT] = "s"
            self.button_working_dir_search.pack(side=tk.RIGHT)
            tkx.add_tooltip(self.button_working_dir_search)

            # input source
            frame = tk.Frame(tab)
            frame.pack(expand=True, fill=tk.BOTH)
            
            self.label_command_name = tk.Label(frame)
            self.label_command_name.pack(side=tk.LEFT, anchor=tk.N)
            # name of command is language independent I guess...
            self.label_command_name[tkc.TEXT] = "youtube-dl "
            
            self.text_command_arguments = tkx.ScrolledText(frame)
            self.text_command_arguments.pack(expand=True, fill=tk.BOTH)

            # help buttons
            frame = tk.Frame(tab)
            frame.pack()#(expand=True, fill=tk.X)

            self.button_man_pages = tk.Button(frame, command=self.root.open_window_cli_help)
            tkx.add_tooltip(self.button_man_pages)
            self.button_copy = tk.Button(frame)
            self.button_paste = tk.Button(frame)
            
            self.button_man_pages.pack(side=tk.LEFT)
            self.button_copy.pack(side=tk.LEFT)
            self.button_paste.pack(side=tk.LEFT)
            

            # ----- buttons -----
            frame = tkx.ButtonsFrame(root,
                ok = dict(command=self.root.download, imagepath=Icon.DOWNLOAD, compound=tk.LEFT),
                cancel = dict(command=self.root.close),
            )
            frame.pack(fill=tk.X)
            self.button_download = frame.button_ok
            self.button_close    = frame.button_cancel

            # update_labels is handled by root
            # update_settings is handled by root


        def update_settings(self):
            WIDTH_SOURCE      = settings.setdefault(KEY.WIDTH_SOURCE_URL, 50) #43
            WIDTH_WORKING_DIR = settings.setdefault(KEY.WIDTH_WORKING_DIR, 40) #30
            WIDTH_CMD_ARGS    = settings.setdefault(KEY.WIDTH_CMD_ARGS, WIDTH_SOURCE)
            HEIGHT_CMD_ARGS   = settings.setdefault(KEY.HEIGHT_CMD_ARGS, 3)
            WIDTH_SUBTITLE_LANGUAGES = settings.setdefault(KEY.WIDTH_SUBTITLE_LANGUAGES, 15)

            self.var_working_directory.set(get_default_destination_directory(settings))

            menus = self.root.menus
            menus.menu_frontend.set_named_checkbutton('update_settings', value=settings.setdefault(settings_manager.KEY.UPDATE_SETTINGS, False))
            menus.menu_debug.set_named_checkbutton('auto_remove_log', value=settings.setdefault(KEY.AUTO_REMOVE_LOG_AT_CLOSE, True))

            # ----- tab: single video -----
            self.entry_source.configure(width=WIDTH_SOURCE)
            self.entry_dest_dir.configure(width=WIDTH_WORKING_DIR)

            if settings.setdefault(KEY.SUBTITLES_DEPEND_ON_AUDIO_ONLY, False):
                if not hasattr(self, 'var_subtitles_for_audio'):
                    self.var_subtitles_for_audio = tk.StringVar()
                    self.var_subtitles_for_audio.trace(tkc.TRACE_WRITE, self.update_subtitle_language_enable)
                self.var_subtitles_for_audio.set(settings.setdefault(KEY.SUBTITLES_FOR_AUDIO, self.SUBTITLES_OFF))

            self.checkbox_audio_only.set_value(settings.setdefault(KEY.EXTRACT_AUDIO, False))
            self.set_menu_values(self.menubtn_format_audio, settings, KEY.AUDIO_FORMATS, self.root.adapter.FORMATS_AUDIO, KEY.AUDIO_FORMAT, "mp3")
            self.checkbox_keep_video.set_value(settings.setdefault(KEY.KEEP_VIDEO, False))
            self.checkbox_video_format.set_value(settings.setdefault(KEY.VIDEO_FORMAT_EXPLICIT, False))

            WIDTH_VIDEO_FORMAT = settings.setdefault(KEY.WIDTH_VIDEO_FORMAT, len(max(settings.setdefault(KEY.VIDEO_FORMATS, self.root.adapter.FORMATS_VIDEO), key=len))+1)
            self.menubtn_video_format.configure(width=WIDTH_VIDEO_FORMAT)
            self.set_menu_values(self.menubtn_video_format, settings, KEY.VIDEO_FORMATS, self.root.adapter.FORMATS_VIDEO, KEY.VIDEO_FORMAT, "mp4")

            self.var_subtitles_for_video.set(settings.setdefault(KEY.SUBTITLES_FOR_VIDEO, self.SUBTITLES_OFF))
            self.entry_subtitle_languages.configure(width=WIDTH_SUBTITLE_LANGUAGES)
            self.entry_subtitle_languages.set_value(settings.setdefault(KEY.SUBTITLE_LANGUAGES, 'en,de'), force=True)
            self.entry_subtitle_languages_auto_created.configure(width=WIDTH_SUBTITLE_LANGUAGES)
            self.entry_subtitle_languages_auto_created.set_value(settings.setdefault(KEY.SUBTITLE_LANGUAGES_AUTO_CREATED, 'en'), force=True)
            self.frame_cl_options.set_expanded(settings.setdefault(KEY.ADDITIONAL_OPTIONS_ENABLED, False))
            self.entry_cl_options.set_value(settings.setdefault(KEY.ADDITIONAL_OPTIONS, ""))

            # ----- tab: custom command -----
            self.entry_working_dir.configure(width=WIDTH_WORKING_DIR)
            self.text_command_arguments.configure(width=WIDTH_CMD_ARGS, height=HEIGHT_CMD_ARGS)


        @staticmethod
        def set_menu_values(menu, settings, list_key, list_default_values, value_key, value_default_value):
            values  = settings.setdefault(list_key, list_default_values)
            if values==None or len(values)==0:
                log.warning("no values are allowed for {key}.".format(key=value_key))
                menu.set_values([])
                return
            default = settings.setdefault(value_key, value_default_value)
            if default not in values:
                new_default = value_default_value if value_default_value in values else values[0]
                log.error("saved default value {default!r} for key {key} is not in allowed values {values}. Using {new_default!r} instead.".format(key=value_key, default=default, new_default=new_default, values=values))
                default = new_default
            menu.set_values(values)
            menu.set_value(default)
            

        def update_labels(self):
            # tabs
            self.tabs.tab(self.tab_single_video, text=_("single video"))
            self.tabs.tab(self.tab_custom_command, text=_("custom command"))

            # tab: single video
            self.label_source[tkc.TEXT] = _("source URL") + ":"
            self.label_dest_dir[tkc.TEXT] = _("destination directory") + ":"
            self.checkbox_audio_only[tkc.TEXT] = _("extract audio")
            self.label_audio_format[tkc.TEXT] = _("to format:")
            self.checkbox_keep_video[tkc.TEXT] = _("keep video file")
            self.checkbox_video_format[tkc.TEXT] = _("explicit video format") + ":"
            self.radiobox_subtitles_off[tkc.TEXT] = _("no subtitles")
            self.radiobox_subtitles_on[tkc.TEXT] = _("subtitles") + ":"
            self.radiobox_subtitles_auto_created[tkc.TEXT] = _("auto created subtitles") + ":"
            self.button_source_clear_and_paste.tooltip[tkc.TEXT] = _("clear & paste")
            self.button_dest_dir_search.tooltip[tkc.TEXT] = _("browse for output directory")
            self.frame_cl_options.configure(label=_("Additional command line options:"), label_expand=_("Specify additional command line options"))
            self.frame_info.update_labels()

            # tab: custom command
            self.label_working_dir[tkc.TEXT] = _("working direcotry")
            self.button_man_pages[tkc.TEXT] = _("man")
            self.button_man_pages.tooltip[tkc.TEXT] = _("youtube-dl --help")
            self.button_copy[tkc.TEXT] = _("copy")
            self.button_paste[tkc.TEXT] = _("paste")
            self.button_working_dir_search.tooltip[tkc.TEXT] = _("browse for working directory")

            # global buttons
            self.button_search_youtube[tkc.TEXT] = _("open youtube")
            #self.button_info[tkc.TEXT] = _("show info")
            self.button_download[tkc.TEXT] = _("download")
            self.button_close[tkc.TEXT] = _("close")

        def update_metainfo(self, event=None):
            self.root.update_metainfo()

        def get_subtitles_var(self):
            if settings[KEY.SUBTITLES_DEPEND_ON_AUDIO_ONLY]:
                return self.var_subtitles_for_video if tkx.is_enabled(self.checkbox_video_format) else self.var_subtitles_for_audio
            else:
                return self.var_subtitles_for_video

        def update_video_enable(self, event=None):
            enabled = not self.checkbox_audio_only.get_value() or self.checkbox_keep_video.get_value()
            enabled_menu = enabled and self.checkbox_video_format.get_value()
            tkx.set_enabled(self.checkbox_video_format, enabled)
            tkx.set_enabled(self.menubtn_video_format, enabled_menu)
            # subtitles:
            var = self.get_subtitles_var()
            self.radiobox_subtitles_off.config(variable=var)
            self.radiobox_subtitles_on.config(variable=var)
            self.radiobox_subtitles_auto_created.config(variable=var)
            self.update_subtitle_language_enable()

        # http://stackoverflow.com/a/29697307
        def update_subtitle_language_enable(self, varname=None, index=None, operation=None):
            val = self.get_subtitles_var().get()
            tkx.set_enabled(self.entry_subtitle_languages, val==self.SUBTITLES_ON)
            tkx.set_enabled(self.entry_subtitle_languages_auto_created, val==self.SUBTITLES_AUTO_CREATED)

        def get_settings(self):
            cns = self.root.adapter  # constants name space
            out = dict()
            active_tab = self.tabs.nametowidget(self.tabs.select())
            if   active_tab==self.tab_single_video:
                out[cns.MODE] = cns.MODE_SINGLE_VIDEO
                out[cns.SOURCE_URL] = tkx.get_text(self.entry_source)
                out[cns.WORKING_DIRECTORY] = tkx.get_text(self.var_working_directory)
                out[cns.AUDIO_ONLY] = self.checkbox_audio_only.get_value()
                if tkx.is_enabled(self.menubtn_format_audio):
                    out[cns.AUDIO_FORMAT] = self.menubtn_format_audio.get_value()
                if tkx.is_enabled(self.checkbox_keep_video):
                    out[cns.FLAG_KEEP_VIDEO] = self.checkbox_keep_video.get_value()
                if tkx.is_enabled(self.checkbox_video_format) and self.checkbox_video_format.get_value():
                    out[cns.VIDEO_FORMAT] = self.menubtn_video_format.get_value()
                if self.get_subtitles_var().get()==self.SUBTITLES_ON:
                    out[cns.FLAG_WRITE_SUBTITLES] = True
                    out[cns.SUBTITLE_LANGUAGES] = tkx.get_text(self.entry_subtitle_languages)
                if self.get_subtitles_var().get()==self.SUBTITLES_AUTO_CREATED:
                    out[cns.FLAG_WRITE_SUBTITLES_AUTO_CREATED] = True
                    out[cns.SUBTITLE_LANGUAGES] = tkx.get_text(self.entry_subtitle_languages_auto_created)
                if self.frame_cl_options.is_expanded():
                    out[cns.ADDITIONAL_OPTIONS] = self.entry_cl_options.get_value()
                
            elif active_tab==self.tab_custom_command:
                out[cns.MODE] = cns.MODE_CUSTOM_COMMAND
                out[cns.ARGS] = tkx.get_text(self.text_command_arguments)
                out[cns.WORKING_DIRECTORY] = tkx.get_text(self.var_working_directory)
            return out


        # local event listener
        def source_clear_and_paste(self, event=None, precheck=False):
            url = self.root.get_clipboard_content()
            if precheck:
                URL_START = "https://www.youtube.com/"
                if url[:len(URL_START)]!=URL_START:
                    return
            tkx.set_text(self.entry_source, url)
            self.entry_source.update()
            self.update_metainfo()

        def dest_select_directory(self, event=None):
            directory = tkFileDialog.askdirectory(
                title = _("Choose Destination Directory"),
                initialdir = tkx.get_text(self.var_working_directory),
                #TODO: consider mustexist
                #TODO: consider parent
            )
            tkx.set_text(self.var_working_directory, directory)

        # setters
        def mark_source_url(self, state):
            if state==self.root.STATE_UNCHECKED:
                color = "#FFFFFF"
                widget_to_be_focused = None
            elif state==self.root.STATE_SUCCESS:
                color = "#cffbca"
                widget_to_be_focused = self.button_download
            elif state==self.root.STATE_ERROR:
                color = "#ff6363"
                widget_to_be_focused = self.entry_source
            self.entry_source[tkc.COLOR_BACKGROUND] = color
            if widget_to_be_focused!=None:
                widget_to_be_focused.focus_set()

        class FrameInfo(tkx.HideableFrame):
            def __init__(self, master, root):
                tk.Frame.__init__(self, master)
                self.root = root
                
                self.labelframe = frame = ttk.LabelFrame(self, text=_("metainfo"))
                frame.pack(expand=True, fill=tk.BOTH)

                frame_upload = tk.Frame(frame)
                frame_numbers = tk.Frame(frame)
                
                self.label_title = tk.Label(frame)
                self.label_uploader = tk.Label(frame)
                self.label_description = tk.Label(frame)

                self.widgets = widgets = dict()
                TextBox = tkx.LabelSelectable
                cnf = dict()
                widgets['title'] = TextBox(frame, **cnf)
                widgets['uploader'] = TextBox(frame_upload, **cnf)
                widgets['description'] = tkx.ScrolledText(frame, bg=None, height=5, readonly=True, **cnf)
                widgets['upload_date'] = tkx.LabelSelectable(frame_upload, justify=tk.RIGHT, **cnf)
                TextBox = tkx.LabelSelectableWithLabel
                widgets['duration'] = TextBox(frame, **cnf)
                widgets['view_count'] = TextBox(frame_numbers, imagepath=Icon.COUNT, justify=tk.RIGHT, **cnf)
                widgets['like_count'] = TextBox(frame_numbers, imagepath=Icon.LIKE, **cnf)
                widgets['dislike_count'] = TextBox(frame_numbers, imagepath=Icon.DISLIKE, **cnf)
                widgets['average_rating'] = TextBox(frame_numbers, imagepath=Icon.RATING, **cnf)

                for key in ('like_count', 'dislike_count', 'average_rating', 'view_count'):
                    tkx.add_tooltip(widgets[key].frame)
                    widgets[key].tooltip = widgets[key].frame.tooltip
                tkx.add_tooltip(widgets['upload_date'])

                frame.columnconfigure(0, pad=1)
                frame.columnconfigure(1, weight=1)
                labelkw = dict(sticky=tk.W+tk.N)
                valuekw = dict(sticky=tk.W+tk.N+tk.E)
                row=0
                self.label_title.grid(column=0, row=row, **labelkw)
                widgets['title'].grid(column=1, row=row, **valuekw)
                row += 1

                self.label_uploader.grid(column=0, row=row, **labelkw)
                frame_upload.grid(column=1, row=row, **valuekw)
                widgets['uploader'].pack(side=tk.LEFT, fill=tk.X)
                #tk.Label(frame_upload, text=')').pack(side=tk.RIGHT)
                widgets['upload_date'].pack(side=tk.RIGHT)
                #tk.Label(frame_upload, text='(').pack(side=tk.RIGHT)
                row += 1

                cnf_stretch = dict(side=tk.LEFT, expand = True, fill=tk.X)
                cnf = dict(side=tk.LEFT)
                #tkx.Stretch(frame_numbers).pack(**cnf_stretch)
                widgets['like_count'].pack(**cnf)
                #tkx.Stretch(frame_numbers).pack(**cnf_stretch)
                tk.Label(frame_numbers, text=" / ").pack(**cnf)
                widgets['dislike_count'].pack(**cnf)
                tkx.Stretch(frame_numbers).pack(**cnf_stretch)
                widgets['average_rating'].pack(**cnf)
                tkx.Stretch(frame_numbers).pack(**cnf_stretch)
                widgets['view_count'].pack(**cnf)
                #tkx.Stretch(frame_numbers).pack(**cnf_stretch)
                frame_numbers.grid(column=1, row=row, sticky=tk.W+tk.E)
                row += 1

                self.label_description.grid(column=0, row=row, **labelkw)
                widgets['description'].grid(column=1, row=row, sticky=tkc.W+tkc.N+tkc.E+tkc.S)
                frame.rowconfigure(row, weight=1)
                row += 1


            def update_labels(self):
                self.label_title[tkc.TEXT] = _("title")
                self.label_uploader[tkc.TEXT] = _("uploaded by")
                self.label_description[tkc.TEXT] = _("description")

                self._update_label_and_tooltip('upload_date', _("upload date"))
                self._update_label_and_tooltip('like_count', _("likes"))
                self._update_label_and_tooltip('dislike_count', _("dislikes"))
                self._update_label_and_tooltip('average_rating', _("rating"))
                self._update_label_and_tooltip('view_count', _("view count"))
                

            def _update_label_and_tooltip(self, widgetkey, text, sep=":"):
                widget = self.widgets[widgetkey]
                try:
                    widget.tooltip[tkc.TEXT] = text
                except AttributeError:
                    pass
                try:
                    widget.label[tkc.TEXT] = text + sep
                except AttributeError:
                    pass
                

            def update_info(self, metainfo):
                KEYS_DATE = ('upload_date',)
                KEYS_INT = ('view_count', 'like_count', 'dislike_count')
                KEYS_FLOAT = ('average_rating',)
                for key in self.widgets:
                    w = self.widgets[key]
                    val = metainfo.get(key, None)
                    if val != None:
                        if key in KEYS_DATE:
                            val = locales.format_date(self.root.adapter.parse_date(val))
                            if key=='upload_date':
                                val = '('+val+')'
                        elif key in KEYS_INT:
                            val = locales.format_int(int(val))
                        elif key in KEYS_FLOAT:
                            val = locales.format_float(float(val))
                        tkx.set_text(w, val)
                    else:
                        log.warning("no meta info for field {key}".format(key=key))
                        tkx.set_text(w, "")
                    
            

    class FrameLog(tk.Frame):
        TAG_WARNING = 'warning'
        TAG_ERROR = 'error'
        TAG_DESTINATION = 'destination'
        TAG_FINISHED = 'finished'
        def __init__(self, master):
            tk.Frame.__init__(self, master)
            self.root = master
            root = self
            frame = root

            self.text_log = tkx.AutoScrolledText(frame, wrap=tk.WORD, readonly=True, height=5)
            self.text_log.pack(expand=True, fill=tk.BOTH)
            self.text_log.tag_configure(self.TAG_WARNING, background='#ffff64')
            self.text_log.tag_configure(self.TAG_ERROR, background='#ff9f9f')
            self.text_log.tag_configure(self.TAG_DESTINATION, background='#caffca')
            font = tkFont.Font(self.text_log, font=self.text_log[tkc.FONT])
            font.configure(weight=tkc.FONT_WEIGHT_BOLD)
            self.text_log.tag_configure(self.TAG_FINISHED, font=font)

            frame = tk.Frame(root)
            frame.pack(side=tk.BOTTOM)
            self.button_cancel = tk.Button(frame, command=self.root.cancel_download)
            self.button_close = tk.Button(frame, command=self.root.close)
            self.button_back = tk.Button(frame, command=lambda: self.root.switch_to_frame(self.root.frame_main))
            self.button_open = tk.Button(frame, command=self.root.open_download_directory)
            tkx.add_tooltip(self.button_open)

            # update_labels is handled by root
            # self.pack_buttons_before_download() is done indirectly by root (WindowMain.__init__ > WindowMain.switch_to_frame > FrameLog.pack_forget > FrameLog.pack_buttons_before_download)

        def update_labels(self):
            self.button_cancel[tkc.TEXT] = _("cancel")
            self.button_close[tkc.TEXT] = _("close")
            self.button_back[tkc.TEXT] = _("back")
            self.button_open[tkc.TEXT] = _("open")
            self.button_open.tooltip[tkc.TEXT] = _("open download directory")
            self.text_log.checkbox_auto_scroll[tkc.TEXT] = _("scroll automatically to end")

        def pack_buttons_before_download(self, dummy=None):
            self.button_cancel.pack(side=tk.LEFT)
            self.button_back.pack_forget()
            self.button_open.pack_forget()
            self.button_close.pack_forget()
        
        def pack_buttons_after_download(self, dummy=None):
            tkx.set_enabled(self.button_open, self.root.can_open_download_directory())
            self.button_cancel.pack_forget()
            self.button_back.pack(side=tk.LEFT)
            self.button_open.pack(side=tk.LEFT)
            self.button_close.pack(side=tk.LEFT)
        
        def pack_buttons_after_update(self, dummy=None):
            self.button_cancel.pack_forget()
            self.button_back.pack(side=tk.LEFT)
            self.button_open.pack_forget()
            self.button_close.pack_forget()
            
        def on_subprocess_finished(self, returncode):
            if returncode==0:
                self.root.log(_("process finished"), tags=(self.TAG_FINISHED,))
            else:
                self.root.log(_("process failed with return code {0}".format(returncode)), tags=(self.TAG_FINISHED,self.TAG_ERROR))
            self.pack_buttons_after_download()

        def pack_forget(self):
            tk.Pack.pack_forget(self)
            self.text_log.delete(1.0, tk.END)
            self.pack_buttons_before_download()
            self.root.reset()


    class FrameNotInstalled(tk.Frame):

        def __init__(self, master, **kw):
            self.check_installed_ret = kw.pop('check_installed_ret')
            tk.Frame.__init__(self, master, **kw)
            self.root = master

            self.label = tkx.ScrolledTextReadonly(self, height=0, wrap=tk.WORD)
            self.label.pack(expand=True, fill=tk.BOTH)

            frame = tk.Frame(self)
            frame.pack(expand=False, fill=tk.X)
            self.entry_path = tkx.Entry(frame)
            self.entry_path.pack(expand=True, fill=tk.X, side=tk.LEFT)
            self.entry_path.default_bg = self.entry_path['bg']
            tkx.set_text(self.entry_path, self.root.adapter._get_default_cmd()[0])
            self.button_browse = tkx.Button(frame, imagepath=Icon.BROWSE, command=self.browse_path)
            self.button_browse.pack(side=tk.RIGHT)

            self.label_error = tkx.LabelSelectable(self, fg='red')
            self.label_error.pack(anchor=tk.W)

            frame = tkx.ButtonsFrame(self,
                ok = dict(command=self.retry, default=tk.ACTIVE),
                cancel = dict(command=self.root.close),
            )
            frame.pack(side=tk.BOTTOM)
            self.frame_buttons = frame
            self.button_retry = frame.button_ok
            self.button_close = frame.button_cancel

        def update_labels(self):
            if self.check_installed_ret == adapter.Adapter.RET_PERMISSION_DENIED:
                text = _("""
I don't have the permission to execute the application youtube-dl. This program is merely a GUI and can not be used without it.

Please make the file executable. (The command in question is displayed in the entry box below.)
While you are at it, please make sure it is writable as well (important for updates).

For further information see the webpage:
http://rg3.github.io/youtube-dl/download.html
""").strip("\n")
            else:
                text = _("""
Failed to find the application youtube-dl. This program is merely a GUI and can not be used without it.

Although youtube-dl is available via apt I discourage installing it that way because it's crucial that youtube-dl is up to date, otherwise it may not work. After the following manual installation, updates can be performed via this GUI by opening the "youtube-dl" menu and clicking on the "update" button.

(1) Download youtube-dl from the following url and move it whereever you want to store it.
http://rg3.github.io/youtube-dl/download.html

(2) Make the file write- and executable for the user. (Write permissions are important for updates.)

(3) Enter it's path into the entry box below and click on Retry.
""").strip("\n")
            tkx.set_text(self.label, text)
            self.button_retry.config(text=_("Retry"))
            self.button_close.config(text=_("Close"))

            self.update_error_label()

        def update_error_label(self):
            ret = self.check_installed_ret
            if ret == adapter.Adapter.RET_PERMISSION_DENIED:
                tkx.set_text(self.label_error, _("permission denied"))
            elif ret == adapter.Adapter.RET_FILE_NOT_FOUND:
                tkx.set_text(self.label_error, _("file not found"))
                self.entry_path.config(bg='red')
                self.entry_path.bind_to_write(lambda: self.entry_path.config(bg=self.entry_path.default_bg))
            else:
                log.error("unknown return code for check_installed: %s" % ret)
                tkx.set_text(self.label_error, ret)


        def browse_path(self, event=None):
            path = tkx.get_text(self.entry_path)
            fn = 'youtube-dl'

            if not os.path.isdir(path):
                path,fn = os.path.split(path)

            if path == "":
                diropt = "/opt"
                if os.path.isdir(diropt):
                    path = diropt

            # https://pypi.org/project/tkfilebrowser/
            path = tkFileDialog.askopenfilename(
                title = _("Choose youtube-dl executable"),
                initialdir = path,
                initialfile = fn,
            )
            if path == "":
                return

            tkx.set_text(self.entry_path, path)

        def retry(self):
            path = tkx.get_text(self.entry_path)
            self.root.adapter.set_path(path)

            ret = self.root.adapter.check_installed()
            if ret == adapter.Adapter.RET_INSTALLED:
                self.root.frames.remove(self)
                self.destroy()
                self.root.start()
                self.root.save_settings(force=True)
            else:
                self.check_installed_ret = ret
                self.update_error_label()

            

    def __init__(self, adapter):
        tk.Tk.__init__(self)
        self.cursor_manager = tkx.CursorManager(self)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.window_cli_help = None
        self.window_cli_version = None
        self.adapter = adapter
        self.frames = []

        if settings.setdefault(KEY.CHECK_BACKEND, True):
            self.check_backend()
        else:
            self.start()


    def start(self):
        # increases startup time significantly.
        # please note that this only takes effect if update-settings is True.
        settings[KEY.CHECK_BACKEND] = False
        self.frame_main = self.FrameMain(self)
        self.frames.append(self.frame_main)
        self.meta_info_display = self.frame_main.frame_info
        
        self.frame_log = self.FrameLog(self)
        self.frames.append(self.frame_log)

        self.update_labels()
        self.switch_to_frame(self.frame_main)

        self.reset()
        self._state = None
        self.invalidate_meta_info()

        self.update_settings()
        self.protocol(tkc.WM_DELETE_WINDOW, self.close)

        # useful for debugging
        url = settings.setdefault(KEY.COPY_TO_CLIPBOARD_ON_STARTUP, None)
        if url!=None:
            self.clipboard_clear()
            self.clipboard_append(url)
        if settings.setdefault(KEY.AUTO_PASTE_ON_STARTUP, True):
            self.frame_main.source_clear_and_paste(precheck=True)

    def check_backend(self):
        ret = self.adapter.check_installed()
        if ret == adapter.Adapter.RET_INSTALLED:
            self.start()
            self.save_settings(force=True)
            return

        self.frame_not_installed = self.FrameNotInstalled(self, check_installed_ret=ret)
        self.frame_not_installed.pack(expand=True, fill=tk.BOTH)
        self.frames.append(self.frame_not_installed)

        self.update_labels(menus=False)

    def update_settings(self):
        log.debug("update_settings()")
        self.menus.set_cascade_visibility(self.menus.menu_debug, settings.setdefault(KEY.SHOW_DEBUG_MENU, False))
        self.frame_main.update_settings()
        self.POLL_INTERVAL_IN_MS_FOR_DOWNLOAD = settings.setdefault(KEY.POLL_INTERVAL_IN_MS_FOR_DOWNLOAD, 500)
        self.POLL_INTERVAL_IN_MS_FOR_METAINFO = settings.setdefault(KEY.POLL_INTERVAL_IN_MS_FOR_METAINFO, 100)
        self.shortcuts()

    def shortcuts(self):
        log.debug("shortcuts()")
        ffn = metainfo.get_config_ffn(FN_SHORTCUTS)
        with open(ffn, 'rt') as f:
            code = f.read()
        env = dict(self=self, settings=settings, KEY=KEY)
        exec(code, env)
        shortcuts = env['shortcuts']
        for event in shortcuts:
            self.bind(event, shortcuts[event])

    def reset(self):
        self.download_dest = None

    def update_labels(self, menus=True):
        log.debug("update_labels()")
        self.title(_("youtube-dl"))
        if menus:
            self.menus = self.ApplicationMenus(self)
        
        for f in self.frames:
            f.update_labels()

        if tkx.is_open_window(self.window_cli_help):
            self.window_cli_help.update_labels()
        if tkx.is_open_window(self.window_cli_version):
            self.window_cli_version.update_labels()

    def switch_to_frame(self, frame):
        for f in self.frames:
            f.pack_forget()
        frame.pack(expand=True, fill=tk.BOTH)
        self.update()


    def log(self, msg, tags=None):
        if tags and self.FrameLog.TAG_ERROR in tags:
            sys.stderr.write(msg)
        else:
            sys.stdout.write(msg)
        #sys.stdout.flush()
        self._log_gui(msg, tags)

    def _log_gui(self, msg, tags):
        # get text widget
        text = self.frame_log.text_log
        
        # process cariage return
        msg = msg.replace("\r\n", "\n")
        msg = msg.replace("\r", "\n")
##        #ERROR: text is not overwritten with cr but only with following content
##        i0 = 0
##        while True:
##            i1 = msg.rfind("\r")
##            if i1==-1:
##                break
##            i0 = msg.rfind("\n", 0, i1)
##            if i0==-1:
##                break
##            msg = msg[:i0+1] + msg[i1+1:]
##        if i0==-1:
##            msg = msg[i1+1:]
##            #TODO: remove last line from text widget

        if msg[-1]!='\n':
            msg += '\n'

        # add message to text widget & scroll
        if tags==None:
            msg = msg[:-1]
            for ln in msg.split("\n"):
                if self.adapter.is_error(ln):
                    tags = (self.frame_log.TAG_ERROR,)
                elif self.adapter.is_warning(ln):
                    tags = (self.frame_log.TAG_WARNING,)
                elif self.adapter.is_destination(ln, self.set_destination):
                    tags = (self.frame_log.TAG_DESTINATION,)
                else:
                    tags = None
                text.append(ln+'\n', tags)
        else:
            text.append(msg, tags)
        text.update()
        
        return msg


    # event listener frame main

    def set_destination(self, dest):
        self.download_dest = dest
    
    def show_info(self, event=None):
        pass

    def get_clipboard_content(self):
        try:
            return self.selection_get(selection = "CLIPBOARD")
        except tk.TclError:
            return ""

    def invalidate_meta_info(self):
        if self._state == self.STATE_UNCHECKED:
            return
        self._state = self.STATE_UNCHECKED
        self.frame_main.mark_source_url(self._state)
        self.meta_info_raw = None
        self.meta_info = None
        #self.meta_info_display.update_info(dict())
        self.meta_info_display.hide()

    def _on_new_meta_data(self):
        if self._state != self.STATE_UNCHECKED: log.warning("changed directly from state {old_state} to state {new_state}".format(old_state=self._state, new_state=self.STATE_SUCCESS))
        self._state = self.STATE_SUCCESS
        self.frame_main.mark_source_url(self._state)
        self.meta_info_display.update_info(self.meta_info)
        self.meta_info_display.show()
        self.cursor_manager.reset_cursor()
        self.menus.menu_debug.entry_enable('save_metainfo')
        
    def _on_error_metainfo_download(self, error_message):
        if self._state != self.STATE_UNCHECKED: log.warning("changed directly from state {old_state} to state {new_state}".format(old_state=self._state, new_state=self.STATE_ERROR))
        self._state = self.STATE_ERROR
        self._error_message = error_message
        log.error(error_message)
        #TODO: determine the cause
        self.frame_main.mark_source_url(self._state)
##        tkMessageBox.showerror(
##            title=_("Failed to retrieve meta info"),
##            message = error_message
##        )
        self.cursor_manager.reset_cursor()
    
    
    def update_metainfo(self):
        if self.meta_info_raw != None:
            log.debug("update metainfo not necessary...")
            return
        adapter = self.adapter
        if adapter.is_running():
            log.info("killing download-metainfo-subprocess in order to download other metainfo")
            self.kill()
            self.update()
            time.sleep(0.1) # visual feedback. short time span in which normal cursor is visible to show the user that the button click is not ignored.
        log.debug("update metainfo...")
        self.cursor_manager.set_cursor()
        self.update()
        self.invalidate_meta_info()
        self._on_finish_listener = self.update_metainfo_on_finish
        settings = self.frame_main.get_settings()
        if not settings[adapter.SOURCE_URL]:
            self._on_error_metainfo_download("no source URL given")
        settings[adapter.METAINFO_ONLY] = True
        adapter.process_params(settings)
        adapter.start()
        self.update_metainfo_poll(adapter)
    def update_metainfo_poll(self, adapter):
        if adapter.is_finished():
            self.update_metainfo_on_finish(adapter)
        else:
            adapter._after_id = self.after(self.POLL_INTERVAL_IN_MS_FOR_METAINFO, self.update_metainfo_poll, adapter)
    def update_metainfo_on_finish(self, adapter):#self=self, lines_json=lines_json):
        returncode = adapter.get_returncode()
        log.debug("return code of get metainfo subprocess: {c}".format(c=returncode))
        self.meta_info_raw = "".join(ln for ln,flag in adapter.iter_out())
        if "is not a valid URL" not in self.meta_info_raw: #returncode==0:
            json_code = self.meta_info_raw
            WARNING = 'WARNING'
            while json_code[:len(WARNING)]==WARNING:
                ln, json_code = json_code.split('\n', 1)
                log.warning(ln)
            try:
                self.meta_info = json.loads(json_code)
            except ValueError as e:
                log.error("ValueError while trying to parse metainfo json:")
                log.error(e)
                self._on_error_metainfo_download(self.meta_info_raw)
                return
            self._on_new_meta_data()
        else:
            log.error("{string!r} is contained in downloaded metainfo".format(string="is not a valid URL"))
            self._on_error_metainfo_download(self.meta_info_raw)
    
    def kill(self):
        adapter = self.adapter
        self.after_cancel(adapter._after_id)
        adapter.kill()
        if self.cursor_manager.is_cursor_changed():
            self.cursor_manager.reset_cursor()
    

    def save_metainfo(self, raw):
        if self.meta_info!=None:
            fn = ""
            for c in self.meta_info['title']:
                if c.isalnum() or c in "-_ +":
                    fn += c
        else:
            fn = "none"
        if raw:
            json_code = self.meta_info_raw
            fn += '_RAW'
        else:
            json_code = json.dumps(self.meta_info, sort_keys=True, indent=4)
        ffn = tkFileDialog.asksaveasfilename(
            initialdir = os.path.join(os.path.split(__file__)[0], '_info', 'example-json-files'),
            initialfile = fn,
            defaultextension='.json',
            filetypes=(
                (_("json files"), "*.json"),
                (_("text files"), "*.txt"),
                (_("all files"), ".*"),
            ),
        )
        if ffn=='':
            log.debug("save metainfo as was canceled by user.")
            return
        with open(ffn, mode='wt') as f:
            f.write(json_code)
        open_directory.open_directory(ffn, select=True)

    def save_log_as(self):
        if self.meta_info!=None:
            fn = self.meta_info['title']
        else:
            fn = "none"
        path = tkx.get_text(self.frame_main.var_working_directory)
        ffn_dest = tkFileDialog.asksaveasfilename(
            title = _("save log as"),
            initialdir = path,
            initialfile = fn,
            defaultextension = '.log',
            filetypes = (
                (_("log files"), ".log"),
                (_("text files"), ".txt"),
                (_("all files"), ".*"),
            ),
        )
        if ffn_dest=='':
            log.debug("save log as was canceled by user.")
            return
        log.debug("save log as {fn}".format(fn=ffn_dest))
        ffn_source = logging_setup.logfile.get_name()
        with open(ffn_source, 'rt') as f_source:
            with open(ffn_dest, 'wt') as f_dest:
                for ln in f_source:
                    f_dest.write(ln)
        

    def open_window_cli_help(self, event=None):
        if tkx.is_open_window(self.window_cli_help):
            self.window_cli_help.lift()
        else:
            self.window_cli_help = WindowCLIHelp(self.adapter.create_new_instance())
            self.window_cli_help.display_help()

    def open_window_cli_version(self, event=None):
        if tkx.is_open_window(self.window_cli_version):
            self.window_cli_version.lift()
        else:
            self.window_cli_version = WindowCLIHelp(self.adapter.create_new_instance())
            self.window_cli_version.display_version()
        
    def download(self, event=None):
        if self.frame_main.entry_source.get_value().strip()=="":
            self._on_error_metainfo_download("no source URL given")
            tkMessageBox.showerror(_("No source URL given"), _("Please paste the source URL."))
            return
        settings = self.frame_main.get_settings()
        adapter = self.adapter
        if adapter.is_running():
            log.info("killing download-metainfo-subprocess in order to start download")
            self.kill()
        adapter.process_params(settings)
        self._on_finish_listener = self.frame_log.on_subprocess_finished
        self.switch_to_frame(self.frame_log)
        adapter.start()
        self._poll_read(adapter)

    def perform_update(self, event=None):
        #TODO: disable backend-menu while running
        self._on_finish_listener = self.frame_log.on_subprocess_finished
        self.switch_to_frame(self.frame_log)
        adapter = self.adapter
        if adapter.is_running():
            log.info("killing download-metainfo-subprocess in order to start backend update")
            self.kill()
        adapter.set_command_update()
        adapter.start()
        self._poll_read(adapter)

    def _poll_read(self, adapter):
        self._read(adapter)
        if adapter.is_finished():
            self._on_finish_listener(adapter.get_returncode())
        else:
            adapter._after_id = self.after(self.POLL_INTERVAL_IN_MS_FOR_DOWNLOAD, self._poll_read, adapter)
    
    def _read(self, adapter):
        for ln, flag in adapter.iter_out():
            if flag==adapter.STDOUT:
                self.log(ln)
            else:
                self.log(ln, (self.FrameLog.TAG_ERROR,))

    def open_download_directory(self, event=None):
        dirpath = self.frame_main.var_working_directory.get()
        filepath = os.path.join(dirpath, self.download_dest)
        if os.path.isfile(filepath):
            open_directory.open_directory(filepath, select=True)
        else:
            log.error("{0!r} does not exist".format(filepath))
            open_directory.open_directory(dirpath, select=False)

    def can_open_download_directory(self):
        return self.download_dest != None

    def save_settings(self, event=None, force=False):
        if force or settings_manager.are_updates_wanted():
            log.debug("updating settings")
            settings[KEY.DESTINATION_PATH] = tkx.get_text(self.frame_main.var_working_directory)
            settings[KEY.AUDIO_FORMAT] = self.frame_main.menubtn_format_audio.get_value()
            settings[KEY.EXTRACT_AUDIO] = self.frame_main.checkbox_audio_only.get_value()
            settings[KEY.KEEP_VIDEO] = self.frame_main.checkbox_keep_video.get_value()
            #if tkx.is_enabled(self.frame_main.checkbox_video_format): #TODO: do I want this?
            settings[KEY.VIDEO_FORMAT_EXPLICIT] = self.frame_main.checkbox_video_format.get_value()
            settings[KEY.VIDEO_FORMAT] = self.frame_main.menubtn_video_format.get_value()
            settings[KEY.SUBTITLES_FOR_VIDEO] = self.frame_main.var_subtitles_for_video.get()
            if settings[KEY.SUBTITLES_DEPEND_ON_AUDIO_ONLY]:
                settings[KEY.SUBTITLES_FOR_AUDIO] = self.frame_main.var_subtitles_for_audio.get()
            settings[KEY.SUBTITLE_LANGUAGES] = self.frame_main.entry_subtitle_languages.get_value()
            settings[KEY.SUBTITLE_LANGUAGES_AUTO_CREATED] = self.frame_main.entry_subtitle_languages_auto_created.get_value()
            settings[KEY.ADDITIONAL_OPTIONS_ENABLED] = self.frame_main.frame_cl_options.is_expanded()
            settings[KEY.ADDITIONAL_OPTIONS] = self.frame_main.entry_cl_options.get_value()
            #settings[KEY.AUTO_PASTE_ON_STARTUP] = 
            #settings[KEY.COPY_TO_CLIPBOARD_ON_STARTUP] =
        settings_manager.save_settings(
            settings=settings,
            force=force,
            ask_overwrite_handler=lambda: tkMessageBox.askyesno(
                title=_("Save Settings?"),
                message=_("You have opened the settings in an external editor. If you have changed the settings there and proceed those changes will be overwritten. Do you want to save the currently active settings?"),
                default=tkMessageBox.NO,
                icon=tkMessageBox.WARNING,
            )
        )

    def open_settings(self, event=None):
        self.save_settings()
        settings_manager.open_settings()
        

    def cancel_download(self, event=None):
        self.log(_("cancelling download on behalf of user intervention"), tags=(self.FrameLog.TAG_WARNING,))
        #TODO: kill_in
        self.kill()
    
    def close(self, event=None):
        log.debug("close()")
        if self.adapter.is_running():
            log.info("killing subprocess in order to quit program")
            self.kill()
        
        self.save_settings()
        logging_setup.logfile.append_end_line() # atexit is not called if executed from IDLE
        if settings[KEY.AUTO_REMOVE_LOG_AT_CLOSE]:
            logging_setup.logfile.remove()
        self.destroy()
        self.quit()
        
        if tkx.is_open_window(self.window_cli_help):
            self.window_cli_help.destroy()
        if tkx.is_open_window(self.window_cli_version):
            self.window_cli_version.destroy()

    def reload_settings(self):
        settings_manager.load_settings(settings)
        self.update_settings()



# ===== other windows ======

class WindowCLIHelp(tk.Tk):

    POLL_INTERVAL_IN_MS = 1000//50
    
    def __init__(self, adapter):
        tk.Tk.__init__(self)
        self.adapter = adapter.create_new_instance()
        self.adapter.add_info = False
        self.cursor_manager = tkx.CursorManager(self)
        
        frame = self
        self.text = tkx.ScrolledText(frame, readonly=True, wrap=tk.WORD)
        self.text.pack(expand=True, fill=tk.BOTH)
        self.text.bind('<Double-Button-1>', self.select_current_word)

        self.update_labels()
        #self.update() #is done in self._run()

    def display_help(self):
        self.adapter.set_command_print_help()
        self._run()
    def display_version(self):
        self.adapter.set_command_print_version()
        self._run()

    def _run(self):
        self.cursor_manager.set_cursor()
        self.title(" ".join(self.adapter.cmd))
        self.update()
        self.adapter.start()
        self._poll_read(self.adapter)

    def _read(self, adapter):
        for ln, flag in adapter.iter_out():
            self.write(ln)

    def _poll_read(self, adapter):
        self._read(adapter)
        if adapter.is_finished():
            self.finish()
        else:
            adapter._after_id = self.after(self.POLL_INTERVAL_IN_MS, self._poll_read, adapter)


    def update_labels(self):
        pass

    def write(self, text):
        self.text.insert(tk.END, text)
        self.update()

    def finish(self):
        self.cursor_manager.reset_cursor()

    def select_current_word(self, event=None):
        i0 = self.text.search(r'[-\w]+', tk.CURRENT+'+1c', backwards=True, regexp=True)
        i1 = self.text.search(r'[^-\w]+', i0, forwards=True, regexp=True)
        self.text.tag_remove(tk.SEL, '1.0', tk.END)
        self.text.tag_add(tk.SEL, i0, i1)
        self.update()
        return tkc.BREAK


class WindowResetSettings(tk.Toplevel):

    def __init__(self, root):
        tk.Toplevel.__init__(self)
        self.title(_("Reset Settings"))
        self.root = root
        self.grid_columnconfigure(0, minsize=18)
        self.grid_columnconfigure(1, weight=1)

        # settings
        self.path_settings = os.path.split(settings_manager.get_fullfilename(settings))[0]
        lbl = tk.Label(self, text=_("Please select what you want to remove:"))
        lbl.grid(columnspan=2, sticky=tk.W)
        self.checkbox_settings_directory = tkx.Checkbutton(self, text=_("entire settings directory")+' ({0})'.format(self.path_settings), command=self.update_state)
        self.checkbox_settings_directory.grid(columnspan=2, sticky=tk.W)
        self.checkboxes_settings_files = list()
        fns = os.listdir(self.path_settings)
        fns.sort()
        can_remove_folder = True
        for fn in fns:
            ffn = os.path.join(self.path_settings, fn)
            if not os.path.isfile(ffn):
                log.debug("non-file in settings directory: {0!r}".format(ffn))
                can_remove_folder = False
                continue
            chkbox = tkx.Checkbutton(self, text=fn)
            chkbox.grid(column=1, sticky=tk.W)
            self.checkboxes_settings_files.append(chkbox)
        if not can_remove_folder:
            self.checkbox_settings_directory[tkc.STATE] = tkc.STATE_DISABLED
            tkx.add_tooltip(self.checkbox_settings_directory)
            self.checkbox_settings_directory.tooltip[tkc.TEXT] = _("Directory can not be removed because it contains more than just configuration files.")
            self.checkboxes_all = self.checkboxes_settings_files
        else:
            self.checkboxes_all = [self.checkbox_settings_directory] + self.checkboxes_settings_files
        
        # buttons
        frame = tkx.ButtonsFrame(self,
            ok = dict(text=_("delete"), command=self.delete, default=tk.ACTIVE),
            cancel = dict(text=_("cancel"), command=self.cancel),
        )
        frame.grid(columnspan=2, sticky='SWE')
        self.button_delete = frame.button_ok
        self.button_cancel = frame.button_cancel
        
        # shortcuts
        self.bind('<Control-a>', lambda e: self.set_checkboxes(self.checkboxes_all, True))
        self.bind('<Control-A>', lambda e: self.set_checkboxes(self.checkboxes_all, False))
        self.bind('<Control-Alt-a>', lambda e: self.toggle_checkboxes(self.checkboxes_all))
        self.bind('<Return>', lambda e: self.button_delete.invoke())
        self.bind('<Escape>', lambda e: self.button_cancel.invoke())
        
        for chkbox in self.checkboxes_all:
            chkbox.bind('<Return>', lambda event: tkx.only(event.widget.invoke(), self.focus()))
            chkbox.bind('<Escape>', lambda event: tkx.only(self.focus()))
        
        for chkbox in self.checkboxes_settings_files:
            chkbox.bind('<Control-a>', lambda e: self.set_checkboxes(self.checkboxes_settings_files, True))
            chkbox.bind('<Control-A>', lambda e: self.set_checkboxes(self.checkboxes_settings_files, False))
            chkbox.bind('<Control-Alt-a>', lambda e: self.toggle_checkboxes(self.checkboxes_settings_files))

        self.set_checkboxes(self.checkboxes_all, True)
        self.update_state()
        

    def update_state(self, event=None):
        chbdir = self.checkbox_settings_directory
        if chbdir.get_value() and chbdir[tkc.STATE]!=tkc.STATE_DISABLED:
            state = tkc.STATE_DISABLED
        else:
            state = tkc.STATE_NORMAL
        for chkbox in self.checkboxes_settings_files:
            chkbox[tkc.STATE] = state


    def set_checkboxes(self, checkboxes, value):
        for chkbox in checkboxes:
            chkbox.set_value(value)
        return tkc.RETURNCODE_BREAK
    
    def toggle_checkboxes(self, checkboxes):
        for chkbox in checkboxes:
            chkbox.toggle()
        return tkc.RETURNCODE_BREAK

    
    def delete(self):
        d = self.path_settings
        if self.checkbox_settings_directory.get_value():
            self.remove_directory(d)
        else:
            for chkbox in self.checkboxes_settings_files:
                if chkbox.get_value():
                    fn = chkbox['text']
                    ffn = os.path.join(d, fn)
                    log.info("removing {0}".format(ffn))
                    os.remove(ffn)
        
        self.root.reload_settings()
        self.destroy()

    @staticmethod
    def remove_directory(path):
        for fn in os.listdir(path):
            ffn = os.path.join(path, fn)
            log.info("removing {0}".format(ffn))
            os.remove(ffn)
        os.rmdir(path)
        log.info("removing {0}".format(path))
        

    def cancel(self):
        log.debug("delete settings has been canceled by user")
        self.destroy()


# ===== main =====

if __name__=='__main__':
    import adapter
    #adapter.TEST = True
    a = adapter.Adapter()
    m = WindowMain(a)
    m.mainloop()
