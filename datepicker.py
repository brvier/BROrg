"""
Datetime Picker
=====

A simple datetime picker for BrOrg
fork of https://gist.github.com/el3/4db1060a4328ae8bbcd9a0fe07826a2b (github.com/el3)
"""
__version__ = "0.1.0"


from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    NumericProperty,
)


KV = """
#:import Calendar calendar.Calendar

<ActionButton@ButtonBehavior+Label>:
    canvas:
        Color:
            rgba: (1, 1, 1, 0.1) if self.text != "" else (0,0,0,0) 
        Rectangle:
            pos: self.pos[0] + dp(1), self.pos[1] + dp(1)
            size: self.size[0] - dp(2), self.size[1] - dp(2) 
    size_hint: 1, 1 
<Day@ButtonBehavior+Label>:
    canvas:
        Color:
            rgba: (1, 1, 1, 0.1) if self.text != "" else (0,0,0,0) 
        Rectangle:
            pos: self.pos[0] + dp(1), self.pos[1] + dp(1)
            size: self.size[0] - dp(2), self.size[1] - dp(2) 
        
    selected: False if self.text=='' else (root.parent.parent.day == int(self.text))
    datepicker: self.parent.datepicker
    color: [1,1,1,1] if not self.selected else [1,0,0,1]
    background_color: [1,1,1,1] if self.text != "" else [0,0,0,0]
    disabled: True if self.text == "" else False
    on_release:
        root.datepicker.day = int(self.text)

<Week@BoxLayout>:
    datepicker: root.parent
    weekdays: ["","","","","","",""]
    Day:
        text: str(root.weekdays[0])
    Day:
        text: str(root.weekdays[1])
    Day:
        text: str(root.weekdays[2])
    Day:
        text: str(root.weekdays[3])
    Day:
        text: str(root.weekdays[4])
    Day:
        text: str(root.weekdays[5])
    Day:
        text: str(root.weekdays[6])

<WeekDays@BoxLayout>:
    Label:
        text: "Mon"
    Label:
        text: "Tue"
    Label:
        text: "Wed"
    Label:
        text: "Thu"
    Label:
        text: "Fri"
    Label:
        text: "Sat"
    Label:
        text: "Sun"

<NavBar@BoxLayout>:
    datepicker: self.parent
    ActionButton:
        text: "<"
        on_release:
            if root.datepicker.month == 1: root.datepicker.year -= 1
            root.datepicker.month = 12 if root.datepicker.month == 1 else root.datepicker.month - 1

    Label:
        text: "%s %s" % (root.datepicker.months[root.datepicker.month-1], str(root.datepicker.year))
        color: 1,0,0,1
  
    ActionButton:
        text: ">"
        on_release:
            if root.datepicker.month == 12: root.datepicker.year += 1
            root.datepicker.month = 1 if root.datepicker.month == 12 else root.datepicker.month + 1
<NavTimeBar@BoxLayout>:
    datepicker: self.parent
    ActionButton:
        text: "<<"
        on_release:
            root.datepicker.hour = 23 if root.datepicker.hour == 0 else root.datepicker.hour - 1
    ActionButton:
        text: "<"
        on_release:
            if root.datepicker.minute <=0  : root.datepicker.hour -= 1
            root.datepicker.minute = 55 if root.datepicker.minute == 0 else root.datepicker.minute - 5


    Label
        text: "%02d:%02d" % (root.datepicker.hour,root.datepicker.minute)
        color: 1,0,0,1
 
    ActionButton:
        text: ">"
        on_release:
            if root.datepicker.minute >= 55: root.datepicker.hour += 1
            root.datepicker.minute = 0 if root.datepicker.minute == 55 else root.datepicker.minute + 5

    ActionButton:
        text: ">>"
        on_release:
            root.datepicker.hour = 0 if root.datepicker.hour == 23 else root.datepicker.hour + 1



 

<DatetimePicker@BoxLayout>:
    picked: ["","",""]
    months: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    calendar: Calendar()
    days: [(i if i > 0 else "") for i in self.calendar.itermonthdays(self.year, self.month)] + [""] * 14
    orientation: "vertical"
    NavBar:
    WeekDays:
    Week:
        weekdays: root.days[0:7]
    Week:
        weekdays: root.days[7:14]
    Week:
        weekdays: root.days[14:21]
    Week:
        weekdays: root.days[21:28]
    Week:
        weekdays: root.days[28:35]
    Week:
        weekdays: root.days[35:]
    NavTimeBar:
"""


class DatetimePicker(BoxLayout):
    day = NumericProperty(1)
    month = NumericProperty(1)
    year = NumericProperty(2022)
    hour = NumericProperty(12)
    minute = NumericProperty(0)


Builder.load_string(KV)

if __name__ == "__main__":
    import datetime

    class MyApp(App):
        def build(self):
            dp = DatetimePicker()
            now = datetime.datetime.now()
            dp.day = now.day
            dp.year = now.year
            dp.month = now.month
            dp.hour = now.hour
            dp.minute = (now.minute // 5) * 5  # round to 5min
            print(dp)
            return dp

    MyApp().run()
