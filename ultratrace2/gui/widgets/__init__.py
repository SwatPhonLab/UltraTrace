ALIGN_HORIZONTAL = "horiz"
ALIGN_VERTICAL = "vert"


class Widget:
    def __init__(self, align=ALIGN_VERTICAL, children=[]):

        if align not in (ALIGN_HORIZONTAL, ALIGN_VERTICAL):
            raise ValueError("Unknown alignment: " + align)
        self.align = align
        self.children = children

    def is_loaded(self):
        return True

    def __iter__(self):
        for child in self.children:
            yield child

    def __len__(self):
        return len(self.children)


class OptionalWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_imported = False

    def is_loaded(self):
        return self.is_imported
