"""Constant variables for libtmux."""
import enum
import typing as t


class ResizeAdjustmentDirection(enum.Enum):
    """Used for *adjustment* in ``resize_window``, ``resize_pane``."""

    Up = "UP"
    Down = "DOWN"
    Left = "LEFT"
    Right = "RIGHT"


RESIZE_ADJUSTMENT_DIRECTION_FLAG_MAP: t.Dict[ResizeAdjustmentDirection, str] = {
    ResizeAdjustmentDirection.Up: "-U",
    ResizeAdjustmentDirection.Down: "-D",
    ResizeAdjustmentDirection.Left: "-L",
    ResizeAdjustmentDirection.Right: "-R",
}


class _DefaultOptionScope:
    # Sentinel value for default scope
    ...


DEFAULT_OPTION_SCOPE: _DefaultOptionScope = _DefaultOptionScope()


class OptionScope(enum.Enum):
    """Scope used with ``set-option`` and ``show-option(s)`` commands."""

    Server = "SERVER"
    Session = "SESSION"
    Window = "WINDOW"
    Pane = "PANE"


OPTION_SCOPE_FLAG_MAP: t.Dict[OptionScope, str] = {
    OptionScope.Server: "-s",
    OptionScope.Session: "",
    OptionScope.Window: "-w",
    OptionScope.Pane: "-p",
}
