"""
Tests for database service bulk delete functionality.

Requirements:
- Test delete_history_bulk deletes multiple records in transaction
- Test audio file cleanup for all deleted entries
- Test empty list edge case handling
- Test invalid IDs handling
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, call
from services.database import DatabaseService


@pytest.fixture
def db_service():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = Path(temp_dir) / "test.db"
        db = DatabaseService(str(test_db_path))
        yield db
        # Cleanup handled by tempfile


def test_delete_history_bulk(db_service):
    """Verify delete_history_bulk deletes multiple records in transaction."""
    # 1. Create test entries
    ids = []
    for i in range(5):
        entry_id = db_service.add_history(
            text=f"Test transcription {i}",
            audio_relpath=None,
            audio_duration_ms=None,
            audio_size_bytes=None,
            audio_mime=None,
        )
        ids.append(entry_id)

    # 2. Delete 3 entries
    to_delete = [ids[0], ids[1], ids[2]]
    db_service.delete_history_bulk(to_delete)

    # 3. Verify deleted entries are gone
    for deleted_id in to_delete:
        entry = db_service.get_history_entry(deleted_id)
        assert entry is None, f"Entry {deleted_id} should be deleted"

    # 4. Verify remaining entries still exist
    for kept_id in [ids[3], ids[4]]:
        entry = db_service.get_history_entry(kept_id)
        assert entry is not None, f"Entry {kept_id} should still exist"
        assert entry["id"] == kept_id
        assert "Test transcription" in entry["text"]


def test_delete_history_bulk_with_audio(db_service):
    """Verify audio files are cleaned up for all deleted entries."""
    # 1. Create test entries with audio files
    ids = []
    audio_paths = []
    for i in range(3):
        audio_relpath = f"audio/test_{i}.wav"
        audio_paths.append(audio_relpath)
        entry_id = db_service.add_history(
            text=f"Test transcription with audio {i}",
            audio_relpath=audio_relpath,
            audio_duration_ms=1000 + i * 100,
            audio_size_bytes=5000 + i * 500,
            audio_mime="audio/wav",
        )
        ids.append(entry_id)

    # 2. Mock _delete_audio_file to verify it's called
    with patch.object(db_service, '_delete_audio_file') as mock_delete_audio:
        # 3. Delete all 3 entries
        db_service.delete_history_bulk(ids)

        # 4. Verify _delete_audio_file was called for each audio file
        assert mock_delete_audio.call_count == 3, "Should delete audio for all 3 entries"

        # Verify it was called with the correct paths
        expected_calls = [call(audio_paths[0]), call(audio_paths[1]), call(audio_paths[2])]
        mock_delete_audio.assert_has_calls(expected_calls, any_order=True)

    # 5. Verify all entries deleted from database
    for deleted_id in ids:
        entry = db_service.get_history_entry(deleted_id)
        assert entry is None, f"Entry {deleted_id} should be deleted"


def test_delete_history_bulk_empty_list(db_service):
    """Verify empty ID list doesn't error."""
    # Create a test entry to verify database still works
    entry_id = db_service.add_history(
        text="Test entry",
        audio_relpath=None,
        audio_duration_ms=None,
        audio_size_bytes=None,
        audio_mime=None,
    )

    # Should not raise any exception
    db_service.delete_history_bulk([])

    # Verify database still functions normally
    entry = db_service.get_history_entry(entry_id)
    assert entry is not None, "Entry should still exist after empty bulk delete"
    assert entry["text"] == "Test entry"

    # Verify we can still add entries
    new_id = db_service.add_history(
        text="New entry after empty delete",
        audio_relpath=None,
        audio_duration_ms=None,
        audio_size_bytes=None,
        audio_mime=None,
    )
    assert new_id is not None, "Should be able to add entries after empty bulk delete"


def test_delete_history_bulk_invalid_ids(db_service):
    """Verify invalid IDs are handled gracefully."""
    # Create a test entry
    entry_id = db_service.add_history(
        text="Valid entry",
        audio_relpath=None,
        audio_duration_ms=None,
        audio_size_bytes=None,
        audio_mime=None,
    )

    # Try to delete non-existent IDs (should not raise exception)
    db_service.delete_history_bulk([9999, 10000])

    # Verify the valid entry still exists
    entry = db_service.get_history_entry(entry_id)
    assert entry is not None, "Valid entry should still exist"
    assert entry["text"] == "Valid entry"


def test_delete_history_bulk_transaction_integrity(db_service):
    """Verify bulk delete is transactional (all or nothing)."""
    # 1. Create test entries
    ids = []
    for i in range(3):
        entry_id = db_service.add_history(
            text=f"Test entry {i}",
            audio_relpath=None,
            audio_duration_ms=None,
            audio_size_bytes=None,
            audio_mime=None,
        )
        ids.append(entry_id)

    # 2. Mock _delete_audio_file to raise an exception on second call
    # This simulates a failure during bulk delete
    call_count = [0]

    def side_effect_raise_on_second(relpath):
        call_count[0] += 1
        if call_count[0] == 2:
            raise Exception("Simulated audio deletion failure")

    with patch.object(db_service, '_delete_audio_file', side_effect=side_effect_raise_on_second):
        # Add audio to the entries
        for i, entry_id in enumerate(ids):
            db_service.update_history_audio(
                history_id=entry_id,
                audio_relpath=f"audio/test_{i}.wav",
                audio_duration_ms=1000,
                audio_size_bytes=5000,
                audio_mime="audio/wav",
            )

        # 3. Try to delete - should raise exception
        with pytest.raises(Exception, match="Simulated audio deletion failure"):
            db_service.delete_history_bulk(ids)

    # 4. Verify transaction was rolled back - all entries should still exist
    for entry_id in ids:
        entry = db_service.get_history_entry(entry_id)
        assert entry is not None, f"Entry {entry_id} should still exist after rollback"


def test_delete_history_bulk_mixed_audio(db_service):
    """Verify bulk delete handles mix of entries with and without audio."""
    # 1. Create entries - some with audio, some without
    ids = []

    # Entry with audio
    id1 = db_service.add_history(
        text="Entry with audio",
        audio_relpath="audio/test1.wav",
        audio_duration_ms=1000,
        audio_size_bytes=5000,
        audio_mime="audio/wav",
    )
    ids.append(id1)

    # Entry without audio
    id2 = db_service.add_history(
        text="Entry without audio",
        audio_relpath=None,
        audio_duration_ms=None,
        audio_size_bytes=None,
        audio_mime=None,
    )
    ids.append(id2)

    # Another entry with audio
    id3 = db_service.add_history(
        text="Another entry with audio",
        audio_relpath="audio/test3.wav",
        audio_duration_ms=2000,
        audio_size_bytes=10000,
        audio_mime="audio/wav",
    )
    ids.append(id3)

    # 2. Mock _delete_audio_file
    with patch.object(db_service, '_delete_audio_file') as mock_delete_audio:
        # 3. Delete all entries
        db_service.delete_history_bulk(ids)

        # 4. Verify _delete_audio_file called only for entries with audio
        assert mock_delete_audio.call_count == 2, "Should delete audio for 2 entries only"

        # Verify called with correct paths
        expected_calls = [call("audio/test1.wav"), call("audio/test3.wav")]
        mock_delete_audio.assert_has_calls(expected_calls, any_order=True)

    # 5. Verify all entries deleted
    for deleted_id in ids:
        entry = db_service.get_history_entry(deleted_id)
        assert entry is None, f"Entry {deleted_id} should be deleted"
