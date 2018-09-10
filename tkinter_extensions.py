#!/usr/bin/env python
# ========== libraries ==========
# standard libraries
try:
    # Python 2
    import Tkinter as tk
    import ttk
    import ScrolledText as tkText
except:
    # Python 3
    import tkinter as tk
    from tkinter import scrolledtext
    tkText = scrolledtext
    from tkinter import ttk
import os.path
import logging
log = logging.getLogger(__name__)

# other libraries
try:
    import tk_tooltip
except:
    import tk_tooltip_fake as tk_tooltip
    log.warning("did not find tk_tooltip library. tooltips are not displayed.")
ImageTk = tk
import tkinter_constants as tkc
import which_os_am_i_on


# ========== Klassenuebergreifende Funktionen ==========

def set_text(widget, text):
    if isinstance(widget, tk.Entry):
        widget.delete(0, tk.END)
        widget.insert(0, text)
    elif isinstance(widget, tk.Text):
        widget.delete(1.0, tk.END)
        widget.insert(tk.END, text)
    elif isinstance(widget, tk.StringVar):
        widget.set(text)
    elif isinstance(widget, tk.Label):
        widget[tkc.TEXT] = text
    else:
        log.error("set_text is not implemented for {0}".format(type(widget)))
        raise NotImplemented

def get_text(widget):
    if isinstance(widget, tk.Entry):
        return widget.get()
    elif isinstance(widget, tk.Text):
        return widget.get(1.0)
    elif isinstance(widget, tk.StringVar):
        return widget.get()
    else:
        raise NotImplemented


def add_tooltip(widget):
    #TODO: delay as setting
    widget.tooltip = tk_tooltip.ToolTip(widget, delay=500)


def is_open_window(window):
    if window==None:
        return False
    else:
        try:
            return window.winfo_exists()
        except tk.TclError:
            return False

def is_enabled(widget):
    return str(widget[tkc.STATE])!=tkc.STATE_DISABLED

def set_enabled(widget, enabled):
    widget[tkc.STATE] = tkc.STATE_NORMAL if enabled else tkc.STATE_DISABLED

def only(*x):
    '''returns 'break'. This can be used in a lambda expression bound to an event to break out of the event handling chain.'''
    return tkc.RETURNCODE_BREAK


def create_image(imagepath):
    if os.path.splitext(imagepath)[1]=='.xbm':
        image = tk.BitmapImage(file=imagepath)
    else:
        image = ImageTk.PhotoImage(file=imagepath)
    return image

# ========== abstract classes ==========

class WidgetWithContextMenu(object):

    default_contextmenu = None
    default_on_contextmenu_open = None
    _contextmenu_bind_sequence = '<Button-3>'

    def __init__(self):
        self._contextmenu_bind_id = None
        self.contextmenu = None
        self._on_contextmenu_open_listeners = set()
        if self.default_on_contextmenu_open!=None:
            self.add_on_contextmenu_open_listener(self.default_on_contextmenu_open)
    
    def process_keywordargs(self, kw):
        self._contextmenu = kw.pop('contextmenu', self.default_contextmenu)
        self._contextmenuadd = kw.pop('contextmenuadd', ())

    def set_contextmenu_from_keywordargs(self):
        menu = self._contextmenu
        if menu==None:
            log.warning("menu==None")
            return
        self.set_contextmenu(menu)

        menu = self._contextmenuadd
        if menu==None:
            return
        for item in menu:
            self.add_to_contextmenu(item)

    def has_contextmenu(self):
        return self._contextmenu_bind_id != None

    def remove_contextmenu(self):
        self.unbind(self._contextmenu_bind_sequence, self._contextmenu_bind_id)
        self._contextmenu_bind_id = None
        self.contextmenu = None

    def set_contextmenu(self, menu):
        '''menu: either tk.Menu|tkx.Menu or iterable like (("label 0", cmd0), ...)\nwith the second option, the function cmd0 gets one parameter: the object it self.'''
        #if self.has_contextmenu():
        #    self.remove_contextmenu()
        if isinstance(menu, tk.Menu):
            self.contextmenu = menu
        else:
            self.contextmenu = Menu(self, tearoff=0)
            for item in menu:
                self.add_to_contextmenu(item)

        if not self.has_contextmenu():
            self._contextmenu_bind_id = self.bind(sequence=self._contextmenu_bind_sequence, func=self.open_contextmenu, add=True)
        #log.debug("bound context menu to sequence {sequence!r} with id {id!r}." % (sequence=self._contextmenu_bind_sequence, id=self._contextmenu_bind_id)
        #TODO: remember focusable, set focusable

    def add_to_contextmenu(self, menuitem):
        '''menuitem: ((['id-0',] "label 0", cmd0), ...)'''
        if len(menuitem)==3:
            name, lbl, cmd = menuitem
        else:
            lbl, cmd = menuitem
            name = lbl
        if hasattr(cmd, '__call__'):
            self.contextmenu.add_named_command(name, label=lbl, command=lambda: cmd(self))
        else:
            #TODO
            raise NotImplemented("sub menus are not yet implemented")
        #else:
        #    lbl, cmd = menuitem
        #    self.contextmenu.add_command(label=lbl, command=cmd)

    def open_contextmenu(self, event):
        '''event must provide screen coordinates x_root and y_root'''
        for listener in self._on_contextmenu_open_listeners:
            listener()
        self.contextmenu.tk_popup(event.x_root, event.y_root)

    def add_on_contextmenu_open_listener(self, listener):
        '''listener: callable object with no parameters'''
        self._on_contextmenu_open_listeners.add(listener)

    def remove_on_contextmenu_open_listener(self, listener):
        self._on_contextmenu_open_listeners.remove(listener)
        

# ========== sub classes ==========

