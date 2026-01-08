"""Tests for retry configuration."""
import pytest
from pydantic import ValidationError

from src.workers.clients.retry import RetryConfig


class TestRetryConfigDefaults:
    """Tests for RetryConfig default values."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 30.0
        assert config.exponential_base == 2.0
        assert config.retryable_status_codes == [429, 500, 502, 503, 504]

    def test_custom_values(self) -> None:
        """Test creating config with custom values."""
        config = RetryConfig(
            max_retries=5,
            base_delay_seconds=2.0,
            max_delay_seconds=60.0,
            exponential_base=3.0,
            retryable_status_codes=[429, 503],
        )

        assert config.max_retries == 5
        assert config.base_delay_seconds == 2.0
        assert config.max_delay_seconds == 60.0
        assert config.exponential_base == 3.0
        assert config.retryable_status_codes == [429, 503]


class TestRetryConfigValidation:
    """Tests for RetryConfig field validation."""

    def test_negative_max_retries_rejected(self) -> None:
        """Test that negative max_retries is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(max_retries=-1)

        assert "max_retries" in str(exc_info.value)

    def test_zero_max_retries_allowed(self) -> None:
        """Test that zero max_retries is allowed (no retries)."""
        config = RetryConfig(max_retries=0)
        assert config.max_retries == 0

    def test_zero_base_delay_rejected(self) -> None:
        """Test that zero base_delay_seconds is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(base_delay_seconds=0.0)

        assert "base_delay_seconds" in str(exc_info.value)

    def test_negative_base_delay_rejected(self) -> None:
        """Test that negative base_delay_seconds is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(base_delay_seconds=-1.0)

        assert "base_delay_seconds" in str(exc_info.value)

    def test_zero_max_delay_rejected(self) -> None:
        """Test that zero max_delay_seconds is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(max_delay_seconds=0.0)

        assert "max_delay_seconds" in str(exc_info.value)

    def test_negative_max_delay_rejected(self) -> None:
        """Test that negative max_delay_seconds is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(max_delay_seconds=-1.0)

        assert "max_delay_seconds" in str(exc_info.value)

    def test_exponential_base_one_rejected(self) -> None:
        """Test that exponential_base of 1.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(exponential_base=1.0)

        assert "exponential_base" in str(exc_info.value)

    def test_exponential_base_less_than_one_rejected(self) -> None:
        """Test that exponential_base less than 1.0 is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RetryConfig(exponential_base=0.5)

        assert "exponential_base" in str(exc_info.value)

    def test_empty_status_codes_allowed(self) -> None:
        """Test that empty retryable_status_codes list is allowed."""
        config = RetryConfig(retryable_status_codes=[])
        assert config.retryable_status_codes == []


class TestCalculateDelay:
    """Tests for calculate_delay method."""

    def test_first_attempt_delay(self) -> None:
        """Test delay calculation for first retry attempt."""
        config = RetryConfig(base_delay_seconds=1.0, exponential_base=2.0)

        delay = config.calculate_delay(1)

        # 1.0 * (2.0 ^ 1) = 2.0
        assert delay == 2.0

    def test_second_attempt_delay(self) -> None:
        """Test delay calculation for second retry attempt."""
        config = RetryConfig(base_delay_seconds=1.0, exponential_base=2.0)

        delay = config.calculate_delay(2)

        # 1.0 * (2.0 ^ 2) = 4.0
        assert delay == 4.0

    def test_third_attempt_delay(self) -> None:
        """Test delay calculation for third retry attempt."""
        config = RetryConfig(base_delay_seconds=1.0, exponential_base=2.0)

        delay = config.calculate_delay(3)

        # 1.0 * (2.0 ^ 3) = 8.0
        assert delay == 8.0

    def test_exponential_growth(self) -> None:
        """Test that delay grows exponentially."""
        config = RetryConfig(base_delay_seconds=1.0, exponential_base=2.0, max_delay_seconds=100.0)

        delay_1 = config.calculate_delay(1)  # 2.0
        delay_2 = config.calculate_delay(2)  # 4.0
        delay_3 = config.calculate_delay(3)  # 8.0

        assert delay_2 == delay_1 * 2
        assert delay_3 == delay_2 * 2

    def test_max_delay_cap(self) -> None:
        """Test that delay is capped at max_delay_seconds."""
        config = RetryConfig(
            base_delay_seconds=1.0,
            exponential_base=2.0,
            max_delay_seconds=10.0,
        )

        # 1.0 * (2.0 ^ 10) = 1024.0, but capped at 10.0
        delay = config.calculate_delay(10)

        assert delay == 10.0

    def test_delay_reaches_cap(self) -> None:
        """Test that delay is capped when it exceeds max."""
        config = RetryConfig(
            base_delay_seconds=5.0,
            exponential_base=2.0,
            max_delay_seconds=30.0,
        )

        # 5.0 * (2.0 ^ 1) = 10.0 (under cap)
        assert config.calculate_delay(1) == 10.0

        # 5.0 * (2.0 ^ 2) = 20.0 (under cap)
        assert config.calculate_delay(2) == 20.0

        # 5.0 * (2.0 ^ 3) = 40.0 (exceeds cap, should be 30.0)
        assert config.calculate_delay(3) == 30.0

        # 5.0 * (2.0 ^ 4) = 80.0 (exceeds cap, should be 30.0)
        assert config.calculate_delay(4) == 30.0

    def test_zero_attempt_returns_zero(self) -> None:
        """Test that attempt 0 returns 0 delay."""
        config = RetryConfig()

        delay = config.calculate_delay(0)

        assert delay == 0.0

    def test_negative_attempt_returns_zero(self) -> None:
        """Test that negative attempt returns 0 delay."""
        config = RetryConfig()

        delay = config.calculate_delay(-1)

        assert delay == 0.0

    def test_custom_base_delay(self) -> None:
        """Test delay calculation with custom base delay."""
        config = RetryConfig(base_delay_seconds=2.5, exponential_base=2.0)

        delay = config.calculate_delay(1)

        # 2.5 * (2.0 ^ 1) = 5.0
        assert delay == 5.0

    def test_custom_exponential_base(self) -> None:
        """Test delay calculation with custom exponential base."""
        config = RetryConfig(base_delay_seconds=1.0, exponential_base=3.0)

        delay_1 = config.calculate_delay(1)  # 1.0 * (3.0 ^ 1) = 3.0
        delay_2 = config.calculate_delay(2)  # 1.0 * (3.0 ^ 2) = 9.0

        assert delay_1 == 3.0
        assert delay_2 == 9.0

    def test_large_attempt_number(self) -> None:
        """Test that very large attempt numbers are capped."""
        config = RetryConfig(
            base_delay_seconds=1.0,
            exponential_base=2.0,
            max_delay_seconds=30.0,
        )

        # Even with attempt 100, should be capped
        delay = config.calculate_delay(100)

        assert delay == 30.0

    def test_fractional_delays(self) -> None:
        """Test that fractional delays work correctly."""
        config = RetryConfig(
            base_delay_seconds=0.5,
            exponential_base=2.0,
            max_delay_seconds=10.0,
        )

        delay = config.calculate_delay(1)

        # 0.5 * (2.0 ^ 1) = 1.0
        assert delay == 1.0


