"""The app is focused on polygon instance segmentation: only that UI is exposed."""

import copy
import os
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6 import QtCore, QtWidgets  # noqa: E402

import anylabeling.resources.resources  # noqa: E402,F401
from anylabeling import config as app_config  # noqa: E402
from anylabeling.views.labeling.settings.schema import (  # noqa: E402
    load_template_config,
)
from anylabeling.views.labeling.settings.schema import (  # noqa: E402
    fields_for_page,
)
from anylabeling.views.labeling.widgets.auto_labeling.auto_labeling import (  # noqa: E402
    DEFAULT_MODEL_NAME,
)
from anylabeling.views.labeling.widgets.toolbar import (  # noqa: E402
    TOOL_BUTTON_SIZE,
)
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
    window.show()
    app.processEvents()
    yield window.labeling_widget.view
    window.labeling_widget.view.dirty = False
    window.close()
    app.removeEventFilter(window.labeling_widget.view)
    window.deleteLater()
    app.sendPostedEvents(None, QtCore.QEvent.Type.DeferredDelete)


def test_toolbar_has_only_the_essential_big_buttons(view):
    actions = view.actions
    tool_actions = [
        a
        for a in view.actions.tool
        if a is not None and not isinstance(a, QtWidgets.QWidgetAction)
    ]
    assert tool_actions == [
        actions.open_dir,
        actions.open_prev_image,
        actions.open_next_image,
        actions.create_mode,
        actions.edit_mode,
        actions.delete,
        actions.undo,
        actions.fit_window,
    ]
    buttons = view.tools.findChildren(QtWidgets.QToolButton)
    assert len(buttons) == 10
    for button in buttons:
        assert button.width() >= TOOL_BUTTON_SIZE
        assert button.height() >= TOOL_BUTTON_SIZE
    assert view.tools.height() >= TOOL_BUTTON_SIZE


@pytest.mark.parametrize(
    "name",
    [
        "create_rectangle_mode",
        "create_cuboid_mode",
        "create_rotation_mode",
        "create_quadrilateral_mode",
        "create_circle_mode",
        "create_line_mode",
        "create_point_mode",
        "create_line_strip_mode",
        "create_relation",
        "manage_relations",
        "open_chatbot",
        "open_vqa",
        "open_pointcloud",
        "toggle_auto_labeling_widget",
    ],
)
def test_removed_features_are_unreachable(view, name):
    # A QAction shortcut only fires once the action is attached to a widget.
    assert getattr(view.actions, name).associatedObjects() == []


@pytest.mark.parametrize(
    "name",
    [
        "create_mode",
        "create_brush_polygon_mode",
        "create_magic_wand_mode",
        "edit_mode",
        "edit_brush_mode",
        "save",
        "delete_file",
        "jump_next_images",
        "jump_prev_images",
        "select_toggle_shapes",
        "fit_width",
        "show_masks",
        "show_image_tags",
        "run_all_images",
    ],
)
def test_actions_off_the_toolbar_keep_a_menu_and_shortcut(view, name):
    assert getattr(view.actions, name).associatedObjects()


def test_display_modes_moved_to_view_menu(view):
    view_actions = view.menus.view.actions()
    for display_action in view.display_mode_group.actions():
        assert display_action in view_actions


def test_menu_bar_and_exports_are_segmentation_only(view):
    menu_bar = view.parent.parent.menuBar()
    assert view.menus.tool.menuAction() in menu_bar.actions()
    assert not hasattr(view.menus, "workflow")
    assert [a for a in view.menus.export.actions() if not a.isSeparator()] == [
        view.actions.export_yolo_seg_annotation,
        view.actions.export_voc_seg_annotation,
        view.actions.export_coco_seg_annotation,
        view.actions.export_mask_annotation,
    ]


def test_digit_shortcut_ignores_non_polygon_modes(view):
    view.drawing_digit_shortcuts = {
        1: {"label": "box", "mode": "rectangle"},
        2: {"label": "plant", "mode": "polygon"},
    }
    with patch.object(view, "toggle_draw_mode") as toggle_draw_mode:
        view.create_digit_mode(1)
        toggle_draw_mode.assert_not_called()
        view.create_digit_mode(2)
        toggle_draw_mode.assert_called_once_with(
            edit=False, create_mode="polygon"
        )


def test_hidden_shortcuts_are_not_listed_in_settings(view):
    keys = {field.key for field in fields_for_page("Shortcuts", "Shape")}
    assert "shortcuts.create_polygon" in keys
    assert "shortcuts.create_rectangle" not in keys


def test_auto_labeling_bar_starts_visible_with_auto_run_enabled(view):
    assert view.auto_labeling_widget.isVisible()
    assert view.actions.run_all_images.isEnabled()


def test_default_model_is_sam2_small_and_selection_loads_it(view):
    widget = view.auto_labeling_widget
    # Swap the real loader out so the test never downloads the model.
    widget.new_model_selected.disconnect(widget.model_manager.load_model)
    emitted = []
    widget.new_model_selected.connect(emitted.append)
    widget.load_default_model()
    assert emitted == [":/sam2_hiera_small.yaml"]
    assert (
        widget.model_selection_button.text() == "Segment Anything 2.1 (Small)"
    )
    assert (
        widget.model_info[DEFAULT_MODEL_NAME]["config_path"]
        == ":/sam2_hiera_small.yaml"
    )


def test_model_dropdown_only_offers_instance_segmentation(view):
    widget = view.auto_labeling_widget
    names = {
        name
        for models in widget.model_dropdown.models_data.values()
        for name in models
    }
    assert DEFAULT_MODEL_NAME in names
    assert "load_custom_model" in names
    assert not any("depth_anything" in name for name in names)
    assert not any("ppocr" in name for name in names)
    assert any("seg" in name for name in names)


def test_saved_entries_of_excluded_models_do_not_come_back(view, tmp_path):
    widget = view.auto_labeling_widget
    with patch(
        "anylabeling.views.labeling.widgets.auto_labeling.auto_labeling.load_json",
        return_value={
            "models_data": {
                "Custom": {},
                "Meta": {
                    "not_a_segmentation_model": {
                        "selected": False,
                        "favorite": False,
                        "display_name": "Stale",
                    }
                },
            }
        },
    ):
        models_data = widget.init_model_data()
    assert "not_a_segmentation_model" not in models_data["Meta"]


def test_output_selector_stays_hidden_and_polygon_is_forced(view):
    widget = view.auto_labeling_widget
    with patch.object(widget.model_manager, "set_output_mode") as set_mode:
        widget.on_output_modes_changed(
            {"rectangle": "Rectangle", "polygon": "Polygon"}, "rectangle"
        )
    set_mode.assert_called_once_with("polygon")
    assert widget.output_select_combobox.currentData() == "polygon"

    class FakeModel:
        @staticmethod
        def get_required_widgets():
            return [
                "output_label",
                "output_select_combobox",
                "button_add_point",
            ]

    widget.update_visible_widgets({"model": FakeModel()})
    assert widget.output_select_combobox.isHidden()
    assert widget.output_label.isHidden()
    assert not widget.button_add_point.isHidden()