class Checkbutton(tk.Checkbutton):
    def __init__(self, master=None, cnf={}, **kwargs):
        value = kwargs.pop('value', None)
        command = kwargs.pop('command', None)
        # original command argument is *not* always called! works with mouse-click and invoke but not whith set_value and toggle
        tk.Checkbutton.__init__(self, master, cnf, **kwargs)
        self.var = tk.IntVar(master=self)
        if value!=None:
            self.set_value(value)
        self.configure(variable=self.var)
        self._slaves = set()
        self.var.trace("w", self._on_change) # w means when variable is written
        if command!=None:
            self.var.trace("w", lambda varname=None, index=None, operation=None: command())

    def get_value(self):
        return bool(self.var.get())

    def set_value(self, value):
        self.var.set(1 if value else 0)

    def trace(self, command):
        '''command(new_value) will be called when value changes'''
        self.var.trace(tkc.TRACE_WRITE, lambda varname,index,operation: command(self.get_value()))

    def add_slave(self, widget):
        """widget will be enabled|disabled as this checkbutton is checked|unchecked"""
        self._slaves.add(widget)
        widget[tkc.STATE] = self._get_slaves_state()

    def _get_slaves_state(self):
        if self.get_value():
            return tkc.STATE_NORMAL
        else:
            return tkc.STATE_DISABLED

    def _on_change(self, varname=None, index=None, operation=None):
        state = self._get_slaves_state()
        for widget in self._slaves:
            widget[tkc.STATE] = state


class Menubutton(ttk.Menubutton):
    
    def __init__(self, master=None, **kw):
        KEY_DEFAULT_VALUE = 'default'
        KEY_DEFAULT_VALUE_ID = 'defaultid'
        values = kw.pop('values', None)
        default = kw.pop(KEY_DEFAULT_VALUE, None)
        default_id = kw.pop(KEY_DEFAULT_VALUE_ID, None)
        if kw.pop("autofixedwidth", 'width' not in kw):
            kw['width'] = self._get_auto_width(values)
        tearoff = kw.pop('tearoff', False)
        kw.setdefault('direction', 'flush') # 'flush', 'below' #TODO: test which one is better on windows. Settings?
        ttk.Menubutton.__init__(self, master, **kw)
        self.menu = tk.Menu(self, tearoff=tearoff)
        self.configure(menu=self.menu)
        self.set_values(values)
        if default!=None:
            if default_id!=None:
                raise TypeError("got value for keywords {0} and {1} but you can only specify one of them".format(KEY_DEFAULT_VALUE, KEY_DEFAULT_VALUE_ID))
            self.set_value(default)
        elif default_id!=None:
            self.set_value_id(default_id)
            

    def _get_auto_width(self, values):
        width = 0
        if values!=None:
            for v in values:
                width = max(len(v), width)
        return width

    def set_values(self, values, current_value_id=0):
        self.values = values
        self.menu.delete(0, tk.END)
        if self.values!=None and len(self.values)>0:
            self.set_value_id(current_value_id)
            for i in range(len(values)):
                v = self.values[i]
                self.menu.add_command(label=v, command=lambda i=i: self.set_value_id(i))
        else:
            self._current_value_id = None

    def get_values(self):
        return self.values

    def set_value(self, value):
        self.set_value_id(self.values.index(value))
        
        
    def set_value_id(self, index):
        if self.values==None:
            raise ValueError("cannot set current value because it has no values at all")
        elif not 0 <= index < len(self.values):
            raise IndexError("values with length of {n} has no index {i}".format(n=len(self.values), i=index))
        self._current_value_id = index
        self[tkc.TEXT] = self.values[self._current_value_id]

    def get_value(self):
        if self._current_value_id == None:
            return None
        else:
            return self.values[self._current_value_id]

    def get_value_id(self):
        return self._current_value_id


RETURN_CODE_BREAK = "break"


#/usr/lib/python2.7/lib-tk/ScrolledText.py
#TODO? auto hide scrollbars: http://effbot.org/zone/tkinter-autoscrollbar.htm
class ScrolledText(tkText.ScrolledText, WidgetWithContextMenu):

    default_on_readonly_enabled = None
    default_on_readonly_disabled = None

    def __init__(self, master=None, **kwargs):
        WidgetWithContextMenu.__init__(self)
        self.process_keywordargs(kwargs)
        readonly = kwargs.pop('readonly', False)
        self.on_readonly_enabled = kwargs.pop('on_readonly_enabled', lambda self: self.default_on_readonly_enabled() if self.default_on_readonly_enabled!=None else None) # methods coming from class attributes are instance methods. So the explicit self argument handed over later on would be too much without this wrapper.
        self.on_readonly_disabled = kwargs.pop('on_readonly_disabled', lambda self: self.default_on_readonly_disabled() if self.default_on_readonly_disabled!=None else None)
        #TODO: *_add is untested
        self.on_readonly_enabled_add = kwargs.pop('on_readonly_enabled_add', None)
        self.on_readonly_disabled_add = kwargs.pop('on_readonly_disabled_add', None)
        tkText.ScrolledText.__init__(self, master, **kwargs)
        self.set_contextmenu_from_keywordargs()
        self.readonly(readonly)
        self.focus_set()

    def readonly(self, readonly=None):
        if readonly==None:
            return self._readonly
        else:
            self._readonly = readonly
            if readonly:
                #self.configure(state=tkc.STATE_READONLY)
                self.bind("<Key>", lambda event: _key_event_disabled(self, event))
                if self.on_readonly_enabled != None:
                    self.on_readonly_enabled(self)
                    if self.on_readonly_enabled_add != None:
                        self.on_readonly_enabled_add(self)
            else:
                #self.configure(state=tkc.STATE_NORMAL)
                self.bind("<Key>", lambda event: _key_event_enabled(self, event))
                if self.on_readonly_disabled != None:
                    self.on_readonly_disabled(self)
                    if self.on_readonly_disabled_add != None:
                        self.on_readonly_disabled_add(self)

    def select_all(self):
        self.tag_add(tk.SEL, "1.0", tk.END)

    def selection_present(self):
        try:
            text = self.get(tk.SEL_FIRST, tk.SEL_LAST)
            return text!=''
        except tk.TclError:
            return False

    def text_copy_selection(self, event=None):
        '''copies the selection to clipboard if text is selected,\ndoes nothing otherwise.\nreturn: true if it has copied to clipboard, false if nothing was selected.'''
        if self.selection_present():
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())
            return True
        return False

    def text_delete_selection(self, event=None):
        '''deletes the selection if text is selected,\ndoes nothing otherwise.\nreturn: true if it has deleted, false if nothing was selected.'''
        try:
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            #self.delete(tk.INSERT+"-1c")
            return False
        return True

    def text_paste(self, event=None):
        '''pastes text from clipboard if can_paste() returns True. replaces the current selection if text is selected. Return: true if text has been pasted.'''
        if self.can_paste():
            self.text_delete_selection()
            self.insert(tk.INSERT, self.clipboard_get())
            return True
        return False

    def can_paste(self):
        '''True if not readonly and clipboard is not empty'''
        if self.readonly():
            return False
        try:
            return self.clipboard_get()!=''
        except tk.TclError:
            return False
        

