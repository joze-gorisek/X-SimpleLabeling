import os
import re
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtWidgets
from PyQt6.QtCore import QTranslator

from anylabeling import config as anylabeling_config
from anylabeling.resources import resources  # noqa: F401
from anylabeling.views.labeling import label_widget as label_widget_module
from anylabeling.views.labeling.pointcloud.selection import validate_polygon
from anylabeling.views.labeling.label_widget import (
    SUPPORTED_LANGUAGES,
    LabelingWidget,
)

SL_CATALOG = "anylabeling/resources/translations/sl_SI.ts"
PLACEHOLDER = re.compile(r"%[sd]|%\.\d+f|%\d|\{[^{}]*\}")


def _load_translator(language):
    translator = QTranslator()
    assert translator.load(f":/languages/translations/{language}.qm")
    return translator


def _fake_widget(language="en_US"):
    return SimpleNamespace(
        _config={"language": language},
        language_button=Mock(),
        tr=lambda text: text,
        parent=SimpleNamespace(parent=SimpleNamespace(close=Mock())),
    )


@pytest.mark.parametrize("language", sorted(SUPPORTED_LANGUAGES))
def test_supported_languages_have_compiled_catalogs(language):
    _load_translator(language)


@pytest.mark.parametrize(
    ("context", "source", "expected"),
    [
        ("LabelingWidget", "File", "Datoteka"),
        # self.tr() in a free function resolves against the runtime class.
        ("LabelingWidget", "Cropped Image Options", "Možnosti obrezanih slik"),
        # QT_TRANSLATE_NOOP with a context constant.
        (
            "SettingsDialog",
            "Wheel Navigation Mode",
            "Način navigacije s kolescem",
        ),
        # Reached through self.tr(variable).
        ("ChatbotDialog", "Chatbot", "Klepetalnik"),
        ("UltralyticsDialog", "Epochs:", "Epohe:"),
        # Qt's own standard button text.
        ("QPlatformTheme", "Cancel", "Prekliči"),
    ],
)
def test_slovenian_catalog_covers_each_lookup_route(context, source, expected):
    assert _load_translator("sl_SI").translate(context, source) == expected


def test_slovenian_catalog_is_complete_and_keeps_placeholders():
    root = ET.parse(SL_CATALOG).getroot()
    assert root.get("language") == "sl_SI"
    messages = root.findall("./context/message")
    assert messages
    for message in messages:
        source = message.find("source").text
        translation = message.find("translation")
        assert translation.get("type") is None, source
        assert translation.text, source
        assert sorted(PLACEHOLDER.findall(source)) == sorted(
            PLACEHOLDER.findall(translation.text)
        ), source
        assert source.count("\n") == translation.text.count("\n"), source


def test_set_language_saves_before_closing():
    widget = _fake_widget()
    calls = []
    widget.parent.parent.close.side_effect = lambda: calls.append("close")
    with (
        patch.object(
            label_widget_module,
            "save_config",
            side_effect=lambda config: calls.append(config["language"]),
        ),
        patch.object(label_widget_module, "QMessageBox"),
    ):
        LabelingWidget.set_language(widget, "sl_SI")

    # Saving first means cancelling the close cannot lose the choice.
    assert calls == ["sl_SI", "close"]
    widget.language_button.setText.assert_called_once_with("Slovenščina")


def test_set_language_ignores_current_language():
    widget = _fake_widget("sl_SI")
    with patch.object(label_widget_module, "save_config") as save_config:
        LabelingWidget.set_language(widget, "sl_SI")

    save_config.assert_not_called()
    widget.parent.parent.close.assert_not_called()


def test_saved_language_is_the_default_on_next_launch(tmp_path):
    previous_work_directory = anylabeling_config._work_directory
    anylabeling_config.set_work_directory(str(tmp_path))
    config_file = str(tmp_path / ".xanylabelingrc")
    try:
        first_launch = anylabeling_config.get_config(config_file)
        assert first_launch["language"] == "en_US"

        first_launch["language"] = "sl_SI"
        anylabeling_config.save_config(first_launch)

        assert (
            anylabeling_config.get_config(config_file)["language"] == "sl_SI"
        )
    finally:
        anylabeling_config._work_directory = previous_work_directory


def test_placeholder_formatting_works_for_every_slovenian_message():
    root = ET.parse(SL_CATALOG).getroot()
    positional = re.compile(r"\{(\d+)[^{}]*\}")
    for message in root.findall("./context/message"):
        text = message.find("translation").text
        indices = [int(index) for index in positional.findall(text)]
        if not indices:
            continue
        # Width/precision specs need numbers; plain fields accept them too.
        text.format(*[1.0] * (max(indices) + 1))


def test_error_messages_are_translated_at_runtime():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    translator = _load_translator("sl_SI")
    app.installTranslator(translator)
    try:
        with pytest.raises(ValueError, match="vsaj tri oglišča"):
            validate_polygon([(0.0, 0.0)])
    finally:
        app.removeTranslator(translator)

    with pytest.raises(ValueError, match="at least three vertices"):
        validate_polygon([(0.0, 0.0)])


def test_every_catalog_entry_is_served_by_the_compiled_translator():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    translator = _load_translator("sl_SI")
    app.installTranslator(translator)
    try:
        root = ET.parse(SL_CATALOG).getroot()
        checked = 0
        for context in root.findall("context"):
            name = context.find("name").text
            for message in context.findall("message"):
                source = message.find("source").text
                expected = message.find("translation").text
                # Same route as tr(), including non-ASCII sources.
                assert app.translate(name, source) == expected, source
                checked += 1
    finally:
        app.removeTranslator(translator)
    assert checked > 2900
