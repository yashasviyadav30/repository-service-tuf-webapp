# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""How close a role is to expiring, said in words."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.dto.schemas import ExpiryBand
from app.services.presenters import expiry_band
from tests.base import UnitTestCase

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


def at(**delta: float) -> datetime:
    return NOW + timedelta(**delta)


class TestExpiryBand(UnitTestCase):
    """Four bands, because valid and expired hide the difference.

    RSTUF renews timestamp roughly daily, so a healthy repository always has
    a role a few hours from expiring. Calling that plain valid until the
    moment it lapses discards the only useful warning.
    """

    def test_a_lapsed_role_is_expired(self) -> None:
        band, phrase = expiry_band(at(hours=-3), NOW)

        assert band is ExpiryBand.EXPIRED
        assert phrase == "expired 3h ago"

    def test_a_role_lapsed_for_days_counts_days(self) -> None:
        band, phrase = expiry_band(at(days=-5), NOW)

        assert band is ExpiryBand.EXPIRED
        assert phrase == "expired 5 days ago"

    def test_under_a_day_is_critical_and_counts_hours(self) -> None:
        band, phrase = expiry_band(at(hours=20, minutes=14), NOW)

        assert band is ExpiryBand.CRITICAL
        assert phrase == "expires in 20h 14m"

    def test_under_a_week_is_expiring(self) -> None:
        band, phrase = expiry_band(at(days=4), NOW)

        assert band is ExpiryBand.EXPIRING
        assert phrase == "expires in 4 days"

    def test_beyond_a_week_is_valid(self) -> None:
        band, phrase = expiry_band(at(days=30), NOW)

        assert band is ExpiryBand.VALID
        assert phrase == "expires in 30 days"

    def test_a_distant_date_is_shown_as_a_date(self) -> None:
        """Past a couple of months, a countdown stops being useful."""
        band, phrase = expiry_band(at(days=365), NOW)

        assert band is ExpiryBand.VALID
        assert phrase == "expires 2027-08-12"

    def test_one_day_is_not_pluralised(self) -> None:
        _, phrase = expiry_band(at(days=1, hours=1), NOW)

        assert phrase == "expires in 1 day"

    def test_a_naive_timestamp_is_read_as_utc(self) -> None:
        """Metadata carries an offset, but a caller may not."""
        band, _ = expiry_band(datetime(2026, 8, 13, 12, 0), NOW)

        assert band is ExpiryBand.EXPIRING
