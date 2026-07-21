import pytest

from icla.exceptions import DuplicateArtifactError
from icla.storage import AppendOnlyStore


def test_append_only_store_refuses_overwrite(tmp_path):
    store = AppendOnlyStore(tmp_path)
    store.append("evidence", "EVD-1", {"id": "EVD-1"})
    with pytest.raises(DuplicateArtifactError):
        store.append("evidence", "EVD-1", {"id": "EVD-1", "changed": True})
