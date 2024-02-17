"""Helpers for tmux options."""
import logging
import re
import shlex
import typing as t
import warnings

from libtmux._internal.constants import TmuxArray
from libtmux.common import CmdMixin
from libtmux.constants import (
    DEFAULT_OPTION_SCOPE,
    OPTION_SCOPE_FLAG_MAP,
    OptionScope,
    _DefaultOptionScope,
)

from . import exc

if t.TYPE_CHECKING:
    from typing_extensions import Self

OptionDict = t.Dict[str, t.Any]

logger = logging.getLogger(__name__)


def handle_option_error(error: str) -> t.Type[exc.OptionError]:
    """Raise exception if error in option command found.

    In tmux 3.0, show-option and show-window-option return invalid option instead of
    unknown option. See https://github.com/tmux/tmux/blob/3.0/cmd-show-options.c.

    In tmux >2.4, there are 3 different types of option errors:

    - unknown option
    - invalid option
    - ambiguous option

    In tmux <2.4, unknown option was the only option.

    All errors raised will have the base error of :exc:`exc.OptionError`. So to
    catch any option error, use ``except exc.OptionError``.

    Parameters
    ----------
    error : str
        Error response from subprocess call.

    Raises
    ------
    :exc:`exc.OptionError`, :exc:`exc.UnknownOption`, :exc:`exc.InvalidOption`,
    :exc:`exc.AmbiguousOption`
    """
    if "unknown option" in error:
        raise exc.UnknownOption(error)
    elif "invalid option" in error:
        raise exc.InvalidOption(error)
    elif "ambiguous option" in error:
        raise exc.AmbiguousOption(error)
    else:
        raise exc.OptionError(error)  # Raise generic option error


