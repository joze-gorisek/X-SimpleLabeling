"""Qt's own UI strings that its bundled catalogs leave untranslated.

Never imported at runtime. It only exists so ``pylupdate6`` keeps these
messages in the application catalogs, whose translator also serves Qt's
standard buttons and text-field context menus.
"""

from PyQt6.QtCore import QT_TRANSLATE_NOOP

QT_BUILTIN_STRINGS = (
    QT_TRANSLATE_NOOP("QPlatformTheme", "OK"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Save"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Save All"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Open"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "&Yes"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Yes to &All"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "&No"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "N&o to All"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Abort"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Retry"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Ignore"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Close"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Cancel"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Discard"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Help"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Apply"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Reset"),
    QT_TRANSLATE_NOOP("QPlatformTheme", "Restore Defaults"),
    QT_TRANSLATE_NOOP("QWidgetTextControl", "&Undo"),
    QT_TRANSLATE_NOOP("QWidgetTextControl", "&Redo"),
    QT_TRANSLATE_NOOP("QWidgetTextControl", "Cu&t"),
    QT_TRANSLATE_NOOP("QWidgetTextControl", "&Copy"),
    QT_TRANSLATE_NOOP("QWidgetTextControl", "Copy &Link Location"),
    QT_TRANSLATE_NOOP("QWidgetTextControl", "&Paste"),
    QT_TRANSLATE_NOOP("QWidgetTextControl", "Delete"),
    QT_TRANSLATE_NOOP("QWidgetTextControl", "Select All"),
    QT_TRANSLATE_NOOP("QDockWidget", "Closes the dock widget"),
    QT_TRANSLATE_NOOP(
        "QDockWidget", "Undocks and re-attaches the dock widget"
    ),
)
