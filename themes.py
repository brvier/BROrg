from kivy.properties import (
    ListProperty,
    StringProperty,
    NumericProperty,
    BooleanProperty,
    ObjectProperty,
)


from pygments.style import Style
from pygments.token import (
    Token,
    Comment,
    Name,
    Literal,
    Keyword,
    Generic,
    Number,
    Punctuation,
    Operator,
    String,
    Text,
    Error,
)


def get_light_theme():
    return {
        "name": "light",
        "screenbg": (1, 1, 1),
        "notebg": (1, 1, 1, 1),
        "notetextcolor": (0, 0, 0, 1),
        "toolbarbg": (0.8, 0.8, 0.8, 0.8),
        "toolbarcolor": (0.2, 0.2, 0.2, 1),
        "textinputbg": (0.8, 0.8, 0.8, 0.5),
        "textinputcolor": (0, 0, 0, 1),
        "circularbuttoncolor": (1, 1, 1, 1),
        "circularbuttonbg": (0.8, 0.2, 0.2, 1),
        "actionbuttonbg": (0, 0, 0, 0.1),
        "actionbuttoncolor": (0, 0, 0, 1),
        "actionselectedbuttoncolor": (1, 0, 0, 1),
        "daybuttonbg": (0, 0, 0, 0.1),
        "daybuttoncolor": (0, 0, 0, 1),
        "dayselectedbuttoncolor": (1, 0, 0, 1),
        "navbarcolor": (1, 0, 0, 1),
        "selectablebuttoncolor": (0, 0, 0, 1),
        "selectablebuttoncolorbg": (0.8, 0.8, 0.8, 1),
        "selectableselectedbuttoncolor": (1, 0, 0, 1),
        "labeltitle": (0.7, 0.7, 0.7, 1),
        "label": (0.7, 0.7, 0.7, 1),
        "textlistitemcolor": (0, 0, 0, 1),
        "textlistitemselectedcolor": (0, 0, 0, 1),
        "textlistitemiconcolor": (0, 0, 0, 1),
        "textlistitemselectediconcolor": (0, 0, 0, 1),
        "textlistitemsubcolor": (0.5, 0.5, 0.5, 1),
        "textlistitemselectedsubcolor": (0.5, 0.5, 0.5, 1),
        "textlistitembgcolor": (1, 1, 1, 1),
        "textlistitemselectedbgcolor": (0.8, 0.8, 0.8, 1),
        "syncingstatusbg": (0.9, 0.9, 0.9, 0.9),
        "syncingstatus": (0, 0, 0, 1),
        "pygmentstyle": GithubStyle,
    }


def get_gruvbox_theme():
    return {
        "name": "gruvbox",
        "screenbg": (0.1560, 0.1560, 0.1560, 1),
        "notebg": (0.1560, 0.1560, 0.1560, 1),
        "notetextcolor": (0.9216, 0.8588, 0.6980, 1),
        "toolbarbg": (0.2, 0.2, 0.2, 0.8),
        "toolbarcolor": (0.9, 0.9, 0.9, 1),
        "textinputbg": (0.2, 0.2, 0.2, 1),
        "textinputcolor": (0.9216, 0.8588, 0.6980, 1),
        "circularbuttoncolor": (1, 1, 1, 1),
        "circularbuttonbg": (0.8392, 0.3647, 0.0549, 1),
        "actionbuttonbg": (1, 1, 1, 0.1),
        "actionbuttoncolor": (1, 1, 1, 1),
        "actionselectedbuttoncolor": (1, 0, 0, 1),
        "daybuttonbg": (1, 1, 1, 0.1),
        "daybuttoncolor": (1, 1, 1, 1),
        "dayselectedbuttoncolor": (1, 0, 0, 1),
        "navbarcolor": (1, 0, 0, 1),
        "selectablebuttoncolor": (1, 1, 1, 1),
        "selectablebuttoncolorbg": (0.2, 0.2, 0.2, 1),
        "selectableselectedbuttoncolor": (1, 0, 0, 1),
        "labeltitle": (0.7, 0.7, 0.7, 1),
        "label": (0.7, 0.7, 0.7, 1),
        "textlistitemcolor": (1, 1, 1, 1),
        "textlistitemselectedcolor": (1, 1, 1, 1),
        "textlistitemiconcolor": (1, 1, 1, 1),
        "textlistitemselectediconcolor": (1, 1, 1, 1),
        "textlistitemsubcolor": (0.5, 0.5, 0.5, 1),
        "textlistitemselectedsubcolor": (0.5, 0.5, 0.5, 1),
        "textlistitembgcolor": (0.1560, 0.1560, 0.1560, 1),
        "textlistitemselectedbgcolor": (0.3, 0.3, 0.3, 1),
        "syncingstatusbg": (0.1, 0.1, 0.1, 0.9),
        "syncingstatus": (1, 1, 1, 1),
        "pygmentstyle": GruvboxDarkStyle,
    }


