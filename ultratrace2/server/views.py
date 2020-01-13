from flask import Flask, request

import logging

from . import app
from . import validate


logger = logging.getLogger(__name__)


@app.route("/project", methods=["PUT"])
def load_project():
    """Main entrypoint.

    NB: To get the actual filename-specific data for a filetype, call
        appropriate /<filetype> endpoint.

    PUT /project?path=<str>
    {
        "bundles": [
            {
                "$filename": {
                    "has_alignment": boolean
                    "has_images": boolean
                    "has_sound": boolean
                    "has_spectrogram": boolean
                },
                ...
            },
            ...
        ],
        "traces": [
            {
                "$trace_id": {
                    "name": str,
                    "color": str
                },
                ...
            },
            ...
        ]
    }
    """
    try:
        project = validate.project(request.args)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/image", methods=["GET"])
def load_image():
    """Load *.dicom, *.png, etc.

    NB: "data" is serialized as a base64-encoded PNG file

    GET /image?path=<str>&filename=<str>&frame=<int>
    {
        "data": str,
        "xhairs": {
            "$xhair_id": {
                "trace_id": int,
                "x": float,
                "y": float
            },
            ...
        }
    }
    """
    try:
        project = validate.project(request.args)
        filename = validate.filename(request.args, project)
        frame = validate.frame(request.args, project, filename)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/spectrogram", methods=["GET"])
def get_spectrogram():
    """Load *.pmpkl, etc.

    NB: "data" is serialized as a base64-encoded PNG file

    GET /spectrogram?path=<str>&filename=<str>&start_time_ms=<float>&stop_time_ms=<float>\
            &window_length=<float>&max_frequency=<float>&dynamic_range=<float>&n_slices=<int>
    {
        "data": str
    }
    """
    try:
        project = validate.project(request.args)
        filename = validate.filename(request.args, project)
        start_time_ms = validate.primitive(request.args, "start_time_ms", int)
        stop_time_ms = validate.primitive(request.args, "stop_time_ms", int)
        window_length = validate.primitive(request.args, "window_length", float)
        max_frequency = validate.primitive(request.args, "max_frequency", float)
        dynamic_range = validate.primitive(request.args, "dynamic_range", float)
        n_slices = validate.primitive(request.args, "n_slices", int)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/audio", methods=["GET"])
def get_audio():
    """Load *.wav, etc.

    #FIXME: How do we want to serialize this data?  Should it be sent all at once
            as a single base64-encoded string or requested in chunks?  If in chunks,
            then we'll need to require a "&frame=<int>" parameter and the Accept-Ranges
            header.

    GET /audio?path=<str>&filename=<str>[&frame=<int>]
    {
        "data": str
    }
    """
    try:
        project = validate.project(request.args)
        filename = validate.filename(request.args, project)
        frame = validate.frame(request.args, project, filename)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/alignment", methods=["GET"])
def get_alignment():
    """Load *.TextGrid, etc.

    NB: We'll have to do something different for Point/Interval tiers -- maybe set
        start_time == stop_time?

    GET /textgrid&path=<str>&filename=<str>
    {
        "offset": float,
        "tiers": [
            {
                "name": str,
                "intervals": [
                    {
                        "start_ms": int,
                        "stop_ms": int,
                        "label": str
                    },
                    ...
                ]
            },
            ...
        ]
    }
    """
    try:
        project = validate.project(request.args)
        filename = validate.filename(request.args, project)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/alignment/offset", methods=["PUT"])
def set_alignment_offset():
    """Set the offset for a given filename

    PUT /alignment/offset?path=<str>&filename=<str>&offset=<float>
    null
    """
    try:
        project = validate.project(request.args)
        filename = validate.filename(request.args, project)
        offset = validate.primitive(request.args, "offset", int)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/traces/default", methods=["PUT"])
def set_default_trace():
    """Set the default trace

    PUT /traces/default?path=<str>&trace_id=<int>
    null
    """
    try:
        project = validate.project(request.args)
        trace = validate.trace(request.args, project)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/traces/name", methods=["PUT"])
def set_trace_name():
    """Set the trace's name

    PUT /traces/name?path=<str>&trace_id=<int>&new_name=<str>
    null
    """
    try:
        project = validate.project(request.args)
        trace = validate.trace(request.args, project)
        new_name = validate.primitive(request.args, "new_name", str)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/traces/color", methods=["PUT"])
def set_trace_color():
    """Set the trace's color

    NB: <new_color> should be given as a six-digit hex string
        (e.g., 00ff00).

    PUT /traces/color?path=<str>&trace_id=<int>&new_color=<str>
    null
    """
    try:
        project = validate.project(request.args)
        trace = validate.trace(request.args, project)
        new_color = validate.color(request.args, "new_color")
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/traces/create", methods=["POST"])
def create_trace():
    """Add a new trace

    NB: <color> should be given as a six-digit hex string
        (e.g. 00ff00).

    PUT /traces/create?path=<str>&name=<str>&color=<str>
    {
        "trace_id": int
    }
    """
    try:
        project = validate.project(request.args)
        name = validate.primitive(request.args, "name", str)
        color = validate.color(request.args, "color")
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/traces/delete", methods=["POST"])
def delete_trace():
    """Delete a trace

    POST /traces/delete?path=<str>&trace_id=<int>
    null
    """
    try:
        project = validate.project(request.args)
        trace = validate.trace(request.args, project)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/xhairs/move", methods=["PUT"])
def move_xhair():
    """Update an xhair's (x,y) position

    PUT /xhairs/move?path=<str>&xhair_id=<int>&x=<float>&y=<float>
    null
    """
    try:
        project = validate.project(request.args)
        xhair = validate.xhair(request.args, project)
        x = validate.primitive(request.args, "x", float)
        y = validate.primitive(request.args, "y", float)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/xhairs/create", methods=["POST"])
def create_xhair():
    """Create a new xhair with given parameters

    POST /xhairs/create?path=<str>&filename=<str>&frame=<int>&trace_id=<int>&x=<float>&y=<float>
    {
        "xhair_id": int
    }
    """
    try:
        project = validate.project(request.args)
        filename = validate.filename(request.args, project)
        frame = validate.frame(request.args, project, filename)
        trace = validate.trace(request.args, project)
        x = validate.primitive(request.args, "x", float)
        y = validate.primitive(request.args, "y", float)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/xhairs/delete", methods=["POST"])
def delete_xhair():
    """Delete an xhair

    POST /xhairs/delete?path=<str>&xhair_id=<int>
    null
    """
    try:
        project = validate.project(request.args)
        xhair = validate.xhair(request.args, project)
        raise NotImplementedError()
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/search", methods=["GET"])
def search():
    """Search query across project

    GET /search?path=<str>&filenames=<List<str>>&tier_names=<List<str>>&query=<str>
    {
        "matches": [
            {
                "filename": str,
                "tier_name": str,
                "interval": {
                    "start_ms": float,
                    "stop_ms": float,
                    "label": str
                }
            },
            ...
        ]
    }
    """
    try:
        project = validate.project(request.args)
        filenames = validate.filenames(request.args, project)
        tier_names = validate.tier_names(request.args, project)
        query = validate.primitive(request.args, "query", str)
    except validate.ValidationError as e:
        logger.error(e)
        return str(e), 400


@app.route("/export", methods=["POST"])
def export():
    raise NotImplementedError()