class TestRetryConfigUsage:
    """Tests for practical usage scenarios."""

    def test_typical_api_retry_config(self) -> None:
        """Test typical configuration for API retries."""
        config = RetryConfig(
            max_retries=3,
            base_delay_seconds=1.0,
            max_delay_seconds=30.0,
            exponential_base=2.0,
            retryable_status_codes=[429, 500, 502, 503, 504],
        )

        assert config.max_retries == 3
        assert 429 in config.retryable_status_codes
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
        assert config.calculate_delay(3) == 8.0

    def test_aggressive_retry_config(self) -> None:
        """Test aggressive retry configuration with more attempts."""
        config = RetryConfig(
            max_retries=10,
            base_delay_seconds=0.5,
            max_delay_seconds=10.0,
            exponential_base=1.5,
        )

        assert config.max_retries == 10
        assert config.calculate_delay(1) == 0.75  # 0.5 * 1.5
        assert config.calculate_delay(5) < 10.0  # Still under cap

    def test_conservative_retry_config(self) -> None:
        """Test conservative retry configuration with fewer attempts."""
        config = RetryConfig(
            max_retries=2,
            base_delay_seconds=5.0,
            max_delay_seconds=60.0,
            exponential_base=2.0,
        )

        assert config.max_retries == 2
        assert config.calculate_delay(1) == 10.0  # 5.0 * 2.0
        assert config.calculate_delay(2) == 20.0  # 5.0 * 4.0

    def test_no_retry_config(self) -> None:
        """Test configuration with no retries."""
        config = RetryConfig(max_retries=0)

        assert config.max_retries == 0
        # Delay calculation still works, but won't be used
        assert config.calculate_delay(1) == 2.0

    def test_status_code_check(self) -> None:
        """Test checking if status code is retryable."""
        config = RetryConfig(retryable_status_codes=[429, 500, 503])

        assert 429 in config.retryable_status_codes
        assert 500 in config.retryable_status_codes
        assert 503 in config.retryable_status_codes
        assert 404 not in config.retryable_status_codes
        assert 200 not in config.retryable_status_codes


class TestRetryConfigSerialization:
    """Tests for Pydantic serialization."""

    def test_model_dump(self) -> None:
        """Test that model can be dumped to dict."""
        config = RetryConfig()

        data = config.model_dump()

        assert data["max_retries"] == 3
        assert data["base_delay_seconds"] == 1.0
        assert data["max_delay_seconds"] == 30.0
        assert data["exponential_base"] == 2.0
        assert data["retryable_status_codes"] == [429, 500, 502, 503, 504]

    def test_model_dump_json(self) -> None:
        """Test that model can be serialized to JSON."""
        config = RetryConfig()

        json_str = config.model_dump_json()

        assert "max_retries" in json_str
        assert "base_delay_seconds" in json_str
        assert isinstance(json_str, str)

    def test_model_validate(self) -> None:
        """Test that model can be validated from dict."""
        data = {
            "max_retries": 5,
            "base_delay_seconds": 2.0,
            "max_delay_seconds": 60.0,
            "exponential_base": 3.0,
            "retryable_status_codes": [429],
        }

        config = RetryConfig.model_validate(data)

        assert config.max_retries == 5
        assert config.base_delay_seconds == 2.0

    def test_partial_config(self) -> None:
        """Test that partial config uses defaults."""
        config = RetryConfig(max_retries=5)

        assert config.max_retries == 5
        assert config.base_delay_seconds == 1.0  # Default
        assert config.max_delay_seconds == 30.0  # Default
