from .themes import ThemedTk, get_theme
from .widgets import (
    Button,
    Div,
    Frame,
    Label,
)
from .. import utils

class GUI(ThemedTk):
    def __init__(self, app, args):

        if hasattr(super(), 'set_theme'):
            theme = get_theme(args.theme)
            if theme is not None:
                utils.info('Using TtkTheme: ' + theme)
                super().__init__(theme=theme)
            else:
                super().__init__()
        else:
            super().__init__()

        self.app = app

        '''
        self.audio = Audio(app, args)
        self.control = Control(app, args)
        self.dicom = Dicom(app, args)
        self.spectrogram = Spectrogram(app, args)
        self.textgrid = TextGrid(app, args)
        self.trace = Trace(app, args)
        self.undo = Undo(app, args)
        self.video = Video(app, args)
        '''

        self.root = Div(self)
        self.root.grid(row=0, column=0, sticky='news')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        top = Div(self.root)
        top.grid()
        left = Div(top)
        left.grid()
        participants = Div(left)
        participants.grid()
        participants_label = Label(participants, text="Choose a participant:")
        participants_label.grid()
        participants_button_group = Div(participants)
        participants_button_group.grid()
        participants_left_button = Button(participants_button_group, text="<")
        participants_left_button.grid(row=0, column=0)
        participants_right_button = Button(participants_button_group, text=">")
        participants_right_button.grid(row=0, column=1)
        files = Div(left)
        files.grid()
        files_label = Label(files, text="Choose a file:")
        files_label.grid()
        files_button_group = Div(files)
        files_button_group.grid()
        files_left_button = Button(files_button_group, text="<")
        files_left_button.grid(row=0, column=0)
        files_right_button = Button(files_button_group, text=">")
        files_right_button.grid(row=0, column=1)
        frames = Div(left)
        frames.grid()
        frames_label = Label(frames, text="Choose a frame:")
        frames_label.grid()
        frames_button_group = Div(frames)
        frames_button_group.grid()
        frames_left_button = Button(frames_button_group, text="<")
        frames_left_button.grid(row=0, column=0)
        frames_right_button = Button(frames_button_group, text=">")
        frames_right_button.grid(row=0, column=1)
        trace = Div(left)
        trace.grid()
        trace_label = Label(trace, text="Choose a trace:")
        trace_label.grid()
        trace_button_group = Div(trace)
        trace_button_group.grid()
        trace_set_as_default_button = Button(trace_button_group, text="Set as default")
        trace_set_as_default_button.grid(row=0, column=0)
        trace_select_all_button = Button(trace_button_group, text="Select all")
        trace_select_all_button.grid(row=1, column=0)
        trace_copy_paste_button_group = Div(trace_button_group)
        trace_copy_paste_button_group.grid(row=2, column=0)
        trace_copy_button = Button(trace_copy_paste_button_group, text="copy")
        trace_copy_button.grid(row=0, column=0)
        trace_paste_button = Button(trace_copy_paste_button_group, text="paste")
        trace_paste_button.grid(row=0, column=1)
        '''
        self.root = Container(app, ALIGN_VERTICAL,
            Container(app, ALIGN_HORIZONTAL,
                Container(app, ALIGN_VERTICAL,
                    self.control,
                    self.trace,
                    self.undo,
                ),
                self.dicom,
            ),
            Container(app, ALIGN_VERTICAL,
                self.spectrogram,
                self.textgrid,
            ),
        )
        '''
