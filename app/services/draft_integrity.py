"""Stable fingerprints for binding approvals to the exact send payload."""

import hashlib
import json


def draft_fingerprint(state) -> str:
    """Fingerprint the complete draft and its selected attachments."""
    if state.draft is None:
        raise ValueError("A draft is required to calculate its fingerprint.")

    payload = {
        "draft": state.draft.model_dump(mode="json"),
        "attachments": [
            attachment.model_dump(mode="json")
            for attachment in state.attachments
        ],
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