def _key_event_enabled(self, event):
    if event.keysym.lower()=='a' and event.state&tkc.MOD_CTRL:
        self.select_all()
        return RETURN_CODE_BREAK
    return None

def _key_event_disabled(self, event):
    if _key_event_enabled(self, event)==RETURN_CODE_BREAK:
        return RETURN_CODE_BREAK
    # return None => default event listener will be called
    # return "break" => event is finished
    if event.keysym.lower()=='c' and event.state&tkc.MOD_CTRL:
        #log.debug("ctrl-c pass through")
        return None 
    if event.keycode in tkc.KEYCODES_MOVE_CURSOR:
        return None
    if event.keycode == tkc.KEYCODE_TAB:
        return None
    #log.debug("char: {e.char} | keycode: {e.keycode} | keysym: {e.keysym} | state: {e.state}".format(e=event))
    return RETURN_CODE_BREAK


class Entry(tk.Entry, WidgetWithContextMenu):
    def __init__(self, master=None, **kw):
        text = kw.pop('text', None)
        if tkc.TEXTVARIABLE in kw:
            self.var = kw[tkc.TEXTVARIABLE]
        else:
            self.var = tk.StringVar()
            kw[tkc.TEXTVARIABLE] = self.var
        WidgetWithContextMenu.__init__(self)
        self.process_keywordargs(kw)
        tk.Entry.__init__(self, master, **kw)
        self.set_contextmenu_from_keywordargs()
        if text:
            self.set_value(self, text, force=True)

    def get_value(self):
        return get_text(self)

    def set_value(self, text, force=True):
        '''force=True: set text regardless of state. force=False: does *not* set text if state is disabled.'''
        if force:
            self.var.set(text)
        else:
            self.delete(0, tk.END)
            self.insert(0, text)

    def text_copy_selection(self, event=None):
        '''copies the selection to clipboard if text is selected,\ndoes nothing otherwise.\nreturn: true if it has copied to clipboard, false if nothing was selected.'''
        if self.selection_present():
            self.clipboard_clear()
            self.clipboard_append(self.selection_get())
            return True
        return False

    def text_delete_selection(self, event=None):
        '''deletes the selected text if text is selected,\ndoes nothing otherwise.\nreturn: true if it has deleted, false if nothing was selected.'''
        try:
            self.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            return False
        return True

    def text_paste(self, event=None):
        '''pastes text from clipboard if can_paste() returns True. replaces the current selection if text is selected. Returns true if text has been pasted.'''
        if self.can_paste():
            self.text_delete_selection()
            self.insert(tk.INSERT, self.clipboard_get())
            return True
        return False

    def can_paste(self):
        '''True if clipboard is not empty'''
        try:
            return self.clipboard_get()!=''
        except tk.TclError:
            return False

#http://stackoverflow.com/questions/1602106/in-pythons-tkinter-how-can-i-make-a-label-such-that-you-can-select-the-text-wi
#TODO: try ttk.Label(takefocus=true)
class LabelSelectable(Entry):
    def __init__(self, master=None, **kw):
        text = kw.pop('text', None)
        autounselect = kw.pop('autounselect', True)
        #self.var = kw.pop('textvariable', tk.StringVar()) # what would that be needed for??
        #kw['textvariable'] = self.var
        Entry.__init__(self, master, **kw)
        try:
            bg = self.master.cget('bg')
        except tk.TclError:
            s = self.master['style']
            bg = ttk.Style().lookup(s, 'background')
        self.configure(
            bg=bg,
            insertbackground = bg, # cursor color
            relief=tk.FLAT,
            highlightthickness=0,
            #state='readonly',
        )
        if text!=None:
            set_text(self, text)
        #self.bind("<Key>", lambda event: _key_event_disabled(self, event))
        self.bind("<Key>", lambda event: _key_event_disabled(self, event))
        if autounselect:
            self.bind("<FocusOut>", self._on_focus_out)
        #TODO
        #problems with text:
        # not text
        # no text variable
        # not changeable when deactivated
        # no flexible width !!!
        pass

    def insert(self, index, string):
        tk.Entry.insert(self, index, string)
        self.configure(width=len(self.get()))

