from . import get_platform
from string import ascii_lowercase

class InputEvent:
    def __init__(self, tk_name, is_mod=False, is_alt=False, is_shift=False):
        self.tk_name = tk_name
        self.is_mod = is_mod
        self.is_alt = is_alt
        self.is_shift = is_shift

    def __or__(self, other):
        pass

    def __and__(self, other):
        pass

    def __str__(self):
        s = '<'
        if s.is_mod:
            s
class SpecialKey(InputEvent):
    def __init__(self, tk_name, is_mod=False, is_alt=False, is_shift=False):
        super().__init__(tk_name, is_mod=is_mod, is_alt=is_alt, is_shift=is_shift)

class AlphaKey(InputEvent):
    def __init__(self, char):
        super().__init__(char)

class ButtonEvent(InputEvent):
    def __init__(self, name):
        super().__init__(name)

class ButtonEventGroup:
    def __init__(self, num):
        self.click = ButtonEvent(f'Button-{num}')
        self.double_click = ButtonEvent(f'Double-Button-{num}')
        self.triple_click = ButtonEvent(f'Triple-Button-{num}')
        self.motion = ButtonEvent(f'B{num}-Motion')
        self.release = ButtonEvent(f'ButtonRelease-{num}')

MOUSE_LEFT = ButtonEventGroup(1)
MOUSE_MIDDLE = ButtonEventGroup(2)
MOUSE_RIGHT = ButtonEventGroup(3)

__platform = get_platform()
if __platform == 'Linux':
    KEY_MOD = SpecialKey('Control', is_mod=True)
    KEY_ALT = SpecialKey('Alt', is_alt=True)
    MOUSE_SCROLL_UP = ButtonEventGroup(4)
    MOUSE_SCROLL_DOWN = ButtonEventGroup(5)
elif __platform == 'Darwin':
    KEY_MOD = SpecialKey('Command', is_mod=True)
    KEY_ALT = SpecialKey('Option', is_alt=True)
    #MOUSE_SCROLL_UP = SpecialKey('MouseWheel', is_button=True)
    #MOUSE_SCROLL_DOWN = SpecialKey('MouseWheel', is_button=True)
else:
    raise NotImplementedError('what does tkinter call Windows other keyboard events?')
    #MOUSE_SCROLL_UP = SpecialKey('MouseWheel', is_button=True)
    #MOUSE_SCROLL_DOWN = SpecialKey('MouseWheel', is_button=True)

KEY_SHIFT = SpecialKey('Shift', is_shift=True)
KEY_BACKSPACE = SpecialKey('BackSpace')
KEY_A = AlphaKey('a')
KEY_B = AlphaKey('b')
KEY_C = AlphaKey('c')
KEY_D = AlphaKey('d')
KEY_E = AlphaKey('e')
KEY_F = AlphaKey('f')
KEY_G = AlphaKey('g')
KEY_H = AlphaKey('h')
KEY_I = AlphaKey('i')
KEY_J = AlphaKey('j')
KEY_K = AlphaKey('k')
KEY_L = AlphaKey('l')
KEY_M = AlphaKey('m')
KEY_N = AlphaKey('n')
KEY_O = AlphaKey('o')
KEY_P = AlphaKey('p')
KEY_Q = AlphaKey('q')
KEY_R = AlphaKey('r')
KEY_S = AlphaKey('s')
KEY_T = AlphaKey('t')
KEY_U = AlphaKey('u')
KEY_V = AlphaKey('v')
KEY_W = AlphaKey('w')
KEY_X = AlphaKey('x')
KEY_Y = AlphaKey('y')
KEY_Z = AlphaKey('z')
KEY_EQUAL = SpecialKey('equal')
KEY_MINUS = SpecialKey('minus')
KEY_ESCAPE = SpecialKey('Escape')
KEY_UP = SpecialKey('Up')
KEY_DOWN = SpecialKey('Down')
KEY_LEFT = SpecialKey('Left')
KEY_RIGHT = SpecialKey('Right')

for k, v in dict(globals()).items():
    if str(k).startswith('KEY_') or str(k).startswith('MOUSE_'):
        print(str(v))
