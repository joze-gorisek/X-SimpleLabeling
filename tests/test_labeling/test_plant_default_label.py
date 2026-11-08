"""New polygons default to the plant name taken from the image filename."""

import copy
import os
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtGui, QtWidgets  # noqa: E402

import anylabeling.resources.resources  # noqa: E402,F401
from anylabeling import config as app_config  # noqa: E402
from anylabeling.views.labeling.settings.schema import (  # noqa: E402
    load_template_config,
)
from anylabeling.views.labeling.shape import Shape  # noqa: E402
from anylabeling.views.mainwindow import MainWindow  # noqa: E402


@pytest.fixture
def view(tmp_path, monkeypatch):
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.setattr(app_config, "_work_directory", str(tmp_path))
    config_file = tmp_path / "config.yaml"
    config_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(app_config, "current_config_file", str(config_file))
    settings_class = QtCore.QSettings
    monkeypatch.setattr(
        QtCore,
        "QSettings",
        lambda *args: settings_class(
            str(tmp_path / "settings.ini"), settings_class.Format.IniFormat
        ),
    )
    window = MainWindow(app, config=copy.deepcopy(load_template_config()))
    app.processEvents()
    yield window.labeling_widget.view
    window.labeling_widget.view.dirty = False
    window.close()
    app.removeEventFilter(window.labeling_widget.view)
    window.deleteLater()
    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)


def _draw_shape(view, shape_type):
    shape = Shape(shape_type=shape_type)
    for x, y in [(10, 10), (60, 10), (60, 60)]:
        shape.add_point(QtCore.QPointF(x, y))
    shape.close()
    view.canvas.shapes.append(shape)
    view.canvas.store_shapes()
    return shape


def _new_shape_with_popup(view, typed_label=None):
    """Run new_shape; the popup accepts its prefilled text (or typed_label)."""
    seen = {}

    def fake_pop_up(text=None, **kwargs):
        seen["text"] = text
        return (typed_label or text, {}, None, "", False, [])

    with patch.object(
        view.label_dialog, "pop_up", side_effect=fake_pop_up
    ), patch.object(view, "set_dirty"):
        view.new_shape()
    return seen.get("text")


def test_polygon_popup_defaults_to_lowercase_plant(view):
    view.filename = r"C:\data\Maize_F12_21_003_rgb.png"
    shape = _draw_shape(view, "polygon")

    assert _new_shape_with_popup(view) == "maize"
    assert shape.label == "maize"


def test_plant_default_overrides_previous_label(view):
    view.label_dialog.add_label_history("weed")
    view.label_dialog.edit.setText("weed")
    view.filename = "/data/SugarBeet_north_7_120_rgb.png"
    _draw_shape(view, "polygon")

    assert _new_shape_with_popup(view) == "sugarbeet"


def test_user_can_still_type_a_different_label(view):
    view.filename = "/data/Maize_F12_21_003_rgb.png"
    shape = _draw_shape(view, "polygon")

    _new_shape_with_popup(view, typed_label="weed")
    assert shape.label == "weed"


def test_auto_use_last_label_uses_plant(view):
    view._config["auto_use_last_label"] = True
    view.label_dialog.add_label_history("weed")
    view.filename = "/data/Soy_F1_14_002_rgb.png"
    shape = _draw_shape(view, "polygon")

    with patch.object(view.label_dialog, "pop_up") as pop_up, patch.object(
        view, "set_dirty"
    ):
        view.new_shape()
    pop_up.assert_not_called()
    assert shape.label == "soy"


def _make_image(folder, name):
    image = QtGui.QImage(32, 32, QtGui.QImage.Format.Format_RGB32)
    image.fill(QtGui.QColor("green"))
    path = folder / name
    assert image.save(str(path))
    return str(path)


def _unique_labels(view):
    return {
        view.unique_label_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole)
        for i in range(view.unique_label_list.count())
    }


def _dialog_labels(view):
    lst = view.label_dialog.label_list
    return {lst.item(i).text() for i in range(lst.count())}


def test_each_new_plant_in_folder_adds_its_own_label(view, tmp_path):
    maize = _make_image(tmp_path, "Maize_F12_21_003_rgb.png")
    sunflower = _make_image(tmp_path, "Sunflower_F12_21_004_rgb.png")
    maize2 = _make_image(tmp_path, "Maize_F12_28_005_rgb.png")

    assert view.load_file(maize) is not False
    assert {"maize"} <= _unique_labels(view)
    assert "sunflower" not in _unique_labels(view)
    assert "maize" in _dialog_labels(view)

    assert view.load_file(sunflower) is not False
    assert {"maize", "sunflower"} <= _unique_labels(view)
    assert {"maize", "sunflower"} <= _dialog_labels(view)

    # Same plant again: no duplicate label.
    assert view.load_file(maize2) is not False
    names = [
        view.unique_label_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole)
        for i in range(view.unique_label_list.count())
    ]
    assert names.count("maize") == 1


def test_sumniki_in_filename_become_plain_letters(view, tmp_path):
    image = _make_image(tmp_path, "Čičerika_F12_21_003_rgb.png")

    assert view.load_file(image) is not False
    assert "cicerika" in _unique_labels(view)
    shape = _draw_shape(view, "polygon")
    assert _new_shape_with_popup(view) == "cicerika"
    assert shape.label == "cicerika"


def test_polygon_default_follows_current_image_plant(view, tmp_path):
    maize = _make_image(tmp_path, "Maize_F12_21_003_rgb.png")
    sunflower = _make_image(tmp_path, "Sunflower_F12_21_004_rgb.png")

    view.load_file(maize)
    first = _draw_shape(view, "polygon")
    _new_shape_with_popup(view)
    assert first.label == "maize"

    # Leftover selection of the previous plant must not carry over.
    view.unique_label_list.find_items_by_label("maize")[0].setSelected(True)
    view.load_file(sunflower)
    second = _draw_shape(view, "polygon")
    assert _new_shape_with_popup(view) == "sunflower"
    assert second.label == "sunflower"


def test_non_matching_filename_keeps_previous_behaviour(view):
    view.filename = "/data/random_image.png"
    _draw_shape(view, "polygon")

    assert _new_shape_with_popup(view) is None
