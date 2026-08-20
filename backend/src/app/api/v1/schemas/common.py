# SPDX-FileCopyrightText: 2026 Repository Service for TUF Contributors
#
# SPDX-License-Identifier: MIT

"""Shapes more than one endpoint answers with."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """What every failure from this API carries.

    Declared so it reaches the OpenAPI document, which is what a consumer
    generates its types from.
    """

    detail: str = Field(
        description="Why the request could not be answered",
        examples=["No trust anchor is available."],
    )