##    def __setitem__(self, key, value):
##        supersetitem = tk.Entry.__setitem__
##        if key==tkc.TEXT:
##            #self.configure(text=value, width=len(text))
##            supersetitem(self, key, value)
##            supersetitem(self, 'width', len(value))
##            log.debug("set length to {0}".format(len(value)))
##        else:
##            supersetitem(self, key, value)

    def select_all(self):
        self.select_range(0, tk.END)

    def _on_focus_out(self, event=None):
        try:
            wf = self.focus_get()
        except KeyError:
            wf = None
        if wf!=None:
            self.remove_selection()

    def remove_selection(self, event=None):
        #self.select_range(0, 0)
        self.selection_clear()

    def text_paste(self, event=None):
        '''overriedes the method of the superclass with doing nothing. Returns False.'''
        return False


class LabelSelectableWithLabel(LabelSelectable):
    def __init__(self, master=None, **kw):
        imagepath = kw.pop('imagepath', None)
        self.frame = tk.Frame(master)
        LabelSelectable.__init__(self, self.frame, **kw)
        self.label = tk.Label(self.frame)
        self.label.pack(side=tk.LEFT)
        tk.Pack.pack(self, side=tk.LEFT)
        if imagepath!=None:
            self.image = create_image(imagepath)
            self.label.configure(image=self.image)

        # based on /usr/lib/python2.7/lib-tk/ScrolledText.py
        # Copy geometry methods of self.frame without overriding Entry methods -- hack!
        text_meths = vars(tk.Entry).keys()
        methods = tuple(vars(tk.Pack).keys()) + tuple(vars(tk.Grid).keys()) + tuple(vars(tk.Place).keys())
        methods = set(methods).difference(text_meths)
        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def __str__(self):
        return str(self.frame)


class TextReadonly(tk.Text):

    def __init__(self, master, **kw):
        text = kw.pop('text', None)

        try:
            bg = master.cget('bg')
        except tk.TclError:
            s = master['style']
            bg = ttk.Style().lookup(s, 'background')
        kw.setdefault('bg', bg)
        kw.setdefault('insertbackground', bg)
        kw.setdefault('relief', tk.FLAT)
        kw.setdefault('highlightthickness', 0)

        tk.Text.__init__(self, master, **kw)
        self.bind("<Key>", lambda event: _key_event_disabled(self, event))

        if text!=None:
            set_text(self, text)

class ScrolledTextReadonly(ScrolledText):

    """ScrolledText has a readonly=True option.
    In contrast to that, this class also changes the visual appearance."""

    def __init__(self, master, **kw):
        text = kw.pop('text', None)

        try:
            bg = master.cget('bg')
        except tk.TclError:
            s = master['style']
            bg = ttk.Style().lookup(s, 'background')
        kw.setdefault('bg', bg)
        kw.setdefault('insertbackground', bg)
        kw.setdefault('relief', tk.FLAT)
        kw.setdefault('highlightthickness', 0)

        ScrolledText.__init__(self, master, **kw)
        self.bind("<Key>", lambda event: _key_event_disabled(self, event))

        if text!=None:
            set_text(self, text)
        
        

#http://effbot.org/zone/tkinter-scrollbar-patterns.htm
class AutoScrolledText(ScrolledText):

    def __init__(self, master=None, **kwargs):
        #tkText.Text.pack(self, side=tk.TOP, fill=tkText.BOTH, expand=True)
        self.frame_ver = tkText.Frame(master)
        ScrolledText.__init__(self, self.frame_ver, **kwargs)
        self.configure(yscrollcommand=self._on_scroll)
        self.pack(expand=True, fill=tk.BOTH)
        self.checkbox_auto_scroll = Checkbutton(self.frame_ver, value=True, text="scroll automatically to end") #TODO: settings
        self.checkbox_auto_scroll.pack(side=tk.BOTTOM, anchor=tk.W)

        # taken from /usr/lib/python2.7/lib-tk/ScrolledText.py
        # Copy geometry methods of self.frame without overriding Text
        # methods -- hack!
        text_meths = vars(tkText.Text).keys()
        methods = tuple(vars(tkText.Pack).keys()) + tuple(vars(tkText.Grid).keys()) + tuple(vars(tkText.Place).keys())
        methods = set(methods).difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame_ver, m))

    def auto_scroll(self, value=None):
        if value==None:
            return self.checkbox_auto_scroll.get_value()
        else:
            self.checkbox_auto_scroll.set_value(value)

    def _on_scroll(self, y0, y1):
        # y0<y1 => y0 is upper edge, y1 is lower edge.
        self.vbar.set(y0, y1)
        self.checkbox_auto_scroll.set_value(float(y1)>=1)

    def append(self, chars, tags=None):
        self.insert(tk.END, chars, tags)
        if self.auto_scroll():
            self.yview(tk.END)


class Indentation(tk.Label):
    WIDTH_INDENTATION_LEVEL = 3
    def __init__(self, master=None, **kw):
        level = kw.pop('level', 1)
        tk.Label.__init__(self, master, width=level*self.WIDTH_INDENTATION_LEVEL)


Stretch = tk.Frame
##class Stretch(tk.Frame):
##
##    def pack(self, **kw):
##        dict.setdefault(
##        tk.Pack.pack(**kw)


class HideableFrame(tk.Frame):
##    def __init__(self, master=None, **kw):
##        pack = kw.pop('pack', None)
##        grid = kw.pop('grid', None)
##        ngms = (pack, grid).count(None) # number of geometry managers
##        if ngms>1:
##            raise ValueError, "got %s geometry managers to use. please decide on one." % (ngms,)
##        elif pack!=None:
##            self._geometry_manager = self.pack
##            self._geometry_manager_config = pack
##        elif pack!=None:
##            self._geometry_manager = self.grid
##            self._geometry_manager_config = grid
##        else:
##            raise ValueError, "please specify a geometry manager"
##        tk.Frame.__init__(self, mater, **kw)
##
##    def set_geometry_manager(self, geometry_manager, geometry_manager_keywords={}):
##        self._geometry_manager = geometry_manager
##        self._geometry_manager_config = geometry_manager_keywords

    def pack(self, **kw):
        self._geometry_manager = tk.Pack.pack
        self._geometry_manager_config = kw

    def grid(self, **kw):
        self._geometry_manager = tk.Grid.grid
        self._geometry_manager_config = kw

    def show(self):
        self._geometry_manager(self, self._geometry_manager_config)

    def hide(self):
        self.pack_forget()
        self.grid_forget()


