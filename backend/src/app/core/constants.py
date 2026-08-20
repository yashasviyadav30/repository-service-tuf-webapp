# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Fixed values shared across the service."""

from tuf.ngclient import UpdaterConfig

TITLE = "Repository Service for TUF Webapp"

# The library's own cap for root metadata, applied to the anchor too.
ROOT_MAX_BYTES = 512_000

# A delegated role holds artifact entries rather than a role table, so it
# is allowed more room than root. Bounded all the same: the file is
# fetched by code written here, and a storage server decides its size.
DELEGATED_MAX_BYTES = 5_000_000

# How many delegated roles are fetched at once while listing artifacts.
# A repository can hold 256 bins, and asking a storage server for all of
# them in one breath is a burst it did not agree to.
DELEGATED_FETCH_LIMIT = 8

# A role name arrives in a URL or a query string and is used to pick out a
# role, so it is constrained here and never trusted. This also rejects path
# traversal before the name reaches any code in this repository.
ROLE_NAME = r"^[A-Za-z0-9._-]{1,128}$"

# The same name, or nothing at all. Used where narrowing to a role is
# optional and an empty value means every role, which ROLE_NAME would reject.
OPTIONAL_ROLE_NAME = r"^$|^[A-Za-z0-9._-]{1,128}$"

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

# RSTUF records a readable name on each key it publishes, and the address of
# the service holding it where the key is an online one.
RSTUF_KEY_NAME = "x-rstuf-key-name"
RSTUF_ONLINE_KEY_URI = "x-rstuf-online-key-uri"

DAY = 86_400
WEEK = 7 * DAY

# How far back the root history walk goes unless asked otherwise. A
# long-lived repository may hold hundreds of versions, and fetching every one
# to draw a page nobody scrolled is work done for the repository, not the
# reader.
DEFAULT_HISTORY = 20
MAX_HISTORY = 256