class OptionMixin(CmdMixin):
    """Mixin for managing tmux options based on scope."""

    default_option_scope: t.Optional[OptionScope]

    def __init__(self, default_option_scope: t.Optional[OptionScope]) -> None:
        """When not a user (custom) option, scope can be implied."""
        self.default_option_scope = default_option_scope

    def set_option(
        self,
        option: str,
        value: t.Union[int, str],
        _format: t.Optional[bool] = None,
        unset: t.Optional[bool] = None,
        unset_panes: t.Optional[bool] = None,
        prevent_overwrite: t.Optional[bool] = None,
        ignore_errors: t.Optional[bool] = None,
        append: t.Optional[bool] = None,
        g: t.Optional[bool] = None,
        _global: t.Optional[bool] = None,
        scope: t.Optional[
            t.Union[OptionScope, _DefaultOptionScope]
        ] = DEFAULT_OPTION_SCOPE,
    ) -> "Self":
        """Set option for tmux target.

        Wraps ``$ tmux set-option <option> <value>``.

        Parameters
        ----------
        option : str
            option to set, e.g. 'aggressive-resize'
        value : str
            option value. True/False will turn in 'on' and 'off',
            also accepts string of 'on' or 'off' directly.

        .. deprecated:: 0.28

           Deprecated by ``g`` for global, use `_global`` instead.

        Raises
        ------
        :exc:`exc.OptionError`, :exc:`exc.UnknownOption`,
        :exc:`exc.InvalidOption`, :exc:`exc.AmbiguousOption`
        """
        if scope is DEFAULT_OPTION_SCOPE:
            scope = self.default_option_scope

        flags: t.List[str] = []
        if isinstance(value, bool) and value:
            value = "on"
        elif isinstance(value, bool) and not value:
            value = "off"

        if unset is not None and unset:
            assert isinstance(unset, bool)
            flags.append("-u")

        if unset_panes is not None and unset_panes:
            assert isinstance(unset_panes, bool)
            flags.append("-U")

        if _format is not None and _format:
            assert isinstance(_format, bool)
            flags.append("-F")

        if prevent_overwrite is not None and prevent_overwrite:
            assert isinstance(prevent_overwrite, bool)
            flags.append("-o")

        if ignore_errors is not None and ignore_errors:
            assert isinstance(ignore_errors, bool)
            flags.append("-q")

        if append is not None and append:
            assert isinstance(append, bool)
            flags.append("-a")

        if g is not None:
            warnings.warn("g argument is deprecated in favor of _global", stacklevel=2)
            _global = g

        if _global is not None and _global:
            assert isinstance(_global, bool)
            flags.append("-g")

        if scope is not None and not isinstance(scope, _DefaultOptionScope):
            assert scope in OPTION_SCOPE_FLAG_MAP
            flags.append(
                OPTION_SCOPE_FLAG_MAP[scope],
            )

        cmd = self.cmd(
            "set-option",
            *flags,
            option,
            value,
        )

        if isinstance(cmd.stderr, list) and len(cmd.stderr):
            handle_option_error(cmd.stderr[0])

        return self

    def unset_option(
        self,
        option: str,
        unset_panes: t.Optional[bool] = None,
        _global: t.Optional[bool] = None,
        ignore_errors: t.Optional[bool] = None,
        scope: t.Optional[
            t.Union[OptionScope, _DefaultOptionScope]
        ] = DEFAULT_OPTION_SCOPE,
    ) -> "Self":
        """Unset option for tmux target.

        Wraps ``$ tmux set-option -u <option>`` / ``$ tmux set-option -U <option>``

        Parameters
        ----------
        option : str
            option to unset, e.g. 'aggressive-resize'

        Raises
        ------
        :exc:`exc.OptionError`, :exc:`exc.UnknownOption`,
        :exc:`exc.InvalidOption`, :exc:`exc.AmbiguousOption`
        """
        if scope is DEFAULT_OPTION_SCOPE:
            scope = self.default_option_scope

        flags: t.List[str] = []

        if unset_panes is not None and unset_panes:
            assert isinstance(unset_panes, bool)
            flags.append("-U")
        else:
            flags.append("-u")

        if ignore_errors is not None and ignore_errors:
            assert isinstance(ignore_errors, bool)
            flags.append("-q")

        if _global is not None and _global:
            assert isinstance(_global, bool)
            flags.append("-g")

        if scope is not None and not isinstance(scope, _DefaultOptionScope):
            assert scope in OPTION_SCOPE_FLAG_MAP
            flags.append(
                OPTION_SCOPE_FLAG_MAP[scope],
            )

        cmd = self.cmd(
            "set-option",
            *flags,
            option,
        )

        if isinstance(cmd.stderr, list) and len(cmd.stderr):
            handle_option_error(cmd.stderr[0])

        return self

    @t.overload
    def show_options(
        self,
        g: t.Optional[bool],
        _global: t.Optional[bool],
        scope: t.Optional[t.Union[OptionScope, _DefaultOptionScope]],
        ignore_errors: t.Optional[bool],
        include_hooks: t.Optional[bool],
        include_inherited: t.Optional[bool],
        values_only: t.Literal[True],
    ) -> t.List[str]:
        ...

    @t.overload
    def show_options(
        self,
        g: t.Optional[bool],
        _global: t.Optional[bool],
        scope: t.Optional[t.Union[OptionScope, _DefaultOptionScope]],
        ignore_errors: t.Optional[bool],
        include_hooks: t.Optional[bool],
        include_inherited: t.Optional[bool],
        values_only: t.Literal[None] = None,
    ) -> "OptionDict":
        ...

    @t.overload
    def show_options(
        self,
        g: t.Optional[bool] = None,
        _global: t.Optional[bool] = None,
        scope: t.Optional[
            t.Union[OptionScope, _DefaultOptionScope]
        ] = DEFAULT_OPTION_SCOPE,
        ignore_errors: t.Optional[bool] = None,
        include_hooks: t.Optional[bool] = None,
        include_inherited: t.Optional[bool] = None,
        values_only: t.Literal[False] = False,
    ) -> "OptionDict":
        ...

    def show_options(
        self,
        g: t.Optional[bool] = False,
        _global: t.Optional[bool] = False,
        scope: t.Optional[
            t.Union[OptionScope, _DefaultOptionScope]
        ] = DEFAULT_OPTION_SCOPE,
        ignore_errors: t.Optional[bool] = None,
        include_hooks: t.Optional[bool] = None,
        include_inherited: t.Optional[bool] = None,
        values_only: t.Optional[bool] = False,
    ) -> t.Union["OptionDict", t.List[str]]:
        """Return a dict of options for the target.

        Parameters
        ----------
        g : str, optional
            Pass ``-g`` flag for global variable, default False.
        """
        if scope is DEFAULT_OPTION_SCOPE:
            scope = self.default_option_scope

        flags: t.Tuple[str, ...] = ()

        if g:
            warnings.warn("g argument is deprecated in favor of _global", stacklevel=2)
            flags += ("-g",)
        elif _global:
            flags += ("-g",)

        if scope is not None and not isinstance(scope, _DefaultOptionScope):
            assert scope in OPTION_SCOPE_FLAG_MAP
            flags += (OPTION_SCOPE_FLAG_MAP[scope],)

        if include_inherited is not None and include_inherited:
            flags += ("-A",)

        if include_hooks is not None and include_hooks:
            flags += ("-H",)

        if values_only is not None and values_only:
            flags += ("-v",)

        if ignore_errors is not None and ignore_errors:
            assert isinstance(ignore_errors, bool)
            flags += ("-q",)

        cmd = self.cmd("show-options", *flags)
        output = cmd.stdout
        options: "OptionDict" = {}
        for item in output:
            try:
                key, val = shlex.split(item)
                matchgroup = re.match(
                    r"(?P<hook>[\w-]+)(\[(?P<index>\d+)\])?",
                    key,
                )
                if matchgroup is not None:
                    match = matchgroup.groupdict()
                    if match.get("hook") and match.get("index"):
                        key = match["hook"]
                        index = int(match["index"])
                        if key == "terminal-features":
                            term, features = val.split(":", maxsplit=1)
                            if options.get(key) is None:
                                options[key] = {}
                            options[key][term] = features.split(":")
                        else:
                            if options.get(key) is None:
                                options[key] = TmuxArray()
                            options[key][index] = val
                        continue
            except ValueError:  # empty option (default)
                key, val = item, None
            except Exception:
                logger.warning(f"Error extracting option: {item}")
                key, val = item, None
            assert isinstance(key, str)
            assert isinstance(val, str) or val is None

            if isinstance(val, str) and val.isdigit():
                options[key] = int(val)
            else:
                options[key] = val

        return options

    def show_option(
        self,
        option: str,
        _global: bool = False,
        g: bool = False,
        scope: t.Optional[
            t.Union[OptionScope, _DefaultOptionScope]
        ] = DEFAULT_OPTION_SCOPE,
        ignore_errors: t.Optional[bool] = None,
        include_hooks: t.Optional[bool] = None,
        include_inherited: t.Optional[bool] = None,
    ) -> t.Optional[t.Union[str, int]]:
        """Return option value for the target.

        todo: test and return True/False for on/off string

        Parameters
        ----------
        option : str
        g : bool, optional
            Pass ``-g`` flag, global. Default False.

        Raises
        ------
        :exc:`exc.OptionError`, :exc:`exc.UnknownOption`,
        :exc:`exc.InvalidOption`, :exc:`exc.AmbiguousOption`
        """
        if scope is DEFAULT_OPTION_SCOPE:
            scope = self.default_option_scope

        flags: t.Tuple[t.Union[str, int], ...] = ()

        if g:
            warnings.warn("g argument is deprecated in favor of _global", stacklevel=2)
            flags += ("-g",)
        elif _global:
            flags += ("-g",)

        if scope is not None and not isinstance(scope, _DefaultOptionScope):
            assert scope in OPTION_SCOPE_FLAG_MAP
            flags += (OPTION_SCOPE_FLAG_MAP[scope],)

        if ignore_errors is not None and ignore_errors:
            flags += ("-q",)

        if include_inherited is not None and include_inherited:
            flags += ("-A",)

        if include_hooks is not None and include_hooks:
            flags += ("-H",)

        flags += (option,)

        cmd = self.cmd("show-options", *flags)

        if len(cmd.stderr):
            handle_option_error(cmd.stderr[0])

        options_output = cmd.stdout

        if not len(options_output):
            return None

        value_raw = next(shlex.split(item) for item in options_output)

        value: t.Union[str, int] = (
            int(value_raw[1]) if value_raw[1].isdigit() else value_raw[1]
        )

        return value
