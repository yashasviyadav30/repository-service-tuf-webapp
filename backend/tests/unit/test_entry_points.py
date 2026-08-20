# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""The command the README documents can actually start the application."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from tests.base import UnitTestCase

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
MAKEFILE = BACKEND_ROOT / "Makefile"


def run_dev_recipe() -> str:
    """The commands the run-dev target runs."""
    body = re.search(
        r"^run-dev:\n((?:\t.*\n)+)", MAKEFILE.read_text(encoding="utf-8"), re.M
    )
    assert body is not None, "the Makefile has no run-dev target"
    return body.group(1)


class TestRunDev(UnitTestCase):
    """pytest puts src on the path itself, through pyproject.toml. Nothing
    else does, so a layout change can leave this command unable to find the
    application while the whole suite stays green."""

    def test_the_documented_command_can_import_the_application(self) -> None:
        recipe = run_dev_recipe()
        target = re.search(r"uvicorn (\S+)", recipe)
        app_dir = re.search(r"--app-dir (\S+)", recipe)

        assert target is not None, "run-dev does not name a uvicorn target"
        assert app_dir is not None, "run-dev does not pass --app-dir"

        module = target.group(1).split(":")[0]
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(BACKEND_ROOT / app_dir.group(1))

        result = subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            cwd=BACKEND_ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.fail(
                f"`{recipe.strip()}` cannot import {module}:\n{result.stderr}"
            )
