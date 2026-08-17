# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Naming the keys root declares, for the status panel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.services.presenters import key_summaries
from tests.base import UnitTestCase

KEYID = "9f" * 32
SECOND = "3c" * 32


@dataclass
class Key:
    scheme: str = "ecdsa-sha2-nistp256"
    unrecognized_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    keyids: list[str]


@dataclass
class Root:
    keys: dict[str, Key]
    roles: dict[str, Role]


def root_declaring(keys: dict[str, Key], roles: dict[str, Role]) -> Any:
    """Return something shaped like root metadata.

    Stubbed rather than signed, because this reads declared fields and
    verifies nothing. A test that had to build a signed root to check how a
    key is labelled would be testing python-tuf.
    """
    return type("Document", (), {"signed": Root(keys, roles)})()


class TestNamingKeys(UnitTestCase):
    """A 64-character identifier tells an operator nothing on its own."""

    def test_uses_the_name_rstuf_records(self) -> None:
        document = root_declaring(
            {KEYID: Key(unrecognized_fields={"x-rstuf-key-name": "root_1"})},
            {"root": Role([KEYID])},
        )

        assert key_summaries(document)[KEYID].name == "root_1"

    def test_falls_back_to_a_short_identifier(self) -> None:
        document = root_declaring({KEYID: Key()}, {"root": Role([KEYID])})

        summary = key_summaries(document)[KEYID]
        assert summary.name == KEYID[:8]
        assert summary.keyid_short == KEYID[:8]

    def test_has_nothing_to_say_without_root(self) -> None:
        assert key_summaries(None) == {}


class TestOnlineAndOfflineKeys(UnitTestCase):
    """RSTUF keeps the online keys in a service and the rest offline.

    Which is which is the question an operator brings to this panel, and
    RSTUF answers it by recording the address of the service that holds a
    key. A key with no such address is one somebody keeps.
    """

    def test_marks_a_key_rstuf_holds_online(self) -> None:
        document = root_declaring(
            {
                KEYID: Key(
                    unrecognized_fields={
                        "x-rstuf-online-key-uri": "fn:/run/keys/online"
                    }
                )
            },
            {"timestamp": Role([KEYID])},
        )

        assert key_summaries(document)[KEYID].online is True

    def test_leaves_a_key_with_no_address_offline(self) -> None:
        document = root_declaring({KEYID: Key()}, {"root": Role([KEYID])})

        assert key_summaries(document)[KEYID].online is False


class TestWhatEachKeySigns(UnitTestCase):
    """One key can be authorised for several roles, and often is."""

    def test_names_every_role_the_key_signs(self) -> None:
        document = root_declaring(
            {KEYID: Key(), SECOND: Key()},
            {
                "root": Role([KEYID]),
                "targets": Role([KEYID, SECOND]),
                "snapshot": Role([SECOND]),
            },
        )

        summaries = key_summaries(document)
        assert summaries[KEYID].signs == ["root", "targets"]
        assert summaries[SECOND].signs == ["snapshot", "targets"]
