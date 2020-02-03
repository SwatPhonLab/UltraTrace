from typing import Any, Sequence, Type, TYPE_CHECKING, TypeVar, Union
from werkzeug.datastructures import ImmutableMultiDict

from .project_cache import get_project_by_path
from ..model.color import Color
from ..model.project import Project
from ..model.trace import Trace
from ..model.xhair import XHair


if TYPE_CHECKING:
    RequestArgs = ImmutableMultiDict[Any, Any]
else:
    RequestArgs = ImmutableMultiDict


class ValidationError(TypeError):
    def __init__(self, name: str, cls: type, args: RequestArgs):
        super().__init__(
            f"Invalid request param: '{name}': got '{type(args.get(name, None))}', expecting '{cls}'"
        )


def project(args: RequestArgs) -> Project:
    if "path" not in args:
        raise ValidationError("path", str, args)
    return get_project_by_path(args["path"])


def filename(args: RequestArgs, project: Project) -> str:
    if "filename" not in args:
        raise ValidationError("filename", str, args)
    raise NotImplementedError()


def filenames(args: RequestArgs, project: Project) -> Sequence[str]:
    if "filenames" not in args:
        raise ValidationError("filenames", list, args)
    raise NotImplementedError()


def frame(args: RequestArgs, project: Project, filename: str) -> int:
    if "frame" not in args:
        raise ValidationError("frame", int, args)
    try:
        frame = int(args["frame"])
        raise NotImplementedError()
    except TypeError as e:
        raise ValidationError("frame", int, args) from e


def trace(args: RequestArgs, project: Project) -> Trace:
    raise NotImplementedError()


def xhair(args: RequestArgs, project: Project) -> XHair:
    raise NotImplementedError()


def color(args: RequestArgs, name: str) -> Color:
    raise NotImplementedError()


def tier_names(args: RequestArgs, project: Project) -> Sequence[str]:
    raise NotImplementedError()


# _ValidateType = TypeVar("_ValidateType", bound=Union[Type[int], Type[float], Type[str]])
_ValidateType = TypeVar("_ValidateType", int, float, str)


def primitive(args: RequestArgs, name: str, cls: Type[_ValidateType]) -> _ValidateType:
    if name not in args:
        raise ValidationError(name, cls, args)
    try:
        return cls(args[name])
    except TypeError as e:
        raise ValidationError(name, cls, args) from e
