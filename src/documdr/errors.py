# SPDX-License-Identifier: MIT


class DocuMDRError(Exception):
    """Base error for the local compiler."""


class TenantNotFound(DocuMDRError):
    """No tenant with this id exists in the local store."""


class ProjectNotFound(DocuMDRError):
    """No project with this id exists for the tenant."""


class ExportBlocked(DocuMDRError):
    """Export wrote nothing because the human gate or the seat cap refused it."""

    def __init__(self, reasons: list[str]) -> None:
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))
