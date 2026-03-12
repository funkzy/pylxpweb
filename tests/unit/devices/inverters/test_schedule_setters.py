"""Tests for individual start/end schedule setters (single register write)."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from pylxpweb import LuxpowerClient
from pylxpweb.constants import pack_time
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


class TestIndividualScheduleSetters:
    """Test individual start/end schedule setters (single register write)."""

    # ── AC charge ──

    @pytest.mark.asyncio
    async def test_ac_charge_start_period_0(
        self, inverter: HybridInverter, mock_client: LuxpowerClient
    ) -> None:
        """AC charge start period 0 writes register 68."""
        result = await inverter.set_ac_charge_schedule_start(0, 1, 30)

        assert result is True
        mock_client.api.control.write_parameters.assert_called_once_with(
            "1234567890", {68: pack_time(1, 30)}
        )

    @pytest.mark.asyncio
    async def test_ac_charge_end_period_0(
        self, inverter: HybridInverter, mock_client: LuxpowerClient
    ) -> None:
        """AC charge end period 0 writes register 69."""
        result = await inverter.set_ac_charge_schedule_end(0, 5, 0)

        assert result is True
        mock_client.api.control.write_parameters.assert_called_once_with(
            "1234567890", {69: pack_time(5, 0)}
        )

    @pytest.mark.asyncio
    async def test_ac_charge_start_period_2(
        self, inverter: HybridInverter, mock_client: LuxpowerClient
    ) -> None:
        """AC charge start period 2 writes register 72 (68 + 2*2)."""
        await inverter.set_ac_charge_schedule_start(2, 23, 45)

        mock_client.api.control.write_parameters.assert_called_once_with(
            "1234567890", {72: pack_time(23, 45)}
        )

    # ── Forced charge ──

    @pytest.mark.asyncio
    async def test_forced_charge_start_period_1(
        self, inverter: HybridInverter, mock_client: LuxpowerClient
    ) -> None:
        """Forced charge start period 1 writes register 78 (76 + 1*2)."""
        await inverter.set_forced_charge_schedule_start(1, 22, 0)

        mock_client.api.control.write_parameters.assert_called_once_with(
            "1234567890", {78: pack_time(22, 0)}
        )

    @pytest.mark.asyncio
    async def test_forced_charge_end_period_0(
        self, inverter: HybridInverter, mock_client: LuxpowerClient
    ) -> None:
        """Forced charge end period 0 writes register 77 (76 + 0*2 + 1)."""
        await inverter.set_forced_charge_schedule_end(0, 6, 0)

        mock_client.api.control.write_parameters.assert_called_once_with(
            "1234567890", {77: pack_time(6, 0)}
        )

    # ── Forced discharge ──

    @pytest.mark.asyncio
    async def test_forced_discharge_start_period_0(
        self, inverter: HybridInverter, mock_client: LuxpowerClient
    ) -> None:
        """Forced discharge start period 0 writes register 84."""
        await inverter.set_forced_discharge_schedule_start(0, 16, 0)

        mock_client.api.control.write_parameters.assert_called_once_with(
            "1234567890", {84: pack_time(16, 0)}
        )

    @pytest.mark.asyncio
    async def test_forced_discharge_end_period_2(
        self, inverter: HybridInverter, mock_client: LuxpowerClient
    ) -> None:
        """Forced discharge end period 2 writes register 89 (84 + 2*2 + 1)."""
        await inverter.set_forced_discharge_schedule_end(2, 21, 30)

        mock_client.api.control.write_parameters.assert_called_once_with(
            "1234567890", {89: pack_time(21, 30)}
        )

    # ── Single write, no sleep ──

    @pytest.mark.asyncio
    async def test_individual_setter_does_not_sleep(
        self, inverter: HybridInverter
    ) -> None:
        """Individual setters write one register, no inter-register delay."""
        with patch(
            "pylxpweb.devices.inverters.hybrid.asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            await inverter.set_ac_charge_schedule_start(0, 1, 30)

        mock_sleep.assert_not_called()

    # ── Validation ──

    @pytest.mark.asyncio
    async def test_start_invalid_period_raises(self, inverter: HybridInverter) -> None:
        """Period 3 raises ValueError on start setter."""
        with pytest.raises(ValueError, match="period must be 0, 1, or 2"):
            await inverter.set_ac_charge_schedule_start(3, 0, 0)

    @pytest.mark.asyncio
    async def test_end_invalid_period_raises(self, inverter: HybridInverter) -> None:
        """Period -1 raises ValueError on end setter."""
        with pytest.raises(ValueError, match="period must be 0, 1, or 2"):
            await inverter.set_forced_discharge_schedule_end(-1, 0, 0)

    @pytest.mark.asyncio
    async def test_invalid_hour_raises(self, inverter: HybridInverter) -> None:
        """Hour 24 raises ValueError via pack_time."""
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            await inverter.set_forced_charge_schedule_start(0, 24, 0)

    @pytest.mark.asyncio
    async def test_invalid_minute_raises(self, inverter: HybridInverter) -> None:
        """Minute 60 raises ValueError via pack_time."""
        with pytest.raises(ValueError, match="Minute must be 0-59"):
            await inverter.set_ac_charge_schedule_end(0, 12, 60)
