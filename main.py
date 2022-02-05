"""
BrOrg
=====

Organize your life in Markdown Files

"""
__version__ = "0.3.0"

from functools import partial
from os.path import join, exists, dirname, basename, relpath, splitext
from os import walk, stat
import time
from threading import Thread
from stat import ST_MTIME
import json
import os
import re
import humanize
import datetime
import themes
import weakref

from kivy.app import App
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.properties import (
    ListProperty,
    StringProperty,
    NumericProperty,
    BooleanProperty,
    DictProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.widget import Widget
from kivy.vector import Vector
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput  # noqa
from kivy.uix.codeinput import CodeInput  # noqa
from kivy.uix.image import Image
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from plyer.utils import platform
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase

from pygments.lexers.markup import MarkdownLexer
from dateutil.parser import parse

from sync import WebDavSync

# import toast

Window.softinput_mode = ""

non_file_safe = [
    '"',
    "#",
    "$",
    "%",
    "&",
    "+",
    ",",
    "/",
    ":",
    ";",
    "=",
    "?",
    "@",
    "[",
    "\\",
    "]",
    "^",
    "`",
    "{",
    "|",
    "}",
    "~",
    "'",
]


def get_android_vkeyboard_height():
    if platform == "android":
        from jnius import autoclass

        Activity = autoclass("org.kivy.android.PythonActivity")
        Rect = autoclass("android.graphics.Rect")
        root_window = Activity.getWindow()
        view = root_window.getDecorView()
        r = Rect()
        view.getWindowVisibleDisplayFrame(r)

        return Window.height - (r.bottom - r.top)


class MyTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.trigger_keyboard_height = Clock.create_trigger(
            self.update_keyboard_height, 0.1, interval=True
        )
        self.trigger_cancel_keyboard_height = Clock.create_trigger(
            lambda dt: self.trigger_keyboard_height.cancel(), 1.0, interval=False
        )

    def update_keyboard_height(self, dt):
        if platform == "android":
            App.get_running_app().keyboard_height = get_android_vkeyboard_height()

    def _bind_keyboard(self):
        super()._bind_keyboard()
        if platform == "android":
            self.trigger_cancel_keyboard_height.cancel()
            self.trigger_keyboard_height()

    def _unbind_keyboard(self):
        super()._unbind_keyboard()
        if platform == "android":
            self.trigger_cancel_keyboard_height()

    def on_touch_down(self, touch):
        self.focus = True
        FocusBehavior.ignored_touch.append(touch)


class CircularButton(
    ButtonBehavior,
    Widget,
):
    def collide_point(self, x, y):
        return Vector(x, y).distance(self.center) <= self.width / 2


class SelectableButton(ButtonBehavior, Label):
    selected = BooleanProperty(False)
    default = BooleanProperty(True)

    def on_release(self, *kwargs):
        if self.default:
            selected = self.selected
            for c in self.parent.children:
                if hasattr(c, "selected"):
                    c.selected = False
            self.selected = not selected


class IconButton(
    ButtonBehavior,
    Image,
):
    pass


class NotesRecycleView(RecycleView):
    def __init__(self, **kwargs):
        super(NotesRecycleView, self).__init__(**kwargs)


class TodayRecycleView(RecycleView):
    def __init__(self, **kwargs):
        super(TodayRecycleView, self).__init__(**kwargs)


class TextRecycleView(RecycleView):
    def __init__(self, **kwargs):
        super(TextRecycleView, self).__init__(**kwargs)


class SelectableRecycleBoxLayout(
    FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout
):
    """Adds selection and focus behaviour to the view."""


class MDInput(CodeInput):

    re_indent_todo = re.compile(r"^\s*(-\s\[\s\]\s)")
    re_indent_done = re.compile(r"^\s*(-\s\[x\]\s)")
    re_indent_list = re.compile(r"^\s*(-\s)")

    def __init__(self, **kwarg):
        CodeInput.__init__(self, lexer=MarkdownLexer(), style_name="default")
        # User can change keyboard size during input, so we should regularly update the keyboard height
        self.trigger_keyboard_height = Clock.create_trigger(
            self.update_keyboard_height, 1, interval=True
        )
        self.trigger_cancel_keyboard_height = Clock.create_trigger(
            lambda dt: self.trigger_keyboard_height.cancel(), 1.0, interval=False
        )

    def update_keyboard_height(self, dt):
        if platform == "android":
            App.get_running_app().keyboard_height = get_android_vkeyboard_height()

    def _bind_keyboard(self):
        super()._bind_keyboard()
        if platform == "android":
            self.trigger_cancel_keyboard_height.cancel()
            self.trigger_keyboard_height()

    def _unbind_keyboard(self):
        super()._unbind_keyboard()
        if platform == "android":
            self.trigger_cancel_keyboard_height()

    def insert_text(self, substring, from_undo=False):
        if not from_undo and self.multiline and self.auto_indent and substring == u"\n":
            substring = self._auto_indent(substring)
        CodeInput.insert_text(self, substring, from_undo)

    def _auto_indent(self, substring):
        index = self.cursor_index()

        if index > 0:
            _text = self.text
            line_start = _text.rfind("\n", 0, index)
            if line_start > -1:
                line = _text[line_start + 1 : index]
                indent = self.re_indent_todo.match(line)

                if indent is None:
                    indent = self.re_indent_done.match(line)
                if indent is None:
                    indent = self.re_indent_list.match(line)
                if indent is not None:
                    substring += indent.group().replace("x", " ")
        return substring


class NoteView(Screen):

    title = StringProperty()
    content = StringProperty()
    last_modification = StringProperty()
    natural_last_modification = StringProperty()
    mtime = NumericProperty()
    filepath = StringProperty()


class TodoView(Screen):
    pass


class TextListItem(RecycleDataViewBehavior, BoxLayout):

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    text = StringProperty()

    def __init__(self, **kwargs):
        super(TextListItem, self).__init__(**kwargs)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        self.index = index
        return super(TextListItem, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super(TextListItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected

        if is_selected:
            rv.text = rv.data[self.index].get("text", "")


class NoteListItem(RecycleDataViewBehavior, BoxLayout):

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    title = StringProperty()
    content = StringProperty()
    last_modification = StringProperty()
    natural_last_modification = StringProperty()
    mtime = NumericProperty()
    filepath = StringProperty()

    def __init__(self, **kwargs):
        print(kwargs)
        super(NoteListItem, self).__init__(**kwargs)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        self.index = index
        return super(NoteListItem, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super(NoteListItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            self.parent.clear_selection()


class TodayListItem(RecycleDataViewBehavior, BoxLayout):

    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    line = StringProperty()
    text = StringProperty()
    due = StringProperty()
    datetime = None
    sortkey = None
    itemtype = NumericProperty(0)  # 0 header, 1 todo, 2 schedule, 3 note
    filename = StringProperty()

    def __init__(self, **kwargs):
        super(TodayListItem, self).__init__(**kwargs)

    def refresh_view_attrs(self, rv, index, data):
        """Catch and handle the view changes"""
        self.index = index
        return super(TodayListItem, self).refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Add selection on touch down"""
        if super(TodayListItem, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        """Respond to the selection of items in the view."""
        self.selected = is_selected
        if is_selected:
            self.parent.clear_selection()


class TodayScreen(Screen):
    """Main Screen listing todos and notes"""


class NotesScreen(Screen):
    """Main Screen listing todos and notes"""


class SettingsScreen(Screen):
    pass


class DatetimePickerScreen(Screen):
    """Datetime picker screen"""

    def dismiss(self, **kwargs):
        print("dismiss")
        self.parent.transition.direction = "right"
        self.parent.current = self.parent.previous


class BrOrg(App):

    notes = ListProperty()
    today = ListProperty()
    syncing = BooleanProperty(False)
    keyboard_height = NumericProperty(0)
    stop_events = False
    auto_sync = None

    webdav_host = StringProperty()
    webdav_login = StringProperty()
    webdav_passwd = StringProperty()
    webdav_path = StringProperty()

    quick_todo_file = StringProperty()
    quick_todo_header = StringProperty()
    quick_note_file = StringProperty()
    quick_note_header = StringProperty()
    quick_event_file = StringProperty()
    quick_event_header = StringProperty()
    quick_journal_file = StringProperty()
    quick_journal_header = StringProperty()
    quick_journal_item = StringProperty()

    theme = DictProperty(themes.get_dark_theme())

    def set_theme(self, thme):
        if thme == "gruvbox":
            self.theme = themes.get_gruvbox_theme()
        elif thme == "dark":
            self.theme = themes.get_dark_theme()
        else:
            self.theme = themes.get_light_theme()
        self.set_pref("theme", self.theme["name"])

    def create_default_prefs(self):
        settings = {
            "webdav_host": "",
            "webdav_login": "",
            "webdav_passwd": "",
            "webdav_path": "",
            "quick_todo_file": "Org.md",
            "quick_todo_header": "## Todos",
            "quick_note_file": "Org.md",
            "quick_note_header": "## Quicknotes",
            "quick_event_file": "Org.md",
            "quick_event_header": "## Events",
            "quick_journal_file": "Journal.md",
            "quick_journal_header": "## {:%Y-%m-%d %a}",
            "quick_journal_item": "- {:%Y-%m-%d %a} : {}",
            "theme": "dark",
        }
        with open(self.settings_fn, "w") as fh:
            json.dump(settings, fh)

    def get_pref(self, key, default=None):
        ans = default
        try:
            with open(self.settings_fn, "rb") as fh:
                ans = json.load(fh).get(key)
            if (ans is None) and (default is not None):
                ans = default
        except (IOError, ValueError) as err:
            print(err)
            self.create_default_prefs()
            return self.get_pref(key, default)
        return ans

    def set_pref(self, key, value):
        try:
            with open(self.settings_fn, "r") as fh:
                settings = json.load(fh)
        except IOError as err:
            print(err)
            self.create_default_prefs()
            with open(self.settings_fn, "r") as fh:
                settings = json.load(fh)

        settings[key] = value
        with open(self.settings_fn, "w") as fh:
            json.dump(settings, fh)

    def key_input(self, window, key, scancode, codepoint, modifier):
        # key == 27 means it is waiting for
        # back button tobe pressed
        if key == 27:

            # checking if we are at mainscreen or not
            if self.root.ids.sm.current == "today":
                # return True means do nothing
                return False
            else:
                self.go_today()
                return True
        return False

    def on_start(self):
        if platform == "android":
            from android import activity
            from jnius import autoclass

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            mactivity = PythonActivity.mActivity
            try:
                self.on_new_intent(mactivity.getIntent())
                print("DEBUG: %s" % PythonActivity.getIntent())
                self.on_new_intent(PythonActivity.getIntent())
                activity.bind(on_new_intent=self.on_new_intent)
            except Exception as err:
                print("DEBUG 3: %s" % err)

    def build(self):
        Window.bind(on_keyboard=self.key_input)
        # load sync settings
        self.webdav_host = self.get_pref("webdav_host")
        self.webdav_login = self.get_pref("webdav_login")
        self.webdav_passwd = self.get_pref("webdav_passwd")
        self.webdav_path = self.get_pref("webdav_path")

        self.quick_todo_file = self.get_pref("quick_todo_file", "Org.md")
        self.quick_todo_header = self.get_pref("quick_todo_header", "## Todos")
        self.quick_note_file = self.get_pref("quick_note_file", "Org.md")
        self.quick_note_header = self.get_pref("quick_note_header", "## Quicknotes")
        self.quick_event_file = self.get_pref("quick_event_file", "Org.md")
        self.quick_event_header = self.get_pref("quick_event_header", "## Events")
        self.quick_journal_file = self.get_pref("quick_journal_file", "Journal.md")
        self.quick_journal_header = self.get_pref(
            "quick_journal_header", "## {%Y-%m-%d %a}"
        )
        self.quick_journal_item = self.get_pref(
            "quick_journal_item", "- {%Y-%m-%d %a} : {}"
        )
        self.set_theme(self.get_pref("theme"))
        self.sync_th = None

        self.noteView = None
        self.transition = SlideTransition(duration=0.05)
        self.mainWidget = Builder.load_file("main.kv")

        Clock.schedule_once(self.__init__later__, 0)
        return self.mainWidget

    def insertSection(self, date):
        if date not in self._sections:
            self._schedule.append(
                {
                    "text": humanize.naturalday(date).title(),
                    "datetime": date,
                    "itemtype": 0,
                    "sortkey": datetime.datetime.combine(
                        date, datetime.datetime.min.time()
                    ),
                }
            )
            self._sections.append(date)

    def load_today(self):
        self._schedule = []
        self._next = []
        self._sections = []
        self.previous_date = None
        try:
            for path in os.listdir(self.notes_fn):
                if not os.path.isfile(os.path.join(self.notes_fn, path)):
                    continue
                with open(os.path.join(self.notes_fn, path), "r") as fh:
                    try:
                        content = fh.read()
                    except UnicodeDecodeError:
                        print("Not a text file {}".format(path))
                        continue
                    idx = 0
                    for line in content.split("\n"):
                        idx += len(line) + 1
                        if "- [x]" in line:
                            continue
                        # Check Now
                        isNow = re.match(r".*- \[ \].*\s#Now", line)
                        if isNow:
                            due = datetime.datetime.now()
                            self.insertSection(due.date())
                            self._schedule.append(
                                {
                                    "line": line[5:].strip(),
                                    "text": re.sub(
                                        r"\s\#Now", "", line.replace("- [ ]", "")
                                    ).strip(),
                                    "due": humanize.naturalday(due),
                                    "datetime": due,
                                    "sortkey": datetime.datetime.combine(
                                        due, datetime.datetime.max.time()
                                    ),
                                    "filename": path,
                                    "filepath": os.path.join(self.notes_fn, path),
                                    "lineno": idx - 1,
                                    "itemtype": 1,
                                }
                            )
                            continue
                        # Check Next
                        isNext = re.match(r".*- \[ \].*\s\#Next", line)
                        if isNext:
                            due = datetime.datetime.now() + datetime.timedelta(days=1)
                            self._next.append(
                                {
                                    "line": line[6:].strip(),
                                    "text": re.sub(
                                        r"\s\{Next\}", "", line.replace("- [ ]", "")
                                    ).strip(),
                                    "due": humanize.naturalday(due),
                                    "datetime": due,
                                    "sortkey": datetime.datetime.combine(
                                        due, datetime.datetime.max.time()
                                    ),
                                    "filename": path,
                                    "filepath": os.path.join(self.notes_fn, path),
                                    "lineno": idx - 1,
                                    "itemtype": 1,
                                }
                            )
                            continue

                        # Check @scheduled
                        due = re.search(r"\<(.*?)\>", line)
                        if due is not None:
                            try:
                                due = parse(due.group(1))
                                if due is not None:
                                    if (
                                        datetime.datetime.now().date() <= due.date()
                                    ) and (
                                        (
                                            datetime.datetime.now().date()
                                            + datetime.timedelta(days=5)
                                        )
                                        >= due.date()
                                    ):
                                        self.insertSection(due.date())
                                        self._schedule.append(
                                            {
                                                "line": line[5:].strip(),
                                                "text": re.sub(
                                                    "<.*>",
                                                    "",
                                                    line.replace("- ", "").replace(
                                                        "[ ]", ""
                                                    ),
                                                ).strip(),
                                                "due": "{} {}".format(
                                                    humanize.naturalday(due),
                                                    due.strftime("%H:%M"),
                                                ),
                                                "datetime": due,
                                                "sortkey": due,
                                                "filename": path,
                                                "filepath": os.path.join(
                                                    self.notes_fn, path
                                                ),
                                                "lineno": idx - 1,
                                                "itemtype": 1 if "- [ ]" in line else 2,
                                            }
                                        )
                            except Exception as err:
                                print("L653", err, line, path)

        except OSError as err:
            print("L656", err)

        self._schedule = sorted(
            self._schedule, key=lambda k: k["sortkey"], reverse=False
        )

        # Now notes list
        self._heads = [
            {
                "text": "Now",
                "itemtype": 0,
                "sortkey": None,
            },
            {
                "text": "Next",
                "itemtype": 0,
                "sortkey": None,
            },
            {
                "text": "Notes",
                "itemtype": 0,
                "sortkey": None,
            },
        ]

        self._notes = []
        for path, folders, files in walk(self.notes_fn):
            if os.path.relpath(path, self.notes_fn) != ".":
                continue
            for afile in files:
                if (splitext(basename(afile))[1] in (".md", ".md")) and (
                    afile[0] != "."
                ):
                    mtime = stat(join(path, afile))[ST_MTIME]
                    self._notes.append(
                        {
                            "text": splitext(basename(afile))[0],
                            "category": dirname(
                                relpath(join(afile, path), self.notes_fn)
                            ),
                            "last_modification": time.asctime(time.localtime(mtime)),
                            "due": humanize.naturalday(
                                datetime.datetime.fromtimestamp(mtime)
                            ),
                            "natural_last_modification": humanize.naturalday(
                                datetime.datetime.fromtimestamp(mtime)
                            ),
                            "mtime": mtime,
                            "content": "",
                            "itemtype": 3,
                            "filepath": join(path, afile),
                            "lineno": 0,
                        }
                    )
        self.sort_notes()

        self.today = self._schedule
        if len(self._next) > 0:
            self.today = self.today + [self._heads[1]] + self._next
        if len(self._notes) > 0:
            self.today = self.today + [self._heads[2]] + self._notes

    def __init__later__(self, dt):
        self.load_today()
        self.sync()
        self.load_today()
        Clock.schedule_once(self.__init__lazy__, 0)

    def __init__lazy__(self, dt):
        Builder.load_file("lazy.kv")
        tV = TodoView(name="todoView")
        sS = SettingsScreen(name="settings")
        dPS = DatetimePickerScreen(name="datetimepicker")
        self.mainWidget.ids.sm.add_widget(tV)
        self.mainWidget.ids.sm.add_widget(sS)
        self.mainWidget.ids.sm.add_widget(dPS)
        self.mainWidget.ids["todoView"] = weakref.ref(tV)
        self.mainWidget.ids["settingsView"] = weakref.ref(sS)
        self.mainWidget.ids["datetimePickerView"] = weakref.ref(dPS)

    def sort_notes(
        self,
    ):
        self._notes = sorted(self._notes, key=lambda k: k["mtime"], reverse=True)

    def slugify(self, text):
        """
        Turn the text content of a header into a slug for use in an ID
        """
        non_safe = [c for c in text if c in non_file_safe]
        if non_safe:
            for c in non_safe:
                text = text.replace(c, "")
        # Strip leading, trailing and multiple whitespace,
        # convert remaining whitespace to _
        text = u"_".join(text.split())
        return text

    def unslugify(self, text):
        """
        Turn the text content of a header into a slug for use in an ID
        """
        return text.replace("_", " ")

    def save_note(self, filepath, content):
        # TODO : Categories in folder
        if self.stop_events:
            return
        new_path = None
        title = self.slugify(content.partition("\n")[0])
        if title != self.noteView.title:
            new_path = self.set_note_title(filepath, title)

        if new_path:
            self.noteView.filepath = new_path
            self.noteView.title = title
            print("Saving %s" % new_path)
            # self.notes[index]["content"] = content

        with open(self.noteView.filepath, "wb") as fh:
            fh.write(content.encode("utf-8"))
            if self.auto_sync:
                self.auto_sync.cancel()
            self.auto_sync = Clock.schedule_once(self.sync, 5)

    def del_note(self, note_index):
        path = join(self.notes_fn, self.notes[note_index]["title"] + ".md")
        print("Deleting path ", path)
        del self.notes[note_index]
        self.sync()
        self.go_notes()

    def edit_today(self, index, is_selected):
        if self.today[index]["itemtype"] == 0:
            return
        pth = self.today[index]["filepath"]
        try:
            mtime = stat(pth)[ST_MTIME]
        except FileNotFoundError:
            mtime = 0

        print("Edit Today %s" % self.today[index]["filepath"])
        note = {
            "title": splitext(basename(pth))[0],
            "category": dirname(relpath(pth, self.notes_fn)),
            "last_modification": time.asctime(time.localtime(mtime)),
            "natural_last_modification": humanize.naturalday(
                datetime.datetime.fromtimestamp(mtime)
            ),
            "mtime": mtime,
            "content": "",
            "filepath": pth,
        }
        try:
            with open(note["filepath"], "r") as fh:
                note["content"] = fh.read()
        except Exception as err:
            print(err)

        # Check title==filename
        title = self.slugify(note["content"].partition("\n")[0])
        if "{}.md".format(title) != os.path.basename(note["filepath"]):
            print(
                "title differ replace it {}<>{}".format(
                    "{}.md".format(title), os.path.basename(note["filepath"])
                )
            )
            note["content"] = (
                "# "
                + self.unslugify(
                    os.path.splitext(os.path.basename(note["filepath"]))[0]
                )
                + "\n".join(note["content"].partition("\n")[1:])
            )

        if self.noteView is None:
            self.noteView = NoteView(
                name="noteView",
                title=note.get("title"),
                content=note.get("content"),
                last_modification=note.get("last_modification"),
                filepath=note.get("filepath"),
            )
            self.root.ids.sm.add_widget(self.noteView)
        else:
            self.stop_events = True
            self.noteView.title = note.get("title")
            self.noteView.last_modification = note.get("last_modification")
            self.noteView.filepath = note.get("filepath")
            self.noteView.content = note.get("content")
            self.stop_events = False

        self.root.ids.sm.transition.direction = "left"
        self.root.ids.sm.current = "noteView"
        self.display_toolbar = True
        self.display_add = False
        Clock.schedule_once(
            partial(self.__go_to_line__, self.today[index]["lineno"]), 0
        )

    def __go_to_line__(self, idx, dts=None):
        col, row = self.noteView.ids.w_textinput.get_cursor_from_index(idx)
        self.noteView.ids.w_textinput.focus = True
        self.noteView.ids.w_textinput.cursor = (col, row)

    def add(self):
        if self.root.ids.sm.current == "notes":
            self.add_note()
        elif self.root.ids.sm.current == "today":
            self.add_todo()
        elif self.root.ids.sm.current == "todoView":
            self.add_item()

    def insert_org(self, filepath, head, t):
        try:
            with open(os.path.join(self.notes_fn, filepath), "r") as rfh:
                c = rfh.read()
        except FileNotFoundError:
            c = ""

        i = c.find(head)
        if i < 0:
            c = "\n".join((c.strip("\n"), "\n" + head, t))
        else:
            c = "\n".join(
                (c[: i + len(head)].strip("\n"), t, c[i + len(head) :].strip("\n"))
            )

        with open(os.path.join(self.notes_fn, filepath), "w") as wfh:
            wfh.write(c)

    def add_item(self):
        if self.root.ids.todoView.ids.w_todo.selected is True:
            c = "- [ ] {}".format(self.root.ids.todoView.ids.w_text.text)
            if self.root.ids.todoView.ids.w_priority_now.selected:
                c = "{} #Now".format(c)
            elif self.root.ids.todoView.ids.w_priority_next.selected:
                c = "{} #Next".format(
                    c,
                )
            if self.root.ids.todoView.ids.w_time.selected is True:
                c = "{} <{}>".format(c, self.root.ids.todoView.ids.w_time.text)
            self.insert_org(self.quick_todo_file, self.quick_todo_header, c)
        elif self.root.ids.todoView.ids.w_event.selected is True:
            c = "- {}".format(self.root.ids.todoView.ids.w_text.text)
            if self.root.ids.todoView.ids.w_time.selected is True:
                c = "{} <{}>".format(c, self.root.ids.todoView.ids.w_time.text)
            self.insert_org(self.quick_event_file, self.quick_event_header, c)
        elif self.root.ids.todoView.ids.w_journal.selected is True:
            c = self.quick_journal_item.format(
                datetime.datetime.now(),
                self.root.ids.todoView.ids.w_text.text,
            )
            self.insert_org(
                self.quick_journal_file,
                self.quick_journal_header.format(datetime.datetime.now()),
                c,
            )
        else:
            self.insert_org(
                self.quick_note_file,
                self.quick_note_header,
                "{}".format(self.root.ids.todoView.ids.w_time.text),
            )
        self.root.ids.todoView.ids.w_text.text = ""
        self.root.ids.todoView.ids.w_text.focus = False
        self.go_today()

    def add_todo(self, *kwargs):
        print((self.root.ids))
        self.root.ids.sm.transition.direction = "left"
        self.root.ids.sm.current = "todoView"
        self.display_add = False
        self.display_toolbar = False
        self.root.ids.todoView.ids.w_text.focus = True

    def add_note(self):
        idx = 1
        if not os.path.exists(
            self.notes_fn,
        ):
            os.mkdir(self.notes_fn)

        while exists(join(self.notes_fn, "New_note_%s.md" % idx)) is True:
            idx += 1
        self.today.insert(
            len(self.today),
            {
                "title": "New_note_%s" % idx,
                "content": "# New note %s" % idx,
                "last_modification": "",
                "mtime": 0,
                "itemtype": 3,
                "lineno": len("New_note_%s" % idx) + 3,
                "filepath": join(self.notes_fn, "New note %s.md" % idx),
            },
        )
        note_index = len(self.today) - 1
        self.edit_today(note_index, True)

    def set_note_lastmodification(self, note_index):
        self.notes[note_index]["last_modification"] = time.time()

    def set_note_title(self, filepath, title):
        print("Renaming %s -> %s" % (filepath, join(self.notes_fn, "%s.md" % title)))

        if self.stop_events:
            print("self.stop_events")
            return

        new_path = join(self.notes_fn, "%s.md" % title)

        if filepath == "":
            return new_path

        try:
            i = 2
            while os.path.exists(new_path):
                new_path = join(self.notes_fn, "%s_2.md" % title)
                i += 1
            os.rename(filepath, new_path)
            return new_path
        except OSError:
            return None

    def insertDatetimeAdd(self, day, month, year, h, m, *kwargs):
        dt = datetime.datetime(year, month, day, h, m, 0)
        self.root.ids.todoView.ids.w_time.text = "{}".format(
            dt.strftime("%a %-d %b %Y %H:%M")
        )

    def insertDatetimeNoteView(self, day, month, year, h, m, *kwargs):
        index = self.noteView.ids.w_textinput.cursor_index()

        dt = datetime.datetime(year, month, day, h, m, 0)
        print("insertDatetimeNoteView index", index)
        if index > 0:
            _text = self.noteView.ids.w_textinput.text
            line_start = _text.rfind("\n", 0, index)
            line_end = _text.find("\n", index)

            due = re.search(r"\<(.*?)\>", _text[line_start:line_end])
            if due is not None:
                self.noteView.ids.w_textinput.text = "{}{}{}".format(
                    self.noteView.ids.w_textinput.text[:line_start],
                    self.noteView.ids.w_textinput.text[line_start:line_end].replace(
                        due.group(), "<{}>".format(dt.strftime("%a %-d %b %Y %H:%M"))
                    ),
                    self.noteView.ids.w_textinput.text[line_end:],
                )
                return

            self.noteView.ids.w_textinput.text = "{}{}{}".format(
                self.noteView.ids.w_textinput.text[:line_end].rstrip(),
                " <{}>".format(dt.strftime("%a %-d %b %Y %H:%M")),
                self.noteView.ids.w_textinput.text[line_end:],
            )
            line_end = _text.find("\n", index)
            # self.set_cursor(line_end)

    def sync(self, *kwargs):
        if self.sync_th:
            if self.sync_th.is_alive() is True:
                return
        self.sync_th = Thread(target=self._sync)
        self.sync_th.start()

    def _rotate_sync_button(self, dt=None):
        self.root.ids.todayScreen.ids.sync_progressbar.value = (
            self.root.ids.todayScreen.ids.sync_progressbar.value + 10
        ) % 100

    def validate_sync_settings(self, *kwargs):
        s = WebDavSync(
            host=self.webdav_host,
            login=self.webdav_login,
            passwd=self.webdav_passwd,
            root=self.webdav_path,
            local_path=self.notes_fn,
        )
        try:
            s._get_remote_etag("/")
            self.root.ids.settingsView.ids.sync_status.text = "OK"
        except Exception as err:
            self.root.ids.settingsView.ids.sync_status.text = str(err)
        self.root.ids.settingsView.ids.sync_test.selected = False

    def _sync(self):
        # self.syncing_inter = Clock.schedule_interval(self._rotate_sync_button, 0.1)
        s = WebDavSync(
            host=self.webdav_host,
            login=self.webdav_login,
            passwd=self.webdav_passwd,
            root=self.webdav_path,
            local_path=self.notes_fn,
        )
        self.syncing = True
        # toast.toast("syncing")
        try:
            s.sync()
        # self.syncing_inter.cancel()
        # self.root.ids.todayScreen.ids.settings_button.angle = 0
        finally:
            self.syncing = False
            if self.root.ids.sm.current == "today":
                self.load_today()

        # FIXME
        # - [ ] Reload list if current screen is list
        # - [ ] Warn user file changes and reload

        # checking if we are at mainscreen or not
        # if self.root.ids.sm.current == "today":
        #    print("File changed with sync")
        #    self.load_today()
        # elif self.root.ids.sm.current == "noteView":
        #    if self.noteView.filepath in downloadedFiles:
        #        toast("File changed with sync")
        #        try:
        #            with open(self.noteView.filepath, "r") as fh:
        #                self.noteView.content = fh.read()
        #        except Exception as err:
        #            print(err)

    def set_cursor(self, idx):
        self.noteView.ids.w_textinput.cursor = (
            self.noteView.ids.w_textinput.get_cursor_from_index(idx)
        )
        self.noteView.ids.w_textinput.focus = True

    def do_copy(self, *kwargs):
        pass

    def do_paste(self, *kwargs):
        pass

    def do_indent(self, *kwargs):
        index = self.noteView.ids.w_textinput.cursor_index()
        if index > 0:
            _text = self.noteView.ids.w_textinput.text
            line_start = _text.rfind("\n", 0, index)
            self.noteView.ids.w_textinput.text = (
                _text[: line_start + 1] + "  " + _text[line_start + 1 :]
            )
            if index > line_start:
                index += 2

        self.set_cursor(index)

    def do_unindent(self, *kwargs):
        index = self.noteView.ids.w_textinput.cursor_index()
        _text = self.noteView.ids.w_textinput.text
        line_start = _text.rfind("\n", 0, index)
        line_end = _text.find("\n", index)
        if line_end == -1:
            line_end = len(_text)
        if (_text[line_start + 1 : line_start + 3]) == "  ":
            self.noteView.ids.w_textinput.text = (
                _text[: line_start + 1] + _text[line_start + 3 :]
            )
            if index > line_start:
                index -= 2
        self.set_cursor(index)

    def do_togglepriority(self, *kwargs):
        index = self.noteView.ids.w_textinput.cursor_index()

        if index > 0:
            _text = self.noteView.ids.w_textinput.text
            previous_len = len(_text)
            line_start = _text.rfind("\n", 0, index)
            line_end = _text.find("\n", index)
            if line_end == -1:
                line_end = len(_text)
            idx = _text.find("#Now", line_start + 1, line_end)
            if idx >= 0:
                self.noteView.ids.w_textinput.text = "{}{}{}".format(
                    self.noteView.ids.w_textinput.text[:idx].rstrip(),
                    " #Next",
                    self.noteView.ids.w_textinput.text[idx + 4 :],
                )
            else:
                idx = _text.find("#Next", line_start + 1, line_end)
                if idx >= 0:
                    self.noteView.ids.w_textinput.text = "{}{}{}".format(
                        self.noteView.ids.w_textinput.text[:idx].rstrip(),
                        " ",
                        self.noteView.ids.w_textinput.text[idx + 5 :],
                    )
                else:
                    idx = line_end
                    self.noteView.ids.w_textinput.text = "{}{}{}".format(
                        self.noteView.ids.w_textinput.text[:line_end].rstrip(),
                        " #Now",
                        self.noteView.ids.w_textinput.text[line_end:],
                    )
            line_end = self.noteView.ids.w_textinput.text.find("\n", idx)
            if index > idx:
                self.set_cursor(line_end)
            else:
                self.set_cursor(index)

    def do_toggletask(self, *kwargs):
        index = self.noteView.ids.w_textinput.cursor_index()

        if index >= 0:
            _text = self.noteView.ids.w_textinput.text
            line_start = _text.rfind("\n", 0, index)
            line_end = _text.find("\n", index)
            if line_end == -1:
                line_end = len(_text)
            if line_start < 0:
                line_start = -1

            idx = _text.find("- [ ]", line_start + 1, line_end)
            if idx >= 0:
                self.noteView.ids.w_textinput.text = "{}{}{}".format(
                    self.noteView.ids.w_textinput.text[: idx + 3],
                    "x",
                    self.noteView.ids.w_textinput.text[idx + 4 :],
                )
            else:
                idx = _text.find("- [x]", line_start + 1, line_end)
                if idx >= 0:
                    self.noteView.ids.w_textinput.text = "{}{}{}".format(
                        self.noteView.ids.w_textinput.text[:idx],
                        "- ",
                        self.noteView.ids.w_textinput.text[idx + 6 :],
                    )
                else:
                    idx = _text.find("- ", line_start + 1, line_end)
                    if idx >= 0:
                        self.noteView.ids.w_textinput.text = "{}{}{}".format(
                            self.noteView.ids.w_textinput.text[:idx],
                            "- [ ] ",
                            self.noteView.ids.w_textinput.text[idx + 2 :],
                        )
                    else:
                        self.noteView.ids.w_textinput.text = "{}{}{}".format(
                            self.noteView.ids.w_textinput.text[: line_start + 1],
                            "- ",
                            self.noteView.ids.w_textinput.text[line_start + 1 :],
                        )
            self.set_cursor(
                index + (len(self.noteView.ids.w_textinput.text) - len(_text))
            )

    def go_settings(self):
        self.root.ids.sm.transition.direction = "left"
        self.root.ids.sm.current = "settings"

    def go_timepicker(self):

        d = None
        if self.root.ids.sm.previous == "noteView":
            index = self.noteView.ids.w_textinput.cursor_index()
            _text = self.noteView.ids.w_textinput.text
        else:
            index = 0
            _text = self.root.ids.todoView.ids.w_text.text
            if self.root.ids.todoView.ids.w_time.selected:
                self.root.ids.todoView.ids.w_time.selected = False
                return
            self.root.ids.todoView.ids.w_time.selected = True

        if index >= 0:
            line_start = _text.rfind("\n", 0, index)
            line_end = _text.find("\n", index)

            if line_end == -1:
                line_end = len(_text)
            if line_start < 0:
                line_start = 0

            d = re.search(r"\<(.*?)\>", _text[line_start:line_end])

        try:
            dt = parse(d.group(1))
        except Exception:
            dt = datetime.datetime.now()
            print("exception", dt)

        dtp = self.root.ids.datetimePickerView.ids.dtp
        dtp.day, dtp.month, dtp.year, dtp.hour, dtp.minute = (
            dt.day,
            dt.month,
            dt.year,
            dt.hour,
            (dt.minute // 5) * 5,
        )

        self.root.ids.sm.transition.direction = "left"
        self.root.ids.sm.previous = self.root.ids.sm.current
        self.root.ids.sm.current = "datetimepicker"
        if self.root.ids.sm.previous == "noteView":
            self.root.ids.datetimePickerView.fn = self.insertDatetimeNoteView
        else:
            self.root.ids.datetimePickerView.fn = self.insertDatetimeAdd

    def go_today(self):
        self.display_add = True
        self.display_toolbar = False
        self.root.ids.sm.transition.direction = "right"
        self.root.ids.sm.current = "today"
        self.load_today()
        # self.sync()

    @property
    def notes_fn(self):
        return join(self.user_data_dir, "notes")

    @property
    def settings_fn(self):
        return join(self.user_data_dir, ".settings.json")

    def on_resume(self):
        if self.noteView:
            self.noteView.ids.w_textinput.focus = True
            self.noteView.ids.w_textinput.focus = False
        self.sync()

    def on_new_intent(self, intent):
        text = None
        try:
            text = intent.getStringExtra(intent.EXTRA_TEXT)
            print(intent.getExtras())
        except Exception as err:
            print("Can t read INTENT : %" % err)

        if text:
            self.root.ids.todoView.ids.w_text.text = text
            Clock.schedule_once(self.add_todo, 1)


if __name__ == "__main__":
    LabelBase.register(
        name="awesome", fn_regular="datas/font_awesome_5_free_solid_900.otf"
    )
    d = BrOrg()
    d.run()
