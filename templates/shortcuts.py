"""
tkinter events:
    http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/event-types.html
    http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/event-modifiers.html
    http://www.python-course.eu/tkinter_events_binds.php

modifiers:
    Control, Alt, Shift, Lock
    Double, Triple
    Any

WARNING: it's not <Shift-Control-f> but <Control-F>!!!

The special keys are:
    Cancel (the Break key), BackSpace,
    Tab, Return(the Enter key),
    Shift_L (any Shift key), Control_L (any Control key), Alt_L (any Alt key),
    Pause, Caps_Lock, Escape, Prior (Page Up), Next (Page Down), End, Home, Left, Up, Right, Down,
    Print, Insert, Delete, F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, Num_Lock, and Scroll_Lock.

tk.Checkbutton has an invoke function and a toggle function. invoke works like click, doing nothing if disabled. toggle does not care about state.
"""

only = lambda x: 'break'

def cycle(var, values):
    print('cycle!')
    i = values.index(var.get())
    i += 1
    if i>=len(values):
        i = 0
    var.set(values[i])

shortcuts = {
    # about
    '<F1>' : lambda event: only(self.menus.menu_backend.invoke('help')),
    '<Control-F1>' : lambda event: only(self.menus.menu_debug.invoke('open_log')),
    '<F5>' : lambda event: only(self.menus.menu_frontend.invoke('edit_settings')),
    '<F6>' : lambda event: only(self.menus.menu_frontend.invoke('edit_shortcuts')),
    # main controls
    '<Control-f>' : lambda event: only(self.frame_main.button_search_youtube.invoke()),
    '<Control-v>' : lambda event: only(self.frame_main.button_source_clear_and_paste.invoke()),
    '<F2>'        : lambda event: only(self.frame_main.button_dest_dir_search.invoke()),
    '<Return>'    : lambda event: only(self.frame_main.button_download.invoke()),
    # optional controls
    '<Control-X>' : lambda event: only(self.frame_main.checkbox_audio_only.invoke()),
    '<Control-K>' : lambda event: only(self.frame_main.checkbox_keep_video.invoke()),
    '<Control-F>' : lambda event: only(self.frame_main.checkbox_video_format.invoke()),
    '<Control-S>' : lambda event: only(cycle(self.frame_main.var_subtitles_for_video, (self.frame_main.SUBTITLES_OFF, self.frame_main.SUBTITLES_ON, self.frame_main.SUBTITLES_AUTO_CREATED))),
}
# menus:
self.menus.shortcut(key='f', name='frontend')
self.menus.shortcut(key='y', name='backend')
if settings[KEY.SHOW_DEBUG_MENU]:
    self.menus.shortcut(key='d', name='debug')
else:
    shortcuts['<Alt-d>'] = lambda event: only(self.menus.open_menu(self.menus.menu_debug))
