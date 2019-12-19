from .base import AlignmentFileLoader


class MeasurementLoader(AlignmentFileLoader):
    # FIXME: what is this? do we need to support it?

    @classmethod
    def from_file(cls, path: str) -> "MeasurementLoader":
        raise NotImplementedError()
