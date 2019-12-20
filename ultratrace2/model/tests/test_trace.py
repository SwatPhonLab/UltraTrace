from ..color import Color
from ..trace import Trace, TraceList


def test_change_color(mocker):
    mock_get_random_color = mocker.patch("ultratrace2.model.trace.get_random_color")
    initial_color = Color(0, 0, 0)
    final_color = Color(100, 0, 0)
    tr = Trace("test", initial_color)

    color_pre_change = tr.get_color()
    change_color_ret = tr.change_color(final_color)
    color_post_change = tr.get_color()

    assert color_pre_change == initial_color == change_color_ret
    assert color_post_change == final_color
    mock_get_random_color.assert_not_called()


def test_change_random_color(mocker):
    mock_get_random_color = mocker.patch("ultratrace2.model.trace.get_random_color")
    initial_color = Color(0, 0, 0)
    final_color = Color(100, 0, 0)
    mock_get_random_color.return_value = final_color
    tr = Trace("test", initial_color)

    color_pre_change = tr.get_color()
    change_color_ret = tr.change_color(None)
    color_post_change = tr.get_color()

    assert color_pre_change == initial_color == change_color_ret
    assert color_post_change == final_color
    mock_get_random_color.assert_called_once()


def test_change_name():
    initial_name = "test"
    final_name = "testtest"
    tr = Trace(initial_name, Color(0, 0, 0))

    name_pre_change = tr.get_name()
    change_name_ret = tr.change_name(final_name)
    name_post_change = tr.get_name()

    assert name_pre_change == initial_name == change_name_ret
    assert name_post_change == final_name


def test_add_xhair(mocker):
    MockFileBundle = mocker.patch("ultratrace2.model.files.bundle.FileBundle")
    file_bundle = MockFileBundle.return_value
    tr = Trace("test", Color(0, 0, 0))

    len_xhairs_pre = len(tr.xhairs)
    tr.add_xhair(file_bundle, 0, 0.0, 0.0)
    len_xhairs_post = len(tr.xhairs)

    assert len_xhairs_pre == 0
    assert len_xhairs_post == 1
    assert len(tr.xhairs[file_bundle][0]) == 1


def test_add_trace():
    tl = TraceList()
    tr = tl.add_trace("test", Color(0, 0, 0))
    assert tr.id in tl.traces
