import os
import sys
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.messagebox as msgbox
import tkinter.filedialog as filedialog
from tkcalendar import DateEntry
from file_manager.core import app_config
from file_manager.core.api import (make_db, write_new_config, publish_folder,
                                   update_config, attribute_values_list, search_cfgs,
                                   make_if_not_exists, remove_folder)
from file_manager.core.config_manager.fs_operations import has_config
from file_manager.core.config_manager.models import Config
from file_manager.core.config_manager.config_rw import parse_config, get_attributes_only
from .helpers import path_is_parent, shorten_path, rewrite_tf


class GUIApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.switch_frame(LoadingFrame)
        make_if_not_exists()
        self.switch_frame(MainFrame)

    def switch_frame(self, frame_class):
        """Destroys current frame and replaces it with a new one"""
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.pack(expand=True, fill='both')


class LoadingFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.geometry('800x700')
        self.master.resizable(False, False)
        self.master.title('File Manager')
        ttk.Label(self, text='LOADING...').pack(expand=True, fill='both')
        ttk.Button(self, text='FDSJDFJSDGBJS').pack(expand=True, fill='both')


class MainFrame(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.geometry('800x700')
        self.master.resizable(False, False)
        self.master.title('File Manager')
        self.create_widgets()

    def make(self):
        self.master.switch_frame(LoadingFrame)
        make_db()
        self.master.switch_frame(MainFrame)

    def create_widgets(self):
        self.grid_rowconfigure(0, weight=20)
        self.grid_rowconfigure(1, weight=20)
        self.grid_rowconfigure(2, weight=20)
        self.grid_rowconfigure(3, weight=20)
        self.grid_rowconfigure(4, weight=20)
        self.grid_columnconfigure(0, weight=100)

        btn_make = ttk.Button(self, text='Make Database',
                              command=self.make).\
            grid(row=0, column=0, padx=15, pady=15, sticky='nswe')
        btn_copy = ttk.Button(self, text='Publish To File Manager',
                              command=lambda: self.master.switch_frame(CopyFrame)).\
            grid(row=1, column=0, padx=15, pady=15, sticky='nswe')
        btn_edit = ttk.Button(self, text='   Edit Folder Configuration',
                              command=lambda: self.master.switch_frame(EditFrame)).\
            grid(row=2, column=0, padx=15, pady=15, sticky='nswe')
        btn_search = ttk.Button(self, text='Search Folder',
                                command=lambda: self.master.switch_frame(SearchFrame)).\
            grid(row=3, column=0, padx=15, pady=15, sticky='nswe')
        btn_quit = ttk.Button(self, text='Quit',
                              command=lambda: sys.exit()).\
            grid(row=4, column=0, columnspan=2,
                 padx=15, pady=15, sticky='nswe')


class CopyFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.geometry('800x700')
        self.master.resizable(False, False)
        self.master.title('Copy')
        self.set_variables()
        self.create_widgets()

    def set_variables(self):
        # initialize variables
        self.attr_vals = attribute_values_list()
        self.attr_names = sorted(self.attr_vals.keys())
        self.path_from = ''
        self.from_dirname = ''
        self.path_to = ''
        self.rel_path_to = ''
        self.config = None
        self.parent_attrs = {}
        self.parent_chkbtn_vars = {}
        self.folder_attrs = {}

    def create_widgets(self):
        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=100)

        # CREATE PATH CONTAINER
        self.path_ct = tk.LabelFrame(self, text='Publish:')
        self.path_ct.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.path_ct.grid_columnconfigure(1, weight=100)
        # create labels
        ttk.Label(self.path_ct, text='From:').\
            grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.path_ct, text='To:').\
            grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.from_txt = tk.Text(self.path_ct, height=2, state='disabled')
        self.from_txt.grid(row=1, column=0, columnspan=2,
                           padx=5, pady=5, sticky='nswe')
        self.to_txt = tk.Text(self.path_ct, height=2, state='disabled')
        self.to_txt.grid(row=3, column=0, columnspan=2,
                         padx=5, pady=5, sticky='nswe')
        # create buttons
        self.btn_from = ttk.Button(self.path_ct, text='Choose Path',
                                   command=self.ask_dir_from)
        self.btn_from.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.btn_to = ttk.Button(self.path_ct, text='Choose Path',
                                 command=self.ask_dir_to)
        self.btn_to.grid(row=2, column=1, padx=5, pady=5, sticky='ew')

        # CREATE FOLDER INFO CONTAINER
        self.info_ct = tk.LabelFrame(self, text='Folder Information:')
        self.info_ct.grid_columnconfigure(1, weight=100)
        self.info_ct.grid_rowconfigure(6, weight=100)
        self.info_ct.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        # create labels
        ttk.Label(self.info_ct, text='Name:').\
            grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Path:').\
            grid(row=1, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Date:').\
            grid(row=2, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Version:').\
            grid(row=3, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Comment:').\
            grid(row=4, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Attributes:').\
            grid(row=5, column=0, padx=5, pady=5, sticky='w')
        # create entry fields and dynamic label for path
        self.entry_name = ttk.Entry(self.info_ct)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.path_txt = tk.Text(self.info_ct, height=2, state='disabled')
        self.path_txt.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.entry_date = DateEntry(self.info_ct)
        self.entry_date.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.entry_ver = ttk.Entry(self.info_ct)
        self.entry_ver.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        self.entry_ver.insert('end', '0')
        self.comment_text = tk.Text(self.info_ct, height=4)
        self.comment_text.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        # create a scrollable frame for attributes
        self.canvas1 = tk.Canvas(self.info_ct)
        self.scrollable_frame1 = tk.Frame(self.canvas1)
        self.vsb1 = tk.Scrollbar(self.info_ct,
                                 orient='vertical', command=self.canvas1.yview)
        self.canvas1.configure(yscrollcommand=self.vsb1.set)

        self.canvas1.grid(row=6, column=0, columnspan=2, sticky='nswe')
        self.vsb1.grid(row=6, column=3, sticky='ns')
        self.canvas1.create_window((0, 0),
                                   window=self.scrollable_frame1, anchor='nw')
        self.scrollable_frame1.bind('<Configure>', self.on_frame_configure1)

        # CREATE ATTRIBUTE CHOOSE CONTAINER
        self.attr_ct = tk.LabelFrame(self, text='Add Attributes:')
        self.attr_ct.grid(row=0, column=1, rowspan=2,
                          padx=5, pady=5, sticky='nsew')
        self.attr_ct.columnconfigure(0, weight=40)
        self.attr_ct.columnconfigure(1, weight=40)
        self.attr_ct.columnconfigure(2, weight=20)
        self.attr_ct.rowconfigure(1, weight=100)
        self.canvas2 = tk.Canvas(self.attr_ct)
        self.scrollable_frame2 = tk.Frame(self.canvas2)
        self.vsb2 = tk.Scrollbar(self.attr_ct,
                                 orient='vertical', command=self.canvas2.yview)
        self.canvas2.configure(yscrollcommand=self.vsb2.set)

        self.canvas2.grid(row=1, column=0, columnspan=3, sticky='nswe')
        self.vsb2.grid(row=1, column=3, sticky='ns')
        self.canvas2.create_window((0, 0),
                                   window=self.scrollable_frame2, anchor='nw')
        self.scrollable_frame2.bind('<Configure>', self.on_frame_configure2)
        self.draw_parent_attrs()
        self.choose_cat = ttk.Combobox(
            self.attr_ct, values=self.attr_names, state='readonly')
        if len(self.attr_names) > 0:
            self.choose_cat.current(0)
        self.choose_cat.grid(row=0, column=0, pady=5, sticky='ew')
        self.choose_cat.bind('<<ComboboxSelected>>', self.clear_value)
        self.choose_value = ttk.Combobox(
            self.attr_ct, postcommand=self.change_values_list)
        self.choose_value.grid(row=0, column=1, pady=5, sticky='ew')
        self.btn_add = ttk.Button(self.attr_ct, text='Add',
                                  command=self.add_attr)
        self.btn_add.grid(row=0, column=2, pady=5, sticky='ew')
        # self.btn_add['command'] = self.add_attr

        # CREATE CONTROL BUTTONS CONTAINER
        self.buttons_ct = tk.Frame(self)
        self.buttons_ct.grid_configure(row=2, column=0, columnspan=2,
                                       padx=5, pady=5, sticky='nsew')
        self.btn_back = ttk.Button(self.buttons_ct, text='Back',
                                   command=lambda: self.master.switch_frame(MainFrame))
        self.btn_back.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.btn_copy = ttk.Button(self.buttons_ct, text='Copy',
                                   command=self.copy_folder)
        self.btn_copy.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.btn_copy_exit = ttk.Button(self.buttons_ct, text='Copy And Exit',
                                        command=self.copy_and_exit)
        self.btn_copy_exit.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
        self.btn_move = ttk.Button(self.buttons_ct, text='Move',
                                   command=self.move_folder)
        self.btn_move.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
        self.btn_move_exit = ttk.Button(self.buttons_ct, text='Move And Exit',
                                        command=self.move_and_exit)
        self.btn_move_exit.grid(row=0, column=4, padx=5, pady=5, sticky='ew')

    def clear_value(self, event):
        self.choose_value.set('')

    def change_values_list(self):
        values = list(sorted(self.attr_vals.get(self.choose_cat.get())))
        self.choose_value.configure(values=values)

    def on_frame_configure1(self, e):
        self.canvas1.configure(scrollregion=self.canvas1.bbox('all'))

    def on_frame_configure2(self, e):
        self.canvas2.configure(scrollregion=self.canvas2.bbox('all'))

    def draw_parent_attrs(self):
        self.checkbutton_variables = {}
        for child in self.scrollable_frame2.winfo_children():
            child.destroy()
        row = 0
        for attr, values in self.parent_attrs.items():
            ttk.Label(self.scrollable_frame2, text=attr + ":").\
                grid(row=row, column=0, sticky='w')
            row += 1
            if values:
                for v in sorted(values):
                    key = (attr, v)
                    checkVar = tk.IntVar()
                    self.parent_chkbtn_vars[key] = checkVar
                    if v in self.folder_attrs.get(attr, set()):
                        checkVar.set(1)
                    else:
                        checkVar.set(0)
                    chckbtn = ttk.Checkbutton(
                        self.scrollable_frame2, text=v, variable=checkVar)
                    chckbtn['command'] = lambda var = checkVar, attr=attr, val=v: self.parent_attribute_checked(
                        var, attr, val)
                    chckbtn.grid(row=row, column=1, sticky='w')
                    row += 1

    def draw_folder_attrs(self):
        for child in self.scrollable_frame1.winfo_children():
            child.destroy()
        row = 0
        for attr, values in self.folder_attrs.items():
            ttk.Label(self.scrollable_frame1, text=attr + ":", border=4).\
                grid(row=row, column=0, sticky='w')
            row += 1
            if values:
                for v in sorted(values):
                    ttk.Label(self.scrollable_frame1, text=v).\
                        grid(row=row, column=1, sticky='w')
                    remove_btn = tk.Button(self.scrollable_frame1,
                                           text='X', bg='red')
                    remove_btn['command'] = lambda attr=attr, val=v: self.remove_attr(
                        attr, val)
                    remove_btn.grid(row=row, column=0, sticky='e', padx=5)
                    row += 1

    def ask_dir_from(self):
        initial_dir = app_config.COPY_PATH if self.path_from == '' else self.path_from
        path = filedialog.askdirectory(initialdir=initial_dir)
        if path:
            if path_is_parent(app_config.ROOT_PATH, path):
                msgbox.showerror(
                    'ERROR', f'"From:" folder must be outside root directory: {app_config.ROOT_PATH}')
                return
            self.from_dirname = os.path.basename(os.path.normpath(path))
            self.entry_name.delete(0, 'end')
            self.entry_name.insert('end', self.from_dirname)
            self.path_from = path
            self.btn_from.configure(text=shorten_path(self.path_from))
            rewrite_tf(self.from_txt, self.path_from)
            if self.rel_path_to != '':
                rewrite_tf(self.path_txt, os.path.join(
                    self.rel_path_to, self.from_dirname))

    def ask_dir_to(self):
        if self.path_from == '':
            msgbox.showerror(
                'ERROR', 'Select "From" folder first')
            return
        initial_dir = app_config.ROOT_PATH if self.path_to == '' else self.path_to
        path = filedialog.askdirectory(initialdir=initial_dir)
        if path:
            if not path_is_parent(app_config.ROOT_PATH, path):
                msgbox.showerror(
                    'ERROR', f'"To:" folder must be inside root directory: {app_config.ROOT_PATH}')
                return
            self.path_to = path
            self.rel_path_to = os.path.relpath(
                self.path_to, app_config.ROOT_PATH)
            rewrite_tf(self.path_txt, os.path.join(
                self.rel_path_to, self.from_dirname))
            rewrite_tf(self.to_txt, self.path_to)
            self.btn_to.configure(text=shorten_path(self.path_to))
            self.parent_attrs = get_attributes_only(self.rel_path_to, {})
            self.draw_parent_attrs()

    def parent_attribute_checked(self, chk, attr, val):
        if chk.get() == 1:
            if attr not in self.folder_attrs:
                self.folder_attrs[attr] = set()
            self.folder_attrs[attr].add(val)
        else:
            self.folder_attrs[attr].discard(val)
            if len(self.folder_attrs[attr]) == 0:
                self.folder_attrs.pop(attr)
        self.draw_folder_attrs()

    def add_attr(self):
        attr = self.choose_cat.get()
        val = self.choose_value.get().strip()
        if val == '':
            return
        if attr not in self.folder_attrs:
            self.folder_attrs[attr] = set()
        self.folder_attrs[attr].add(val)
        if (attr, val) in self.parent_chkbtn_vars:
            self.parent_chkbtn_vars[(attr, val)].set(1)
        self.draw_folder_attrs()

    def remove_attr(self, attr, val):
        if (attr, val) in self.parent_chkbtn_vars:
            self.parent_chkbtn_vars[(attr, val)].set(0)
        self.folder_attrs[attr].discard(val)
        if len(self.folder_attrs[attr]) == 0:
            self.folder_attrs.pop(attr)
        self.draw_folder_attrs()

    def create_folder_config(self):
        if self.path_from:
            msgbox.showerror(
                'ERROR', 'You hawe already selected "From" folder. You can only copy this folder now.')
            return
        if has_config(self.rel_path_to):
            msgbox.showerror(
                'ERROR', 'Can not create config file in this directory. It already has one.')
            return
        cfg = self.create_config()
        if cfg == None:
            msgbox.showerror(
                'ERROR', 'Please fill in all fields.')
            return
        write_new_config(cfg)

    def copy_folder(self):
        if self.path_from == '' or self.path_to == '':
            msgbox.showerror(
                'ERROR', 'Please choose "From" and "To" directories.')
            return
        cfg = self.create_config()
        if cfg == None:
            msgbox.showerror(
                'ERROR', 'Please fill in all fields.')
            return
        p = os.path.join(self.path_to, self.from_dirname)
        try:
            publish_folder(self.path_from, p, cfg)
        except Exception as err:
            msgbox.showerror('ERROR', err)
            return
        msgbox.showinfo('SUCCESS', 'Operation successful!')

    def copy_and_exit(self):
        self.copy_folder()
        self.master.switch_frame(MainFrame)

    def move_folder(self):
        self.copy_folder()
        remove_folder(self.path_from)

    def move_and_exit(self):
        self.move_folder()
        self.master.switch_frame(MainFrame)

    def create_config(self):
        self.from_dirname = self.formate_dirname()
        p = os.path.join(self.path_to, self.from_dirname)
        self.rel_path_to = os.path.relpath(p, app_config.ROOT_PATH)
        name = self.entry_name.get().strip()
        date = self.entry_date.get_date()
        ver = self.entry_ver.get().strip()
        path = self.rel_path_to
        attrs = self.folder_attrs
        spec = {'comment': self.comment_text.get('1.0', 'end-1c')}
        if name == '' or ver == '' or path == '':
            return None
        cfg = Config(name, date, ver, path, attributes=attrs, special=spec)
        print(cfg)
        return cfg

    def formate_dirname(self):
        new_dirname = self.from_dirname
        return new_dirname


class EditFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.geometry('800x700')
        self.master.resizable(False, False)
        self.master.title('Edit')
        self.set_variables()
        self.create_widgets()

    def set_variables(self):
        # initialize variables
        self.path = ''
        self.rel_path = ''
        self.config = None
        self.parent_attrs = {}
        self.parent_chkbtn_vars = {}
        self.folder_attrs = {}
        self.attr_vals = attribute_values_list()
        self.attr_names = sorted(self.attr_vals.keys())

    def create_widgets(self):
        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=100)

        # CREATE PATH CONTAINER
        self.path_ct = tk.LabelFrame(self, text='Edit:')
        self.path_ct.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        self.path_ct.grid_columnconfigure(1, weight=100)
        # create labels
        ttk.Label(self.path_ct, text='Folder:').\
            grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.fp_txt = tk.Text(self.path_ct, height=2, state='disabled')
        self.fp_txt.grid(row=1, column=0, columnspan=2,
                         padx=5, pady=5, sticky='nsew')
        # create buttons
        self.btn_folder = ttk.Button(self.path_ct, text='Choose Path',
                                     command=self.ask_dir)
        self.btn_folder.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

        # CREATE FOLDER INFO CONTAINER
        self.info_ct = tk.LabelFrame(self, text='Folder Information:')
        self.info_ct.grid_columnconfigure(1, weight=100)
        self.info_ct.grid_rowconfigure(6, weight=100)
        self.info_ct.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        # create labels
        ttk.Label(self.info_ct, text='Name:').\
            grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Path:').\
            grid(row=1, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Date:').\
            grid(row=2, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Version:').\
            grid(row=3, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Comment:').\
            grid(row=4, column=0, padx=5, pady=5, sticky='w')
        ttk.Label(self.info_ct, text='Attributes:').\
            grid(row=5, column=0, padx=5, pady=5, sticky='w')
        # create entry fields and dynamic label for path
        self.entry_name = ttk.Entry(self.info_ct)
        self.entry_name.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self.path_txt = tk.Text(self.info_ct, height=2, state='disabled')
        self.path_txt.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.entry_date = DateEntry(self.info_ct)
        self.entry_date.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        self.entry_ver = ttk.Entry(self.info_ct)
        self.entry_ver.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        self.entry_ver.insert('end', '0')
        self.comment_text = tk.Text(self.info_ct, height=4)
        self.comment_text.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        # create a scrollable frame for attributes
        self.canvas1 = tk.Canvas(self.info_ct)
        self.scrollable_frame1 = tk.Frame(self.canvas1)
        self.vsb1 = tk.Scrollbar(self.info_ct,
                                 orient='vertical', command=self.canvas1.yview)
        self.canvas1.configure(yscrollcommand=self.vsb1.set)

        self.canvas1.grid(row=6, column=0, columnspan=2, sticky='nswe')
        self.vsb1.grid(row=6, column=3, sticky='ns')
        self.canvas1.create_window((0, 0),
                                   window=self.scrollable_frame1, anchor='nw')
        self.scrollable_frame1.bind('<Configure>', self.on_frame_configure1)

        # CREATE ATTRIBUTE CHOOSE CONTAINER
        self.attr_ct = tk.LabelFrame(self, text='Add Attributes:')
        self.attr_ct.grid(row=0, column=1, rowspan=2,
                          padx=5, pady=5, sticky='nsew')
        self.attr_ct.columnconfigure(0, weight=40)
        self.attr_ct.columnconfigure(1, weight=40)
        self.attr_ct.columnconfigure(2, weight=20)
        self.attr_ct.rowconfigure(1, weight=100)
        self.canvas2 = tk.Canvas(self.attr_ct)
        self.scrollable_frame2 = tk.Frame(self.canvas2)
        self.vsb2 = tk.Scrollbar(self.attr_ct,
                                 orient='vertical', command=self.canvas2.yview)
        self.canvas2.configure(yscrollcommand=self.vsb2.set)

        self.canvas2.grid(row=1, column=0, columnspan=3, sticky='nswe')
        self.vsb2.grid(row=1, column=3, sticky='ns')
        self.canvas2.create_window((0, 0),
                                   window=self.scrollable_frame2, anchor='nw')
        self.scrollable_frame2.bind('<Configure>', self.on_frame_configure2)
        self.draw_parent_attrs()
        self.choose_cat = ttk.Combobox(
            self.attr_ct, values=self.attr_names, state='readonly')
        if len(self.attr_names) > 0:
            self.choose_cat.current(0)
        self.choose_cat.grid(row=0, column=0, pady=5, sticky='ew')
        self.choose_cat.bind('<<ComboboxSelected>>', self.clear_value)
        self.choose_value = ttk.Combobox(
            self.attr_ct, postcommand=self.change_values_list)
        self.choose_value.grid(row=0, column=1, pady=5, sticky='ew')
        self.btn_add = ttk.Button(self.attr_ct, text='Add',
                                  command=self.add_attr)
        self.btn_add.grid(row=0, column=2, pady=5, sticky='ew')

        # CREATE CONTROL BUTTONS CONTAINER
        self.buttons_ct = tk.Frame(self)
        self.buttons_ct.grid_configure(row=2, column=0, columnspan=2,
                                       padx=5, pady=5, sticky='nsew')
        self.btn_back = ttk.Button(self.buttons_ct, text='Back',
                                   command=lambda: self.master.switch_frame(MainFrame))
        self.btn_back.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.btn_save = ttk.Button(self.buttons_ct, text='Save',
                                   command=self.save_config)
        self.btn_save.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

    def clear_value(self, event):
        self.choose_value.set('')

    def change_values_list(self):
        values = list(sorted(self.attr_vals.get(self.choose_cat.get())))
        self.choose_value.configure(values=values)

    def on_frame_configure1(self, e):
        self.canvas1.configure(scrollregion=self.canvas1.bbox('all'))

    def on_frame_configure2(self, e):
        self.canvas2.configure(scrollregion=self.canvas2.bbox('all'))

    def draw_parent_attrs(self):
        self.checkbutton_variables = {}
        for child in self.scrollable_frame2.winfo_children():
            child.destroy()
        row = 0
        for attr, values in self.parent_attrs.items():
            ttk.Label(self.scrollable_frame2, text=attr + ":").\
                grid(row=row, column=0, sticky='w')
            row += 1
            if values:
                for v in sorted(values):
                    key = (attr, v)
                    checkVar = tk.IntVar()
                    self.parent_chkbtn_vars[key] = checkVar
                    if v in self.folder_attrs.get(attr, set()):
                        checkVar.set(1)
                    else:
                        checkVar.set(0)
                    chckbtn = ttk.Checkbutton(
                        self.scrollable_frame2, text=v, variable=checkVar)
                    chckbtn['command'] = lambda var = checkVar, attr=attr, val=v: self.parent_attribute_checked(
                        var, attr, val)
                    chckbtn.grid(row=row, column=1, sticky='w')
                    row += 1

    def draw_folder_attrs(self):
        for child in self.scrollable_frame1.winfo_children():
            child.destroy()
        row = 0
        if self.folder_attrs == None:
            return
        for attr, values in self.folder_attrs.items():
            ttk.Label(self.scrollable_frame1, text=attr + ":", border=4).\
                grid(row=row, column=0, sticky='w')
            row += 1
            if values:
                for v in sorted(values):
                    ttk.Label(self.scrollable_frame1, text=v).\
                        grid(row=row, column=1, sticky='w')
                    remove_btn = tk.Button(self.scrollable_frame1,
                                           text='X', bg='red')
                    remove_btn['command'] = lambda attr=attr, val=v: self.remove_attr(
                        attr, val)
                    remove_btn.grid(row=row, column=0, sticky='e', padx=5)
                    row += 1

    def ask_dir(self):
        initial_dir = app_config.ROOT_PATH if self.path == '' else self.path
        path = filedialog.askdirectory(initialdir=initial_dir)
        if path:
            if not path_is_parent(app_config.ROOT_PATH, path):
                msgbox.showerror(
                    'ERROR', f'"Folder must be inside root directory: {app_config.ROOT_PATH}')
                return
            self.path = path
            self.rel_path = os.path.relpath(self.path, app_config.ROOT_PATH)
            rewrite_tf(self.path_txt, self.rel_path)
            self.btn_folder.configure(text=shorten_path(self.path))
            rewrite_tf(self.fp_txt, self.path)
            self.parent_attrs = get_attributes_only(self.rel_path, {})
            self.config = parse_config(self.rel_path)
            print(self.config)
            self.entry_name.delete(0, 'end')
            if self.config.ver:
                self.entry_name.insert('end', self.config.name)
            else:
                self.entry_name.insert(
                    'end', os.path.basename(os.path.normpath(path)))
            self.entry_ver.delete(0, 'end')
            if self.config.ver:
                self.entry_ver.insert('end', self.config.ver)
            else:
                self.entry_ver.insert('end', '0')
            self.entry_date.set_date(self.config.date)
            comment = self.config.special.get('comment', '')
            rewrite_tf(self.comment_text, comment, False)
            self.folder_attrs = self.config.attributes
            self.draw_folder_attrs()
            self.draw_parent_attrs()

    def parent_attribute_checked(self, chk, attr, val):
        if chk.get() == 1:
            if attr not in self.folder_attrs:
                self.folder_attrs[attr] = set()
            self.folder_attrs[attr].add(val)
        else:
            self.folder_attrs[attr].discard(val)
            if len(self.folder_attrs[attr]) == 0:
                self.folder_attrs.pop(attr)
        self.draw_folder_attrs()

    def add_attr(self):
        if self.config == None or self.folder_attrs == None:
            return
        attr = self.choose_cat.get()
        val = self.choose_value.get().strip()
        if val == '':
            return
        if attr not in self.folder_attrs:
            self.folder_attrs[attr] = set()
        self.folder_attrs[attr].add(val)
        if (attr, val) in self.parent_chkbtn_vars:
            self.parent_chkbtn_vars[(attr, val)].set(1)
        self.draw_folder_attrs()

    def remove_attr(self, attr, val):
        if (attr, val) in self.parent_chkbtn_vars:
            self.parent_chkbtn_vars[(attr, val)].set(0)
        self.folder_attrs[attr].discard(val)
        if len(self.folder_attrs[attr]) == 0:
            self.folder_attrs.pop(attr)
        self.draw_folder_attrs()

    def save_config(self):
        if self.config == None:
            msgbox.showerror(
                'ERROR', 'Choose folder first.')
            return
        self.update_config()
        if self.config.name == '' or self.config.ver == '' or self.config.path == '':
            msgbox.showerror(
                'ERROR', 'Fill in all fields first.')
            return
        if self.config.id == None:
            self.config.id = write_new_config(self.config)
        else:
            update_config(self.config)

    def update_config(self):
        self.config.name = self.entry_name.get().strip()
        self.config.date = self.entry_date.get_date()
        self.config.ver = self.entry_ver.get().strip()
        self.config.path = self.rel_path
        self.config.attributes = self.folder_attrs
        self.config.special = {
            'comment': self.comment_text.get('1.0', 'end-1c')}