def get_dark_theme():
    return {
        "name": "dark",
        "screenbg": (0.1, 0.1, 0.1, 1),
        "notebg": (0.1, 0.1, 0.1, 1),
        "notetextcolor": (1, 1, 1, 1),
        "toolbarbg": (0.2, 0.2, 0.2, 0.8),
        "toolbarcolor": (0.9, 0.9, 0.9, 1),
        "textinputbg": (0.2, 0.2, 0.2, 1),
        "textinputcolor": (1, 1, 1, 1),
        "actionbuttonbg": (1, 1, 1, 0.1),
        "actionbuttoncolor": (1, 1, 1, 1),
        "actionselectedbuttoncolor": (1, 0, 0, 1),
        "circularbuttoncolor": (1, 1, 1, 1),
        "circularbuttonbg": (0.8, 0.2, 0.2, 1),
        "daybuttonbg": (1, 1, 1, 0.1),
        "daybuttoncolor": (1, 1, 1, 1),
        "dayselectedbuttoncolor": (1, 0, 0, 1),
        "navbarcolor": (1, 0, 0, 1),
        "selectablebuttoncolor": (1, 1, 1, 1),
        "selectablebuttoncolorbg": (0.2, 0.2, 0.2, 1),
        "selectableselectedbuttoncolor": (1, 0, 0, 1),
        "labeltitle": (0.7, 0.7, 0.7, 1),
        "label": (0.7, 0.7, 0.7, 1),
        "textlistitemcolor": (1, 1, 1, 1),
        "textlistitemselectedcolor": (1, 1, 1, 1),
        "textlistitemiconcolor": (1, 1, 1, 1),
        "textlistitemselectediconcolor": (1, 1, 1, 1),
        "textlistitemsubcolor": (0.5, 0.5, 0.5, 1),
        "textlistitemselectedsubcolor": (0.5, 0.5, 0.5, 1),
        "textlistitembgcolor": (0, 0, 0, 0),
        "textlistitemselectedbgcolor": (0.05, 0.05, 0.05, 1),
        "syncingstatusbg": (0.1, 0.1, 0.1, 0.9),
        "syncingstatus": (1, 1, 1, 1),
        "pygmentstyle": ZenburnStyle,
    }


class GruvboxDarkStyle(Style):
    """
    Pygments version of the "gruvbox" dark vim theme.
    """

    background_color = "#282828"
    highlight_color = "#ebdbb2"

    styles = {
        Token: "#dddddd",
        Comment: "italic #928374",
        Comment.PreProc: "#8ec07c",
        Comment.Special: "bold italic #ebdbb2",
        Keyword: "#fb4934",
        Operator.Word: "#fb4934",
        String: "#b8bb26",
        String.Escape: "#fe8019",
        Number: "#d3869b",
        Name.Builtin: "#fe8019",
        Name.Variable: "#83a598",
        Name.Constant: "#d3869b",
        Name.Class: "#8ec07c",
        Name.Function: "#8ec07c",
        Name.Namespace: "#8ec07c",
        Name.Exception: "#fb4934",
        Name.Tag: "#8ec07c",
        Name.Attribute: "#fabd2f",
        Name.Decorator: "#fb4934",
        Generic.Heading: "bold #ebdbb2",
        Generic.Subheading: "underline #ebdbb2",
        Generic.Deleted: "bg:#fb4934 #282828",
        Generic.Inserted: "bg:#b8bb26 #282828",
        Generic.Error: "#fb4934",
        Generic.Emph: "italic",
        Generic.Strong: "bold",
        Generic.Prompt: "#a89984",
        Generic.Output: "#f2e5bc",
        Generic.Traceback: "#fb4934",
        Error: "bg:#fb4934 #282828",
    }