class Button(tk.Button):
    def __init__(self, master=None, **kw):
        imagepath = kw.pop('imagepath', None)
        tk.Button.__init__(self, master, **kw)
        if imagepath!=None:
            self.image = create_image(imagepath)
            self.configure(image=self.image)

class ButtonsFrame(tk.Frame):

    BTN_OK     = 'ok'
    BTN_YES    = 'yes'
    BTN_NO     = 'no'
    BTN_CANCEL = 'cancel'
    
    def __init__(self, master, **kw):
        '''This frame should be packed to fill x direction.
            If default=True (and it is initially True) the yes or ok button will be marked as the default button (unless the keyword arguments for the buttons suggest otherwise).
            If a button is marked as default it is bound to the <Return> event on the toplevel window.
            If escape=True (and it is initially True) the event <Escape> will be bound to the cancel button on the toplevel window (if there is a cancel button).'''
        #TODO: padding
        default = kw.pop(tkc.DEFAULT, True)
        escape  = kw.pop('escape', True)
        kw_cancel = kw.pop(self.BTN_CANCEL, None)
        if self.BTN_YES in kw:
            mode = self.BTN_YES
            kw_yes = kw.pop(self.BTN_YES)
            kw_no  = kw.pop(self.BTN_NO)
            if default and not tkc.DEFAULT_ACTIVE in (
                    kw_yes.get(tkc.DEFAULT, tk.DISABLED),
                    kw_no.get(tkc.DEFAULT, tk.DISABLED),
                    kw_cancel.get(tkc.DEFAULT, tk.DISABLED) if kw_cancel!=None else tk.DISABLED,
            ):
                kw_yes.setdefault(tkc.DEFAULT, tkc.DEFAULT_ACTIVE)
        else:
            mode = self.BTN_OK
            kw_ok = kw.pop(self.BTN_OK)
            if default and not tkc.DEFAULT_ACTIVE in (
                    kw_ok.get(tkc.DEFAULT, tk.DISABLED),
                    kw_cancel.get(tkc.DEFAULT, tk.DISABLED) if kw_cancel!=None else tk.DISABLED,
            ):
                kw_ok.setdefault(tkc.DEFAULT, tkc.DEFAULT_ACTIVE)

        tk.Frame.__init__(self, master, **kw)

        if kw_cancel!=None:
            self.button_cancel = Button(self, **kw_cancel)
        else:
            self.button_cancel = None

        # I am using the same order like tkMessageBox
        if mode==self.BTN_YES:
            self.button_yes = Button(self, **kw_yes)
            self.button_no  = Button(self, **kw_no)
            self._bind_if_default(self.button_yes) or self._bind_if_default(self.button_no) or self._bind_if_default(self.button_cancel)
            if which_os_am_i_on.mac():
                self.button_yes.pack(side=tk.RIGHT)
                self.button_no.pack(side=tk.RIGHT)
                if self.button_cancel!=None:
                    self.button_cancel.pack(side=tk.LEFT)
            else:
                if self.button_cancel!=None:
                    self.button_cancel.pack(side=tk.RIGHT)
                self.button_no.pack(side=tk.RIGHT)
                self.button_yes.pack(side=tk.RIGHT)
        else:
            self.button_ok = Button(self, **kw_ok)
            self._bind_if_default(self.button_ok) or self._bind_if_default(self.button_cancel)
            if which_os_am_i_on.mac():
                self.button_ok.pack(side=tk.RIGHT)
                if self.button_cancel!=None:
                    self.button_cancel.pack(side=tk.RIGHT)
            else:
                if self.button_cancel!=None:
                    self.button_cancel.pack(side=tk.RIGHT)
                self.button_ok.pack(side=tk.RIGHT)
        if escape and self.button_cancel!=None:
            self.winfo_toplevel().bind('<Escape>', lambda e: only(self.button_cancel.invoke()))

    def _bind_if_default(self, btn):
        if btn==None:
            return False
        if btn[tkc.DEFAULT]==tkc.DEFAULT_ACTIVE:
            log.debug("bind default button: {0!r}".format(btn['text']))
            self.winfo_toplevel().bind('<Return>', lambda e: only(btn.invoke()))
            return True
        return False