class SearchFrame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master.geometry('800x700')
        self.master.resizable(False, False)
        self.master.title('Search')
        self.set_variables()
        self.create_widgets()

    def set_variables(self):
        # initialize variables
        self.config = None
        self.search_attrs = {}
        self.folder_attrs = {}
        self.attr_vals = attribute_values_list()
        self.attr_names = sorted(self.attr_vals.keys())
        self.searched_folders = search_cfgs()

    def create_widgets(self):
        # configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=70)
        self.grid_rowconfigure(1, weight=30)

        # CREATE FOLDER INFO CONTAINER
        self.info_ct = tk.LabelFrame(self, text='Folder Information:')
        self.info_ct.grid_columnconfigure(0, weight=0)
        self.info_ct.grid_columnconfigure(1, weight=100)
        self.info_ct.grid_rowconfigure(6, weight=100)
        self.info_ct.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        # create labels
        tk.Label(self.info_ct, text='Name:').\
            grid(row=0, column=0, padx=5, pady=5, sticky='w')
        tk.Label(self.info_ct, text='Path:').\
            grid(row=1, column=0, padx=5, pady=5, sticky='w')
        tk.Label(self.info_ct, text='Date:').\
            grid(row=2, column=0, padx=5, pady=5, sticky='w')
        tk.Label(self.info_ct, text='Version:').\
            grid(row=3, column=0, padx=5, pady=5, sticky='w')
        tk.Label(self.info_ct, text='Comment:').\
            grid(row=4, column=0, padx=5, pady=5, sticky='w')
        tk.Label(self.info_ct, text='Attributes:').\
            grid(row=5, column=0, padx=5, pady=5, sticky='w')
        self.lbl_name = ttk.Label(self.info_ct, text='---')
        self.lbl_name.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.path_txt = tk.Text(self.info_ct, height=2, state='disabled')
        self.path_txt.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.lbl_date = ttk.Label(self.info_ct, text='---')
        self.lbl_date.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.lbl_ver = ttk.Label(self.info_ct, text='---')
        self.lbl_ver.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        self.comment_text = tk.Text(self.info_ct, height=4, state='disabled')
        self.comment_text.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        # create a scrollable frame for attributes
        self.canvas1 = tk.Canvas(self.info_ct)
        self.scrollable_frame1 = tk.Frame(self.canvas1)
        self.vsb1 = tk.Scrollbar(self.info_ct,
                                 orient='vertical', command=self.canvas1.yview)
        self.canvas1.configure(yscrollcommand=self.vsb1.set)

        self.canvas1.grid(row=6, column=0, columnspan=2, sticky='nswe')
        self.vsb1.grid(row=6, column=3, sticky='ns')
        self.canvas1.create_window((0, 0),
                                   window=self.scrollable_frame1, anchor='nw')
        self.scrollable_frame1.bind('<Configure>', self.on_frame_configure1)
        self.btn_open = ttk.Button(
            self.info_ct, text='Open', command=self.open_folder)
        self.btn_open.grid(row=7, column=0, padx=5, pady=5,)

        # CREATE ATTRIBUTE CHOOSE CONTAINER
        self.attr_ct = tk.LabelFrame(self, text='Search By Attributes:')
        self.attr_ct.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.attr_ct.columnconfigure(0, weight=40)
        self.attr_ct.columnconfigure(1, weight=40)
        self.attr_ct.columnconfigure(2, weight=20)
        self.attr_ct.rowconfigure(1, weight=100)
        self.canvas2 = tk.Canvas(self.attr_ct)
        self.scrollable_frame2 = tk.Frame(self.canvas2)
        self.vsb2 = tk.Scrollbar(self.attr_ct,
                                 orient='vertical', command=self.canvas2.yview)
        self.canvas2.configure(yscrollcommand=self.vsb2.set)

        self.canvas2.grid(row=1, column=0, columnspan=3, sticky='nswe')
        self.vsb2.grid(row=1, column=3, sticky='ns')
        self.canvas2.create_window((0, 0),
                                   window=self.scrollable_frame2, anchor='nw')
        self.scrollable_frame2.bind('<Configure>', self.on_frame_configure2)
        self.choose_cat = ttk.Combobox(
            self.attr_ct, values=self.attr_names, state='readonly')
        if len(self.attr_names) > 0:
            self.choose_cat.current(0)
        self.choose_cat.grid(row=0, column=0, pady=5, sticky='ew')
        self.choose_cat.bind('<<ComboboxSelected>>', self.clear_value)
        self.choose_value = ttk.Combobox(self.attr_ct, postcommand=self.change_values_list,
                                         state='readonly')
        self.choose_value.grid(row=0, column=1, pady=5, sticky='ew')
        self.btn_add = ttk.Button(self.attr_ct, text='Add',
                                  command=self.add_attr)
        self.btn_add.grid(row=0, column=2, pady=5, sticky='ew')

        # CREATE LIST OF SEARCH RESULTS
        self.list_ct = tk.LabelFrame(self, text='Folders:')
        self.list_ct.grid(row=1, column=0, columnspan=2,
                          padx=5, pady=5, sticky='nsew')
        self.list_ct.columnconfigure(0, weight=100)
        self.list_ct.rowconfigure(0, weight=100)
        self.columns = ('#1', '#2', '#3', '#4', '#5')
        self.table = ttk.Treeview(self.list_ct, show='headings',
                                  columns=self.columns, selectmode='browse')
        self.table.column('#1', width=10)
        self.table.column('#2', width=150)
        self.table.column('#3', width=350)
        self.table.column('#4', width=20)
        self.table.column('#5', width=60)
        self.table.heading('#1', text='ID')
        self.table.heading('#2', text='Name')
        self.table.heading('#3', text='Path')
        self.table.heading('#4', text='Ver')
        self.table.heading('#5', text='Date')
        vsb3 = ttk.Scrollbar(self.list_ct, orient='vertical',
                             command=self.table.yview)
        self.table.configure(yscrollcommand=vsb3.set)
        self.table.bind('<<TreeviewSelect>>', self.select_folder)
        self.table.grid(row=0, column=0, sticky='nswe')
        vsb3.grid(row=0, column=1, sticky='ns')
        self.fill_table()

        # CREATE CONTROL BUTTONS CONTAINER
        self.buttons_ct = tk.Frame(self)
        self.buttons_ct.grid_configure(row=2, column=0, columnspan=2,
                                       padx=5, pady=5, sticky='nsew')
        self.btn_back = ttk.Button(self.buttons_ct, text='Back',
                                   command=lambda: self.master.switch_frame(MainFrame))
        self.btn_back.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.btn_search = ttk.Button(self.buttons_ct, text='Search',
                                     command=self.search_folders)
        self.btn_search.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

    def on_frame_configure1(self, e):
        self.canvas1.configure(scrollregion=self.canvas1.bbox('all'))

    def on_frame_configure2(self, e):
        self.canvas2.configure(scrollregion=self.canvas2.bbox('all'))

    def select_folder(self, event):
        ri = self.table.selection()[0]
        item = self.table.item(ri)
        path = item['values'][2]
        self.load_folder_info(path)

    def load_folder_info(self, rel_path):
        self.config = parse_config(rel_path)
        rewrite_tf(self.path_txt, self.config.path)
        self.lbl_name.configure(text=self.config.name)
        self.lbl_ver.configure(text=self.config.ver)
        self.lbl_date.configure(text=self.config.date)
        comment = self.config.special.get('comment', '')
        rewrite_tf(self.comment_text, comment)
        print(self.config)
        self.folder_attrs = self.config.attributes
        self.draw_folder_attrs()

    def clear_value(self, event):
        self.choose_value.set('')

    def change_values_list(self):
        values = list(sorted(self.attr_vals.get(self.choose_cat.get())))
        self.choose_value.configure(values=values)

    def fill_table(self):
        self.table.delete(*self.table.get_children())
        for f in self.searched_folders:
            row = (f.id, f.name, f.path, f.ver, f.date)
            self.table.insert("", 'end', values=row)

    def draw_search_attrs(self):
        for child in self.scrollable_frame2.winfo_children():
            child.destroy()
        row = 0
        for attr, values in self.search_attrs.items():
            ttk.Label(self.scrollable_frame2, text=attr + ":").\
                grid(row=row, column=0, sticky='w')
            row += 1
            if values:
                for v in sorted(values):
                    ttk.Label(self.scrollable_frame2, text=v).\
                        grid(row=row, column=1, sticky='w')
                    remove_btn = tk.Button(self.scrollable_frame2,
                                           text='X', bg='red')
                    remove_btn['command'] = lambda attr=attr, val=v: self.remove_attr(
                        attr, val)
                    remove_btn.grid(row=row, column=0, sticky='e', padx=5)
                    row += 1

    def draw_folder_attrs(self):
        for child in self.scrollable_frame1.winfo_children():
            child.destroy()
        row = 0
        for attr, values in self.folder_attrs.items():
            ttk.Label(self.scrollable_frame1, text=attr + ":", border=4).\
                grid(row=row, column=0, sticky='w')
            row += 1
            if values:
                for v in sorted(values):
                    ttk.Label(self.scrollable_frame1, text=v).\
                        grid(row=row, column=1, sticky='w')
                    row += 1

    def add_attr(self):
        attr = self.choose_cat.get()
        val = self.choose_value.get()
        if val == '':
            return
        if attr not in self.search_attrs:
            self.search_attrs[attr] = set()
        self.search_attrs[attr].add(val)
        self.draw_search_attrs()

    def remove_attr(self, attr, val):
        self.search_attrs[attr].discard(val)
        if len(self.search_attrs[attr]) == 0:
            self.search_attrs.pop(attr)
        self.draw_search_attrs()

    def open_folder(self):
        if self.config:
            path = os.path.join(app_config.ROOT_PATH, self.config.path)
            try:
                os.startfile(path)
            except FileNotFoundError:
                msgbox.showerror(
                    'ERROR', "Folder doesn't exist. Try remaking the database.")
                return
            except Exception as err:
                msgbox.showerror('ERROR', err)

    def search_folders(self):
        print(self.search_attrs)
        self.searched_folders = search_cfgs(self.search_attrs)
        self.fill_table()


def run_app():
    root = tk.Tk()
    app = MainFrame(root)
    root.mainloop()
