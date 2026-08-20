# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Fixed values shared across the service."""

from tuf.ngclient import UpdaterConfig

TITLE = "Repository Service for TUF Webapp"

# The library's own cap for root metadata, applied to the anchor too.
ROOT_MAX_BYTES = 512_000

# What the client will accept from a storage server nobody here controls.
# max_root_rotations is what makes pinning a root once and leaving it safe:
# the client walks forward from the version it holds, checking each rotation
# against the one before it, and this is how far it will walk.
UPDATER_CONFIG = UpdaterConfig(
    max_root_rotations=256,
    max_delegations=32,
    root_max_length=512_000,
    timestamp_max_length=16_384,
    snapshot_max_length=2_000_000,
    targets_max_length=5_000_000,
    app_user_agent="rstuf-webapp",
)

# The cache key one verification pass is stored under.
OVERVIEW_KEY = "overview"

# How recently the repository must have been read for a refresh to be turned
# away. RSTUF's worker renews metadata every 5 minutes, so declining a second
# look within 5 seconds gives up nothing.
MIN_REFRESH_SECONDS = 5.0

# RSTUF records a readable name on each key it publishes.
RSTUF_KEY_NAME = "x-rstuf-key-name"

DAY = 86_400
WEEK = 7 * DAY
