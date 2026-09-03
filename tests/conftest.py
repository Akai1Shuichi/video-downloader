"""Shared pytest safeguards and opt-in network test support."""

import socket

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-network",
        action="store_true",
        default=False,
        help="run tests marked 'network' (live URLs must be supplied via environment variables)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-network"):
        return

    skip_network = pytest.mark.skip(reason="network test; pass --run-network to opt in")
    for item in items:
        if item.get_closest_marker("network") is not None:
            item.add_marker(skip_network)


@pytest.fixture(autouse=True)
def prevent_unmarked_network_access(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Make accidental Internet access fail immediately in the offline test suite."""
    if request.node.get_closest_marker("network") is not None:
        return

    def blocked_connect(*_args: object, **_kwargs: object) -> None:
        message = "Network access is forbidden in offline tests; add @pytest.mark.network"
        raise AssertionError(message)

    monkeypatch.setattr(socket, "create_connection", blocked_connect)
    monkeypatch.setattr(socket.socket, "connect", blocked_connect)
