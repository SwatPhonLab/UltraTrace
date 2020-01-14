# UltraTrace REST API

OK, I'm going to try to enumerate the endpoints we would need for a REST API (based on [#126](https://github.com/SwatPhonLab/UltraTrace/issues/126) and an offline conversation with Caleb, I think this framework makes the most sense for us at the moment).

One quick question: we're assuming one backend per frontend right (i.e., not running the backend as a daemon)?  If we're not, we'll have to manage concurrency somehow.  I think for `v1` we can assume that only one user will be editing a given project at a time.

The responses listed below are all for `200`-level status codes.  Obviously, the backend should return `400`-level codes for malformed input.

#### `GET /project`
- request:
```python
{
    "path": str
}
```
- response:
```python
{
    # List of known file names (i.e., "bundles"), where each
    # item is a tuple (filename, files), where files is a list
    # of tuples (filetype, filepath), where filetype is one of
    # ImageSet, Alignment, etc.
    "files": Sequence[Tuple[str, Sequence[Tuple[str, Optional[str]]]]],
    # Tuple of (default_trace_id, traces), where traces is a tuple
    # (trace_id, name, color).
    "traces": Tuple[Optional[int], Sequence[Tuple[int, str, str]]]
}
```

#### `GET /image`
- request:
```python
{
    "project": str,  # i.e., root path
    "filename": str,
    "frame": int,
}
```
- response:
```python
{
    # base64 encoded PNG? could we also just stream the bytes?
    "data": str,
    "width": int,
    "height": int,
    # List of tuples (trace_id, x, y)
    "traces": Sequence[Tuple[int, float, float]]
}
```

#### `GET /alignment`
- request:
```python
{
    "project": str,
    "filename": str,
}
```
- response:
```python
{
    # A list of tiers, where each tier is a tuple of (name, list
    # of intervals), where each interval is a tuple of (start,
    # stop, content)
    "tiers": Sequence[Tuple[str,Sequence[Tuple[int,int,str]]]]
}
```

#### `GET /spectrogram`
- request:
```python
{
    "project": str,
    "filename": str,
    "start_time_ms": int,
    "stop_time_ms": int,
    "window_length": float,
    "max_frequency": int,
    "dynamic_range": int,
    "n_slices": int,
}
```
- response:
```python
{
    # see comment for /image response
    "data": str,
    "width": int,
    "height": int,
}
```

#### `GET /audio`
- request:
```python
{
    # See Accept-Ranges[1] header spec for details on how we might
    # implement play/pause at arbitrary points.  I'm not sure how
    # we'll want to implement syncing the audio to the images /
    # spectrogram vertical-bar.
    #
    # [1] https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Ranges
    "project": str,
    "filename": str,
    "time": int,
}
```
- response:
```python
{
    # see comment for /image response
    "data": str,
}
```

#### `PUT /traces/default`
- request:
```python
{
    "project": str,
    "trace_id": int,
}
```
- response:
```python
null
```

#### `PUT /traces/name`
- request:
```python
{
    "project": str,
    "trace_id": int,
    "new_name": str,
}
```
- response:
```python
null
```

#### `PUT /traces/color`
- request:
```python
{
    "project": str,
    "trace_id": int,
    "new_color": str,
}
```
- response:
```python
null
```

#### `POST /traces/create`
- request:
```python
{
    "project": str,
    "name": str,
    "color": str,
}
```
- response:
```python
{
    "trace_id": int
}
```

#### `POST /traces/delete`
- request:
```python
{
    "project": str,
    "trace_id": int,
}
```
- response:
```python
null
```

#### `PUT /xhairs/move`
- request:
```python
{
    "project": str,
    "xhair_id": int,
    "x": float,
    "y": float,
}
```
- response:
```python
null
```

#### `POST /xhairs/create`
- request:
```python
{
    "project": str,
    "filename": str,
    "frame": int,
    "trace_id": int,
    "x": float,
    "y": float,
}
```
- response:
```python
{
    "xhair_id": int
}
```

#### `PUT /xhairs/delete`
- request:
```python
{
    "project": str,
    "xhair_id": int,
}
```
- response:
```python
null
```

#### `GET /search`
- request:
```python
{
    "project": str,
    "pattern": str,
}
```
- response:
```python
# ?
```

#### `POST /export`
- request:
```python
{
    "project": str,
    # Export all of our trace data to some json-encoded string and dumps
    # that into <filepath>.
    "filepath": str,
}
```
- response:
```python
# ?
```

###### FIXME: Figure out what the "Offset" spinbox in the lower left-hand corner does
