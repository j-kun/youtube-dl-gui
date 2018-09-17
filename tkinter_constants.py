#!/usr/bin/env python
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

import which_os_am_i_on

TEXT = 'text'
TEXTVARIABLE = 'textvariable'
STATE = 'state'
COMMAND = 'command'
STATE_NORMAL = tk.NORMAL
STATE_ACTIVE = tk.ACTIVE
STATE_DISABLED = tk.DISABLED
STATE_READONLY = 'readonly'
# readonly seems to work for Entry but not for Text
# as work around use something like
# text.bind("<Key>", lambda event: "break")
STATES_WRITABLE = (STATE_NORMAL, STATE_ACTIVE)
STATES_READONLY = (STATE_DISABLED, STATE_READONLY)

COLOR_FOREGROUND = 'foreground'
COLOR_BACKGROUND = 'background'

N = tk.N
S = tk.S
W = tk.W
E = tk.E
WNSE = W+N+S+E

#.keycode:
#   http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/key-names.html
#.state (modifier masks):
#   http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/event-handlers.html
#   does not seem reliable: https://stackoverflow.com/a/19863837
MOD_CTRL = 0x0004 # keyevent.state: modifier control
if which_os_am_i_on.windows():
    MOD_ALT   = 0x20000
else:
    MOD_ALT   = 0x0008

KEYCODE_ARROW_UP    = 111
KEYCODE_ARROW_DOWN  = 116
KEYCODE_ARROW_LEFT  = 113
KEYCODE_ARROW_RIGHT = 114
KEYCODES_ARROWS = (KEYCODE_ARROW_UP, KEYCODE_ARROW_DOWN, KEYCODE_ARROW_LEFT, KEYCODE_ARROW_RIGHT)
KEYCODE_HOME = 110
KEYCODE_END  = 115
KEYCODES_MOVE_CURSOR = KEYCODES_ARROWS + (KEYCODE_HOME, KEYCODE_END)
KEYCODE_TAB = 23

KEY_CURSOR = 'cursor'
CURSOR_ARROW = 'arrow'
CURSOR_WATCH = 'watch'

# Protocols:
WM_DELETE_WINDOW = 'WM_DELETE_WINDOW'
WM_TAKE_FOCUS    = 'WM_TAKE_FOCUS'
WM_SAVE_YOURSELF = 'WM_SAVE_YOURSELF'

# Menu:
KEY_TEAROFF = 'tearoff'
KEY_MENU = 'menu'

# Style
RELIEF_FLAT   = tk.FLAT
RELIEF_RAISED = tk.RAISED
RELIEF_SUNKEN = tk.SUNKEN
RELIEF_GROOVE = tk.GROOVE
RELIEF_RIDGE  = tk.RIDGE

DEFAULT = 'default'
DEFAULT_ACTIVE   = tk.ACTIVE    # In active state, the button is drawn with the platform specific appearance for a default button.
DEFAULT_NORMAL   = tk.NORMAL    # In normal state, the button is drawn with the platform specific appearance for a non-default button, leaving enough space to draw the default button appearance. The normal and active states will result in buttons of the same size.
DEFAULT_DISABLED = tk.DISABLED  # In disabled state, the button is drawn with the non-default button appearance without leaving space for the default appearance. The disabled state may result in a smaller button than the active state.
                                # https://www.tcl.tk/man/tcl8.4/TkCmd/button.htm#M7

# Variables:
TRACE_WRITE = 'w'
TRACE_READ  = 'r'
TRACE_UNDEFINE = 'u'

# Listener:
BREAK = 'break'
RETURNCODE_BREAK = BREAK

# Fonts:
FONT = 'font'
FONT_WEIGHT_BOLD = 'bold'
FONT_WEIGHT_NORMAL = 'normal'
FONT_SLANT_ITALIC = 'italic'
FONT_SLANT_ROMAN = 'roman'
