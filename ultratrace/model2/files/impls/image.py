from ..ADT import TypedFile, TypedFileImpl

class Image(TypedFile):

    class PNG(TypedFileImpl):
        mimetypes = ['image/png']
        extensions = ['.png']
        def load(self):
            raise NotImplementedError()

    class DICOM(TypedFileImpl):
        mimetypes = ['application/dicom']
        extensions = ['.dicom', '.dcm']
        def load(self):
            raise NotImplementedError()

    preferred_impls = [PNG, DICOM]

    def __init__(self):
        super().__init__()
