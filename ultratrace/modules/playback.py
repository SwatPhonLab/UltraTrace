from .base import Module
import tkinter as tk

class Playback(Module):
    def __init__(self, app):
        self.frame = tk.Frame(self.app.BOTTOM)
        self.playBtn = tk.Button(self.frame, text="Play/Pause", command=self.playpauseAV, state='disabled', takefocus=0) # NOTE: not currently appearing
        self.app.bind('<space>', self.playpauseAV )
        self.app.bind('<Escape>', self.stopAV )

    def reset(self):
        self.playBtn.config( state='normal' )

    def grid(self):
        self.frame.grid( row=0 )
        self.playBtn.grid()

    def grid_remove(self):
        self.frame.grid_remove()
        self.playBtn.grid_remove()

