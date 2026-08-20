# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""The commands the README documents can actually start the application."""

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
RUN_LOCAL = BACKEND_ROOT / "scripts" / "run_local.sh"


def run_dev_recipe() -> str:
    """The commands the run-dev target runs."""
    body = re.search(
        r"^run-dev:\n((?:\t.*\n)+)", MAKEFILE.read_text(encoding="utf-8"), re.M
    )
    assert body is not None, "the Makefile has no run-dev target"
    return body.group(1)


def importable_from(directory: Path, module: str, command: str) -> None:
    """Fail unless ``module`` imports with only ``directory`` on the path."""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(directory)

    result = subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=BACKEND_ROOT,
        env=environment,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        pytest.fail(f"`{command}` cannot import {module}:\n{result.stderr}")


class TestEntryPoints(UnitTestCase):
    """pytest puts src on the path itself, through pyproject.toml. Nothing
    else does, so a layout change can leave these commands unable to find
    the application while the whole suite stays green."""

    def test_run_dev_can_import_the_application(self) -> None:
        recipe = run_dev_recipe()
        target = re.search(r"uvicorn (\S+)", recipe)
        app_dir = re.search(r"--app-dir (\S+)", recipe)

        assert target is not None, "run-dev does not name a uvicorn target"
        assert app_dir is not None, "run-dev does not pass --app-dir"

        importable_from(
            BACKEND_ROOT / app_dir.group(1),
            target.group(1).split(":")[0],
            recipe.strip(),
        )

    def test_run_local_can_import_the_application(self) -> None:
        script = RUN_LOCAL.read_text(encoding="utf-8")

        exported = re.search(
            r'^export PYTHONPATH="\$\{PYTHONPATH:-(.+)\}"$', script, re.M
        )
        target = re.search(r"uvicorn (\S+)", script)

        assert exported is not None, "run_local.sh does not export PYTHONPATH"
        assert (
            target is not None
        ), "run_local.sh does not name a uvicorn target"

        # $PWD is the backend directory: the script changes to it first.
        path = exported.group(1).replace("$PWD", str(BACKEND_ROOT))

        importable_from(
            Path(path), target.group(1).split(":")[0], "./scripts/run_local.sh"
        )
