from ultratrace.gui2 import GUI

class NoOp:
    def __getattribute__(*args, **kwargs):
        return NoOp()
    def __call__(*args, **kwargs):
        return NoOp()
    def __radd__(self, other):
        return other

g = GUI(NoOp(), NoOp())

g.mainloop()
