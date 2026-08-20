# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What can go wrong reaching out of this process."""


class MetadataUnavailableError(RuntimeError):
    """The metadata could not be retrieved at all.

    Not the same as metadata that arrived and failed verification. Broken
    trust is what this service exists to show; an unreachable repository
    leaves nothing to show.
    """


class TrustAnchorMissingError(RuntimeError):
    """No trust anchor could be established, so nothing can be checked."""
