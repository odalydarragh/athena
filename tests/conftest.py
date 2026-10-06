# SPDX-License-Identifier: MIT
import pytest

from documdr.models import Annotation


@pytest.fixture
def ann():
    def _ann(**kwargs):
        attrs = dict(kwargs.pop("attrs", {}))
        data = {
            "kind": "REQ",
            "ref_id": "REQ-1",
            "statement": "The module shall halt.",
            "path": "mod.c",
            "line_number": 1,
            "content_sha256": "hash-1",
            "commit_sha": "commit-1",
            "contributor_ref": None,
            "attrs": attrs,
        }
        data.update(kwargs)
        return Annotation(**data)

    return _ann