class DetailsFrame(tk.Frame):

    BITMAP_DATA_EXPAND = """
#define expand_width 11
#define expand_height 11
static unsigned char expand_bits[] = {
   0x00, 0x00, 0x10, 0x00, 0x30, 0x00, 0x60, 0x00, 0xc0, 0x00, 0x80, 0x01,
   0xc0, 0x00, 0x60, 0x00, 0x30, 0x00, 0x10, 0x00, 0x00, 0x00 };"""
    BITMAP_DATA_COLLAPSE = """
#define collapse_width 11
#define collapse_height 11
static unsigned char collapse_bits[] = {
   0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x06, 0x03, 0x8c, 0x01,
   0xd8, 0x00, 0x70, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00 };"""
    BITMAP_MASK = """
#define circle_mask_width 11
#define circle_mask_height 11
static unsigned char circle_mask_bits[] = {
   0xf8, 0x00, 0xfc, 0x01, 0xfe, 0x03, 0xff, 0x07, 0xff, 0x07, 0xff, 0x07,
   0xff, 0x07, 0xff, 0x07, 0xfe, 0x03, 0xfc, 0x01, 0xf8, 0x00 };"""

    __bitmaps_to_be_created = True
    @classmethod
    def create_bitmaps(cls):
        if cls.__bitmaps_to_be_created:
            cls.__bitmaps_to_be_created = False
            
            chk = tk.Checkbutton()
            cls._normalcolor = chk['background']
            cls._activecolor = chk['activebackground']
            bg = cls._normalcolor
            
            cls.bitmap_expand = tk.BitmapImage(data=cls.BITMAP_DATA_EXPAND, maskdata=cls.BITMAP_MASK, background=bg)
            cls.bitmap_collapse = tk.BitmapImage(data=cls.BITMAP_DATA_COLLAPSE, maskdata=cls.BITMAP_MASK, background=bg)
    
    @classmethod
    def reset_bitmaps(cls):
        cls.__bitmaps_to_be_created = True
        del cls.bitmap_expand
        del cls.bitmap_collapse
    
    
    def __init__(self, master=None, **kw):
        # create bitmaps
        self.create_bitmaps()

        # init
        self.parentframe = tk.Frame(master)
        self.checkbutton = tk.Label(self.parentframe, compound=tk.LEFT, relief=tkc.RELIEF_FLAT, pady=0, padx=5, takefocus=True)
        self.checkbutton.pack(side=tk.TOP, anchor=tk.W)
        self.checkbutton.var = tk.IntVar(self.checkbutton)
        self.checkbutton.bind('<1>', self.toggle_expanded)
        tk.Frame.__init__(self, self.parentframe)
        self.trace(self._update_show_hide)
        kw.setdefault('expanded', False)
        self.configure(**kw)

        # checkbutton change color on hover (both Button and Checkbutton have this but for both the relief is making trouble)
        self.checkbutton.bind('<Enter>', lambda event: self.checkbutton.config(bg=self._activecolor))
        self.checkbutton.bind('<Leave>', lambda event: self.checkbutton.config(bg=self._normalcolor))

        # pack, grid, place (based on /usr/lib/python2.7/lib-tk/ScrolledText.py)
        geometry_manager_methods = set(tuple(vars(tk.Pack).keys()) + tuple(vars(tk.Grid).keys()) + tuple(vars(tk.Place).keys()))#.difference(vars(tk.Frame)) ## vars(tk.Frame) are all private anyway
        for m in geometry_manager_methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.parentframe, m))

    def configure(self, **kw):
        self._label_expand = self._label_collapse = kw.pop('label', None)
        self._label_expand = kw.pop('label_expand', self._label_expand)
        self._label_collapse = kw.pop('label_collapse', self._label_collapse)
        # nice idea but relief is ignored anyway
        #self._relief_expand = self._relief_collapse = kw.pop('relief', None)
        #self._relief_expand = kw.pop('relief_expand', self._relief_expand if self._relief_expand!=None else tkc.RELIEF_FLAT)
        #self._relief_collapse = kw.pop('relief_collapse', self._relief_collapse if self._relief_collapse!=None else tkc.RELIEF_SUNKEN)
        expanded = kw.pop('expanded', None)
        selfkw = dict()
        bg = None
        for key in ('bg', 'background'):
            if key in kw:
                selfkw[key] = kw[key]
                bg = kw[key]
        if bg!=None:
            self.checkbutton.configure(background=bg)
            self._normalcolor = bg
        self._activecolor = kw.pop('activebackground', self._activecolor)

        self.parentframe.configure(**kw)
        tk.Frame.configure(self,**selfkw)
        if expanded==None:
            self._update_show_hide(self.is_expanded())
        elif expanded==self.is_expanded():
            self._update_show_hide(expanded)
        else:
            self.set_expanded(expanded)

    config=configure
        

    def _update_show_hide(self, is_expanded):
        if is_expanded:
            tk.Pack.pack(self, expand=True, fill=tk.BOTH)
            self.checkbutton.configure(image=self.bitmap_collapse, text=self._label_collapse)
            #self.parentframe.configure(relief=self._relief_collapse)
        else:
            tk.Pack.pack_forget(self)
            self.checkbutton.configure(image=self.bitmap_expand, text=self._label_expand)
            #self.parentframe.configure(relief=self._relief_expand)

    def trace(self, command):
        '''command(new_value) will be called when details are expanded or collapsed'''
        self.checkbutton.var.trace(tkc.TRACE_WRITE, lambda varname,index,operation: command(self.is_expanded()))

    def is_expanded(self):
        return bool(self.checkbutton.var.get())

    def set_expanded(self, is_expanded):
        self.checkbutton.var.set(bool(is_expanded))

    def expand(self):
        self.set_expanded(True)

    def collapse(self):
        self.set_expanded(False)

    def toggle_expanded(self, event=None):
        self.set_expanded(not self.is_expanded())


