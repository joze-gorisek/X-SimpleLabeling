"""X-SimpleLabeling SAM controls: TinyObj on by default, AMD/AMG hidden,
Point +/- labels and colors."""

import copy
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtWidgets  # noqa: E402

import anylabeling.resources.resources  # noqa: E402,F401
from anylabeling import config as app_config  # noqa: E402
from anylabeling.views.labeling.settings.schema import (  # noqa: E402
    load_template_config,
)
from anylabeling.views.labeling.widgets.auto_labeling.auto_labeling import (  # noqa: E402
    SAM_ADD_COLOR,
    SAM_REMOVE_COLOR,
)
from anylabeling.views.mainwindow import MainWindow  # noqa: E402

SAM2_WIDGETS = [
    "button_add_point",
    "button_remove_point",
    "button_add_rect",
    "button_clear",
    "button_finish_object",
    "button_auto_decode",
    "button_cropping",
    "button_segment_everything",
]


class FakeSam:
    def __init__(self):
        self.cropping_mode = False

    @staticmethod
    def get_required_widgets():
        return SAM2_WIDGETS

    def set_cropping_mode(self, enabled):
        self.cropping_mode = enabled


@pytest.fixture
def widget(tmp_path, monkeypatch):
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
    window.show()
    app.processEvents()
    yield window.labeling_widget.view.auto_labeling_widget
    window.labeling_widget.view.dirty = False
    window.close()
    window.deleteLater()
    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)


def _load_fake_sam(widget):
    model = FakeSam()
    config = {"type": "segment_anything_2", "name": "fake", "model": model}
    widget.model_manager.loaded_model_config = config
    widget.model_manager.model_loaded.emit(config)
    QtWidgets.QApplication.processEvents()
    return model


def test_tinyobj_is_on_by_default_and_applied_to_loaded_model(widget):
    assert widget.button_cropping.isChecked()
    model = _load_fake_sam(widget)
    assert model.cropping_mode is True


def test_tinyobj_can_still_be_turned_off(widget):
    model = _load_fake_sam(widget)
    widget.button_cropping.click()
    assert not widget.button_cropping.isChecked()
    assert model.cropping_mode is False


def test_amd_and_amg_are_hidden(widget):
    widget.show()
    _load_fake_sam(widget)
    assert widget.button_add_point.isVisible()
    assert widget.button_cropping.isVisible()
    assert not widget.button_auto_decode.isVisible()
    assert not widget.button_segment_everything.isVisible()


def test_point_buttons_show_plus_and_minus(widget):
    assert widget.button_add_point.text().startswith("Point + (")
    assert widget.button_remove_point.text().startswith("Point - (")
    # Re-applying shortcuts must not stack signs.
    widget.update_shortcut_button_texts()
    assert widget.button_add_point.text().count("+") == 1
    assert widget.button_remove_point.text().count(" - ") == 1


def test_button_colors(widget):
    assert SAM_ADD_COLOR in widget.button_add_point.styleSheet()
    assert SAM_REMOVE_COLOR in widget.button_remove_point.styleSheet()
    assert SAM_ADD_COLOR in widget.button_finish_object.styleSheet()
    assert SAM_REMOVE_COLOR in widget.button_clear.styleSheet()