class ZenburnStyle(Style):
    """
    Low contrast Zenburn style.
    """

    default_style = ""
    background_color = "#3f3f3f"
    highlight_color = "#484848"
    line_number_color = "#5d6262"
    line_number_background_color = "#353535"
    line_number_special_color = "#7a8080"
    line_number_special_background_color = "#353535"
    styles = {
        Token: "#dcdccc",
        Error: "#e37170 bold",
        Keyword: "#efdcbc",
        Keyword.Type: "#dfdfbf bold",
        Keyword.Constant: "#dca3a3",
        Keyword.Declaration: "#f0dfaf",
        Keyword.Namespace: "#f0dfaf",
        Name: "#dcdccc",
        Name.Tag: "#e89393 bold",
        Name.Entity: "#cfbfaf",
        Name.Constant: "#dca3a3",
        Name.Class: "#efef8f",
        Name.Function: "#efef8f",
        Name.Builtin: "#efef8f",
        Name.Builtin.Pseudo: "#dcdccc",
        Name.Attribute: "#efef8f",
        Name.Exception: "#c3bf9f bold",
        Literal: "#9fafaf",
        String: "#cc9393",
        String.Doc: "#7f9f7f",
        String.Interpol: "#dca3a3 bold",
        Number: "#8cd0d3",
        Number.Float: "#c0bed1",
        Operator: "#f0efd0",
        Punctuation: "#f0efd0",
        Comment: "#7f9f7f italic",
        Comment.Preproc: "#dfaf8f bold",
        Comment.PreprocFile: "#cc9393",
        Comment.Special: "#dfdfdf bold",
        Generic: "#ecbcbc bold",
        Generic.Emph: "#ffffff bold",
        Generic.Output: "#5b605e bold",
        Generic.Heading: "#efefef bold",
        Generic.Deleted: "#c3bf9f bg:#313c36",
        Generic.Inserted: "#709080 bg:#313c36 bold",
        Generic.Traceback: "#80d4aa bg:#2f2f2f bold",
        Generic.Subheading: "#efefef bold",
    }


class GithubStyle(Style):
    """
    Port of the github color scheme.
    """

    default_style = ""

    background_color = "#ffffff"

    styles = {
        Comment.Multiline: "italic #999988",
        Comment.Preproc: "bold #999999",
        Comment.Single: "italic #999988",
        Comment.Special: "bold italic #999999",
        Comment: "italic #999988",
        Error: "bg:#e3d2d2 #a61717",
        Generic.Deleted: "bg:#ffdddd #000000",
        Generic.Emph: "italic #000000",
        Generic.Error: "#aa0000",
        Generic.Heading: "#999999",
        Generic.Inserted: "bg:#ddffdd #000000",
        Generic.Output: "#888888",
        Generic.Prompt: "#555555",
        Generic.Strong: "bold",
        Generic.Subheading: "#aaaaaa",
        Generic.Traceback: "#aa0000",
        Keyword.Constant: "bold #000000 ",
        Keyword.Declaration: "bold #000000",
        Keyword.Namespace: "bold #000000",
        Keyword.Pseudo: "bold #000000",
        Keyword.Reserved: "bold #000000",
        Keyword.Type: "bold #445588",
        Keyword: "bold #000000",
        Literal.Number.Float: "#009999",
        Literal.Number.Hex: "#009999",
        Literal.Number.Integer.Long: "#009999",
        Literal.Number.Integer: "#009999",
        Literal.Number.Oct: "#009999",
        Literal.Number: "#009999",
        Literal.String.Backtick: "#d14",
        Literal.String.Char: "#d14",
        Literal.String.Doc: "#d14",
        Literal.String.Double: "#d14",
        Literal.String.Escape: "#d14",
        Literal.String.Heredoc: "#d14",
        Literal.String.Interpol: "#d14",
        Literal.String.Other: "#d14",
        Literal.String.Regex: "#009926",
        Literal.String.Single: "#d14",
        Literal.String.Symbol: "#990073",
        Literal.String: "#d14",
        Name.Attribute: "#008080",
        Name.Builtin.Pseudo: "#999999",
        Name.Builtin: "#0086B3",
        Name.Class: "bold #445588",
        Name.Constant: "#008080",
        Name.Decorator: "bold #3c5d5d",
        Name.Entity: "#800080",
        Name.Exception: "bold #990000",
        Name.Function: "bold #990000",
        Name.Label: "bold #990000",
        Name.Namespace: "#555555",
        Name.Tag: "#000080",
        Name.Variable.Class: "#008080",
        Name.Variable.Global: "#008080",
        Name.Variable.Instance: "#008080",
        Name.Variable: "#008080",
        Operator.Word: "bold #000000",
        Operator: "bold #000000",
        Text.Whitespace: "#bbbbbb",
    }


"""
class Theme(object):
    name = StringProperty("light")
    screenbg = ListProperty((1, 1, 1))


class GruvboxTheme(Theme):
    def __init__(
        self,
    ):
        self.name = "gruvbox"
        self.screenbg = (0.2, 0.1, 0.1)


class DarkTheme(Theme):
    def __init__(
        self,
    ):
        self.name = "dark"
        self.screenbg = (0.1, 0.1, 0.1)
"""