class Menu(tk.Menu):

    _PREFIX_INDEX = '_index_'
    _PREFIX_MENU = 'menu_'

    tearoff = False

    def __init__(self, master=None, **kw):
        if tkc.KEY_TEAROFF not in kw:
            kw[tkc.KEY_TEAROFF] = self.tearoff
        tk.Menu.__init__(self, master, kw)

    def add_named_command(self, name, **kw):
        setattr(self, self._PREFIX_INDEX+name, kw['label'])
        self.add_command(**kw)

    def add_named_checkbutton(self, name, **kw):
        if 'variable' in kw:
            var = kw['variable']
        else:
            var = tk.BooleanVar(value=kw.pop('value', False))
            kw['variable'] = var
        command = kw.pop('command')
        assert command!=None
        var.trace(tkc.TRACE_WRITE, lambda varname,index,operation: command(bool(var.get())))
        setattr(self, self._PREFIX_INDEX+name, kw['label'])
        setattr(self, self._PREFIX_INDEX+name+'_variable', var)
        self.add_checkbutton(**kw)

    def set_named_checkbutton(self, name, value):
        var = getattr(self, self._PREFIX_INDEX+name+'_variable')
        var.set(value)

    def add_named_cascade(self, name, **kw):
        menu = kw.pop(tkc.KEY_MENU, None)
        if menu==None:
            tearoff = kw.pop(tkc.KEY_TEAROFF, self.tearoff)
            menu = Menu(self, tearoff=tearoff)
        kw[tkc.KEY_MENU] = menu
        visible = bool(kw.pop('visible', True))
        menu.label = kw['label']
        setattr(self, self._PREFIX_INDEX+name, kw['label'])
        setattr(self, self._PREFIX_MENU+name, menu)
        if visible:
            self.add_cascade(**kw)
        menu._visible = visible
        return menu

    def set_cascade_visibility(self, menu, visible):
        visible = bool(visible)
        if visible == menu._visible:
            return
        if visible:
            self.add_cascade(menu=menu, label=menu.label)
            menu._visible = True
        else:
            self.delete(menu.label)
            menu._visible = False

    def entry_disable(self, name):
        i = getattr(self, self._PREFIX_INDEX+name)
        self.entryconfig(i, state=tk.DISABLED)

    def entry_enable(self, name):
        i = getattr(self, self._PREFIX_INDEX+name)
        self.entryconfig(i, state=tk.NORMAL)

    def set_entry_enabled(self, name, enabled):
        if enabled:
            self.entry_enable(name)
        else:
            self.entry_disable(name)

    def entries_disable(self, *names):
        names = self._parse_names(names)
        #log.debug("disable: {0}".format(names))
        for name in names:
            self.entry_disable(name)

    def entries_enable(self, *names):
        names = self._parse_names(names)
        #log.debug("enable: {0}".format(names))
        for name in names:
            self.entry_enable(name)

    def _parse_names(self, names):
        if len(names)==1 and names[0] == '*':
            names = []
            for attr in dir(self):
                if attr[:len(self._PREFIX_INDEX)]==self._PREFIX_INDEX:
                    names.append(attr[len(self._PREFIX_INDEX):])
        return names

    def invoke(self, btn):
        i = self.to_index(btn)
        tk.Menu.invoke(self, i)

    def to_index(self, name):
        if isinstance(name, int) or name==tk.END:
            return name
        else:
            return getattr(self, self._PREFIX_INDEX+name)

    def shortcut(self, name, key):
        '''create a shortcut Alt+key by underlining one character of the label. This is mainly intended for the main-menus of the window-menubar. If key is not contained in the label, no shortcut can be created. In that case an error is logged and this function returns False.'''
        index = getattr(self, self._PREFIX_INDEX+name)
        label = self.entrycget(index, 'label')
        i = label.find(key)
        if i<0:
            i = label.find(key.swapcase())
        if i<0:
            log.error("cannot create shortcut {key!r} to menu entry {label!r} because key is not contained in label".format(key=key, label=label))
            return False
        self.entryconfig(index, underline=i)
        return True

    def open_menu(self, menu):
        log.debug("open_menu({menu})".format(menu=menu.label))
        #TODO: pause update screen in this function (is that even possible?)
        # init
        focussed_widget = self.focus_displayof()
        t = tk.Toplevel(menu)
        t.overrideredirect(True)
        x = self.master.winfo_rootx()
        y = self.master.winfo_rooty()
        x += self.master.winfo_width()
        if not hasattr(menu, 'width'):
            menu.tk_popup(x,y)
            menu.width = menu.winfo_width()
            #print("background: "+menu.entrycget(0, 'background'))
            #print("activebackground: "+menu.entrycget(0, 'activebackground'))
            menu.unpost()
            menu.update()
        padding = 6
        l = tk.Label(t, text=menu.label, relief=tkc.RELIEF_RAISED, padx=padding, pady=padding)
        l['background'] = l['activebackground']
        l.pack()
        t.update_idletasks()
        t.width = t.winfo_width()
        t.height = t.winfo_height()

        # correct setup
        t.geometry('{width}x{height}+{x}+{y}'.format(x=x-t.width, y=y-t.height, width=t.width, height=t.height))
        menu.tk_popup(x-menu.width,y)
        menu.focus_force()# yes, I really need a focus_force here because the update above seems to pass the focus to a different application
        def close(event=None):
            log.debug("close")
            menu.unbind('<Escape>', fid_esc) # to avoid conflict when menu is opened normally
            menu.unbind('<FocusOut>', fid_foc) # to avoid double close
            #menu.unbind('<Button-1>', fid_clk) # to avoid double close
            #TODO: menu_open, Escape, Alt-f, Escape returns focus but does not close menu
            menu.unpost()
            t.destroy()
            focussed_widget.focus()
            return tkc.BREAK
        fid_esc = menu.bind('<Escape>', close, add=True)
        fid_foc = menu.bind('<FocusOut>', close, add=True)
        #menu.bind('<Button-1>', lambda event: None, add=True)
        #TODO: does not close on FIRST open
        l.bind('<Button-1>', close)
        self.update()


# ========== other classes ==========

