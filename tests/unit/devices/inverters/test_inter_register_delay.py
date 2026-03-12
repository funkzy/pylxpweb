"""Tests for 3.5s inter-register delay in paired schedule writes."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from pylxpweb import LuxpowerClient
from pylxpweb.devices.inverters.hybrid import HybridInverter


@pytest.fixture
def mock_client() -> LuxpowerClient:
    """Create a mock client for testing."""
    client = Mock(spec=LuxpowerClient)
    client.api = Mock()
    client.api.control = Mock()
    return client


@pytest.fixture
def inverter(mock_client: LuxpowerClient) -> HybridInverter:
    """Create a HybridInverter with mock client and successful writes."""
    inv = HybridInverter(
        client=mock_client, serial_number="1234567890", model="FlexBOSS21"
    )
    mock_write_response = Mock()
    mock_write_response.success = True
    mock_client.api.control.write_parameters = AsyncMock(
        return_value=mock_write_response
    )
    return inv


class TestInterRegisterDelay:
    """Test 3.5s delay between paired schedule register writes."""

    @pytest.mark.asyncio
    async def test_paired_write_sleeps_between_registers(
        self, inverter: HybridInverter, mock_client: LuxpowerClient
    ) -> None:
        """set_ac_charge_schedule sleeps 3.5s between start and end writes."""
        with patch(
            "pylxpweb.devices.inverters.hybrid.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            result = await inverter.set_ac_charge_schedule(0, 1, 30, 5, 0)

        assert result is True
        mock_sleep.assert_called_once_with(3.5)
        assert mock_client.api.control.write_parameters.call_count == 2

    @pytest.mark.asyncio
    async def test_forced_charge_paired_write_also_sleeps(
        self, inverter: HybridInverter
    ) -> None:
        """Forced charge paired write also has the delay."""
        with patch(
            "pylxpweb.devices.inverters.hybrid.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await inverter.set_forced_charge_schedule(0, 22, 0, 6, 0)

        mock_sleep.assert_called_once_with(3.5)

    @pytest.mark.asyncio
    async def test_forced_discharge_paired_write_also_sleeps(
        self, inverter: HybridInverter
    ) -> None:
        """Forced discharge paired write also has the delay."""
        with patch(
            "pylxpweb.devices.inverters.hybrid.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await inverter.set_forced_discharge_schedule(0, 16, 0, 21, 0)

        mock_sleep.assert_called_once_with(3.5)
