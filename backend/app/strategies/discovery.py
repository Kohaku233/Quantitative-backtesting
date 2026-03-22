import importlib.util
import inspect
from collections import defaultdict
from pathlib import Path
from types import ModuleType

from backend.app.models.strategies import DiscoveryWarning, StrategyMetadata
from backend.app.strategies.base import BaseStrategyPlugin


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"strategy_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module for {path.name}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_plugin_class(plugin_class: type[BaseStrategyPlugin]) -> None:
    required_attributes = (
        "id",
        "name",
        "description",
        "supported_timeframes",
        "required_lookback_bars",
        "parameter_schema",
    )

    for attribute in required_attributes:
        if not hasattr(plugin_class, attribute):
            raise TypeError(f"missing required attribute '{attribute}'")

    if not isinstance(plugin_class.supported_timeframes, tuple):
        raise TypeError("supported_timeframes must be a tuple[str, ...]")
    if not isinstance(plugin_class.parameter_schema, list):
        raise TypeError("parameter_schema must be a list[dict[str, Any]]")

    expected_methods = {
        "validate_params": ("cls", "params"),
        "compute_indicators": ("cls", "df", "params"),
        "generate_signals": ("cls", "df", "indicators", "params"),
    }

    for method_name, expected_parameters in expected_methods.items():
        descriptor = inspect.getattr_static(plugin_class, method_name, None)
        if not isinstance(descriptor, classmethod):
            raise TypeError(f"{method_name} must be declared as a @classmethod")

        actual_parameters = tuple(inspect.signature(descriptor.__func__).parameters)
        if actual_parameters != expected_parameters:
            raise TypeError(
                f"{method_name} must have signature ({', '.join(expected_parameters)})"
            )


def discover_strategies(
    directory: Path,
) -> tuple[list[StrategyMetadata], list[DiscoveryWarning]]:
    warnings: list[DiscoveryWarning] = []
    discovered: list[tuple[Path, StrategyMetadata]] = []

    for plugin_path in sorted(directory.glob("*.py")):
        if plugin_path.name == "__init__.py":
            continue

        try:
            module = _load_module(plugin_path)
        except Exception as exc:  # noqa: BLE001
            warnings.append(
                DiscoveryWarning(
                    file=plugin_path.name,
                    reason=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        plugin_classes = [
            member
            for _, member in inspect.getmembers(module, inspect.isclass)
            if issubclass(member, BaseStrategyPlugin) and member is not BaseStrategyPlugin
        ]

        if not plugin_classes:
            warnings.append(
                DiscoveryWarning(
                    file=plugin_path.name,
                    reason="TypeError: no BaseStrategyPlugin subclass found",
                )
            )
            continue

        for plugin_class in plugin_classes:
            try:
                if inspect.isabstract(plugin_class):
                    raise TypeError("plugin class must implement all abstract strategy methods")
                _validate_plugin_class(plugin_class)
                discovered.append((plugin_path, plugin_class.to_metadata()))
            except Exception as exc:  # noqa: BLE001
                warnings.append(
                    DiscoveryWarning(
                        file=plugin_path.name,
                        reason=f"{type(exc).__name__}: {exc}",
                    )
                )

    grouped_by_id: dict[str, list[tuple[Path, StrategyMetadata]]] = defaultdict(list)
    for plugin_path, metadata in discovered:
        grouped_by_id[metadata.id].append((plugin_path, metadata))

    strategies: list[StrategyMetadata] = []
    for strategy_id, candidates in grouped_by_id.items():
        if len(candidates) > 1:
            for plugin_path, _ in candidates:
                warnings.append(
                    DiscoveryWarning(
                        file=plugin_path.name,
                        reason=f"duplicate id '{strategy_id}'",
                    )
                )
            continue

        strategies.append(candidates[0][1])

    strategies.sort(key=lambda strategy: strategy.id)
    return strategies, warnings
