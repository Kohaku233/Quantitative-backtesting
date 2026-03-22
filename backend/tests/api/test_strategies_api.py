from backend.app.api import strategies as strategies_api
from backend.app.models.strategies import DiscoveryWarning, StrategyMetadata


def test_strategies_api_returns_schema_and_warnings(client, monkeypatch) -> None:
    monkeypatch.setattr(
        strategies_api,
        "discover_strategies",
        lambda _path: (
            [
                StrategyMetadata(
                    id="sma_cross",
                    name="SMA Cross",
                    description="Long/short moving-average crossover strategy.",
                    supported_timeframes=["15m", "1h", "4h", "1d"],
                    required_lookback_bars=200,
                    parameter_schema=[
                        {
                            "key": "fast_period",
                            "label": "Fast Period",
                            "type": "integer",
                            "default": 20,
                            "required": True,
                            "min": 1,
                            "max": 500,
                            "step": 1,
                            "help": "Short moving average period.",
                        }
                    ],
                )
            ],
            [
                DiscoveryWarning(
                    file="broken_plugin.py",
                    reason="ImportError: missing dependency",
                )
            ],
        ),
    )

    response = client.get("/api/strategies")

    assert response.status_code == 200
    assert response.json() == {
        "strategies": [
            {
                "id": "sma_cross",
                "name": "SMA Cross",
                "description": "Long/short moving-average crossover strategy.",
                "supported_timeframes": ["15m", "1h", "4h", "1d"],
                "required_lookback_bars": 200,
                "parameter_schema": [
                    {
                        "key": "fast_period",
                        "label": "Fast Period",
                        "type": "integer",
                        "default": 20,
                        "required": True,
                        "min": 1,
                        "max": 500,
                        "step": 1,
                        "help": "Short moving average period.",
                    }
                ],
            }
        ],
        "discovery_warnings": [
            {
                "file": "broken_plugin.py",
                "reason": "ImportError: missing dependency",
            }
        ],
    }
