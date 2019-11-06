import utils

class Action:
    def __init__(self, *args):
        self.args = args

class Add(Action): pass
class Delete(Action): pass
class Move(Action): pass
class Recolor(Action): pass
class Rename(Action): pass

class Stack:
    def __init__(self):
        self.items = []
    def push(self, action):
        self.items.append(action)
    def pop(self):
        return self.items.pop()
    def __len__(self):
        return len(self.items)
    def clear(self):
        self.items = []

class UndoRedo:
    def __init__(self, app):
        self.app = app
        self.undos = Stack()
        self.redos = Stack()

    def clear(self):
        self.undos.clear()
        self.redos.clear()

    def push(self, action):
        self.undos.push(action)
        self.redos.clear()

    def undo(self):

        if not len(self.undos):
            utils.warn('Nothing to undo!')
            return

        action = self.undos.pop()

        if isinstance(action, Add):
            xhairs = item.args
            for xhair in xhairs:
                self.app.model.traces.remove(xhair)
            self.redos.push(Delete(*xhairs))

        elif isinstance(action, Delete):
            xhairs = items.args
            for xhair in xhairs:
                self.app.model.traces.add(xhair)
            self.redos.push(Add(xhairs))

        elif isinstance(action, Move):
            xhairs, coords = items.args
            for xhair, coord in zip(xhairs, coords):
                self.app.model.traces.move(xhair, coord)
            self.redos.push(Move( (xhairs, coords) ))

        elif isinstance(action, Recolor):
            trace, newColor = action.args
            oldColor = app.model.traces.get_color(trace)
            app.model.traces.change_color(trace, newColor)
            self.redos.push(Recolor( (trace, oldColor) ))

        elif isinstance(action, Rename):
            trace, oldName, newName = action.args
            app.model.traces.rename(trace, oldName) # "this is backwards on purpose"
            self.redos.push(Rename( (trace, newName, oldName) ))

    def redo(self):

        if not len(self.redos):
            utils.warn('Nothing to redo!')
            return

        action = self.redos.pop()

        if isinstance(action, Add):
            xhairs = item.args
            for xhair in xhairs:
                self.app.model.traces.remove(xhair)
            self.undos.push(Delete(*xhairs))

        elif isinstance(action, Delete):
            xhairs = items.args
            for xhair in xhairs:
                self.app.model.traces.add(xhair)
            self.undos.push(Add(xhairs))

        elif isinstance(action, Move):
            xhairs, coords = items.args
            for xhair, coord in zip(xhairs, coords):
                self.app.model.traces.move(xhair, coord)
            self.undos.push(Move( (xhairs, coords) ))

        elif isinstance(action, Recolor):
            trace, newColor = action.args
            oldColor = app.model.traces.get_color(trace)
            app.model.traces.change_color(trace, newColor)
            self.undos.push(Recolor( (trace, oldColor) ))

        elif isinstance(action, Rename):
            trace, oldName, newName = action.args
            app.model.traces.rename(trace, newName)
            self.undos.push(Rename( (trace, oldName, newName) ))

