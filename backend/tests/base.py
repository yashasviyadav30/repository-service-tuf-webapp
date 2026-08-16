# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""What the test classes inherit from.

The conditions the integration tests depend on sit on their base class, so
a new test cannot forget one and appear to pass.
"""

from tests.conftest import requires_fixtures, requires_symlinks


class UnitTestCase:
    """A test that reaches nothing outside this process."""


class RepositoryTestCase:
    """A test driven against a generated repository, through the API.

    Skips itself, with the reason stated, where the platform cannot support
    it. A green run that quietly omitted these would be worse than a red one.
    """

    pytestmark = [requires_fixtures, requires_symlinks]