# http://effbot.org/zone/tkinter-busy.htm
class CursorManager(object):

    def __init__(self, widget, set_cursor=tkc.CURSOR_WATCH, reset_cursor=tkc.CURSOR_ARROW):
        self.toplevel = widget.winfo_toplevel()
        self.default_set_cursor = set_cursor
        self.default_reset_cursor = reset_cursor
        self._w_cursors = dict()
        self._is_cursor_changed = False

    def set_cursor(self, cursor=None, widget=None):
        if cursor is None:
            cursor = self.default_set_cursor
        if widget is None:
            w = self.toplevel
        else:
            w = widget

        #log.debug("=====   set cursor =====")
        self._is_cursor_changed = True
        try:
            w_cursor = w.cget(tkc.KEY_CURSOR)
            if w_cursor != cursor:
                # originally it was str(w).
                # however str(ScrolledText)==str(ScrolledText.frame) # how can that be???
                # repr(ScrolledText)!=repr(ScrolledText.frame) # if this is not valid for str, are there exceptions for repr, too?
                # id(ScrolledText)!=id(ScrolledText.frame) # is this more difficult than str or repr?
                key = repr(w)
                if key not in self._w_cursors:
                    self._w_cursors[key] = (w, w_cursor) #TODO: only if not contained
                    #log.debug("set cursor of {widget!r} to {cursor!r}".format(widget=w, cursor=cursor))
                else:
                    log.debug("{widget!r} already contained".format(widget=w))
                w.config(cursor=cursor)
        except tk.TclError:
            log.warning("failed to set cursor of {widget!r} to {cursor!r}".format(widget=w, cursor=cursor))
        
        for w in w.children.values():
            self.set_cursor(cursor, w)

    def reset_cursor(self):
        log.debug("===== reset cursor =====")
        self._is_cursor_changed = False
        for w, w_cursor in self._w_cursors.values():
            if w_cursor=="":
                w_cursor = self.default_reset_cursor
            try:
                w.config(cursor=w_cursor)
                #log.debug("reset cursor of {widget!r} to {cursor!r}".format(widget=w, cursor=w_cursor))
            except tk.TclError:
                log.warning("failed to reset cursor for {widget!r}".format(widget=w))
        self._w_cursors = dict()

    def is_cursor_changed(self):
        return self._is_cursor_changed


# ========== test ==========

if __name__=='__main__':
    import sys
    logging.basicConfig(level=0, format="[%(levelname)-8s] %(message)s", stream=sys.stdout, disable_existing_loggers=True)
    import time
    #_ = lambda x: x
    toggle_readonly = True
    class Test:
        i = 0
        def fill(self):
            b[tkc.TEXT] = "pause"
            b[tkc.COMMAND] = self.pause
            if toggle_readonly: t.readonly(True)
            self.is_running = True
            while self.is_running:
                t.append(str(self.i)+"\n")
                self.i += 1
                if self.i<25:
                    continue
                for i in xrange(10):
                    t.update()
                    time.sleep(0.1)

        def pause(self):
            self.is_running = False
            b[tkc.TEXT] = "continue"
            b[tkc.COMMAND] = self.fill
            if toggle_readonly: t.readonly(False)

    AutoScrolledText.default_contextmenu = (
        ('copy', 'copy', AutoScrolledText.text_copy_selection),
        ('paste', 'paste', AutoScrolledText.text_paste)
    )
    def on_contextmenu_open(self):
        self.contextmenu.set_entry_enabled('copy', self.selection_present())
        self.contextmenu.set_entry_enabled('paste', self.can_paste())
    AutoScrolledText.default_on_contextmenu_open = on_contextmenu_open
    AutoScrolledText.default_on_readonly_enabled = lambda self: self.contextmenu.entry_disable('paste')
    AutoScrolledText.default_on_readonly_disabled = lambda self: self.contextmenu.set_entry_enabled('paste', self.can_paste())

    LabelSelectable.default_contextmenu = (
        ('copy', 'copy', LabelSelectable.text_copy_selection),
    )

    def ask_to_close():
        t = tk.Toplevel()
        LabelSelectable(t, text="Are you sure you want to quit?").pack()
        ButtonsFrame(t,
            yes = dict(text="Yes", command=lambda: only(t.destroy(), r.destroy(), r.quit())),
            no  = dict(text="No", command=lambda: only(t.destroy())),
            cancel = dict(text="Cancel", command=lambda: only(t.destroy()))
        ).pack(side=tk.BOTTOM, fill=tk.X)

    m = Test()
    r = tk.Tk()
    
    menu = Menu(r)
    menu_file = menu.add_named_cascade('file', label="File")
    menu_file.add_named_command('save', label="Save", command=lambda: log.info("save"))
    menu_file.add_named_command('open', label="Open", command=lambda: log.info("open"))
    menu_edit = menu.add_named_cascade('edit', label="Edit")
    menu_edit.add_named_command('add', label="Add", command=lambda: log.info("add"))
    menu_edit.add_named_command('remove', label="Remove", command=lambda: log.info("rm"))
    menu.shortcut('file', 'f')
    menu.shortcut('edit', 'e')
    r.bind('<Control-f>', lambda event: menu.open_menu(menu_file))
    r.bind('<Control-e>', lambda event: menu.open_menu(menu_edit))
    
    r.config(menu=menu)
    l = LabelSelectableWithLabel(r,
        text="bla bla bla",
        imagepath="symbole/resized/count.png"
    )# textvariable=tk.StringVar(value="some test app:"))
    l.pack(side=tk.TOP, fill=tk.X)
    t = AutoScrolledText(r,
        readonly=not toggle_readonly,
        #on_readonly_enabled = lambda self: self.contextmenu.entries_disable('*')
    )
    t.pack(expand=True, fill=tk.BOTH)
    details = DetailsFrame(r, label='Details', label_expand='Expand Details', label_collapse='Collapse Details')
    details.pack(expand=True, fill=tk.X)
    LabelSelectable(details, text="This is just a test. Nothing more.").pack(side=tk.LEFT)
    buttons_frame = ButtonsFrame(r,
        ok = dict(text="Start", command=m.fill),
        cancel = dict(text="Close", command=ask_to_close)
    )
    buttons_frame.pack(side=tk.BOTTOM, fill=tk.X)
    b = buttons_frame.button_ok
    r.mainloop()
