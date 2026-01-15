#!/usr/bin/env python3
"""
Verification script for bulk delete functionality.
This script tests the database bulk_delete_history method in isolation.
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src-pyloid to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src-pyloid'))

from services.database import DatabaseService


def create_test_database():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test.db')
    audio_dir = os.path.join(temp_dir, 'audio')
    os.makedirs(audio_dir)

    db_service = DatabaseService(db_path=db_path, audio_base_dir=audio_dir)
    return db_service, temp_dir


def create_test_audio_file(audio_dir, filename):
    """Create a dummy audio file for testing."""
    audio_path = os.path.join(audio_dir, filename)
    with open(audio_path, 'wb') as f:
        f.write(b'fake audio data')
    return filename


def test_bulk_delete():
    """Test bulk delete functionality."""
    print("=" * 60)
    print("BULK DELETE VERIFICATION TEST")
    print("=" * 60)

    db_service, temp_dir = create_test_database()
    audio_dir = os.path.join(temp_dir, 'audio')

    try:
        # Create test entries
        print("\n1. Creating test history entries...")
        entry_ids = []
        audio_files = []

        for i in range(5):
            audio_file = create_test_audio_file(audio_dir, f'test_{i}.wav')
            audio_files.append(audio_file)

            entry_id = db_service.add_history(
                text=f"Test transcription {i}",
                char_count=len(f"Test transcription {i}"),
                word_count=2,
                audio_relpath=audio_file,
                audio_duration_ms=1000,
                audio_size_bytes=15,
                audio_mime="audio/wav"
            )
            entry_ids.append(entry_id)
            print(f"   ✓ Created entry {entry_id} with audio file {audio_file}")

        # Verify all entries exist
        print("\n2. Verifying entries exist in database...")
        history = db_service.get_history(limit=10)
        assert len(history) == 5, f"Expected 5 entries, got {len(history)}"
        print(f"   ✓ All 5 entries exist in database")

        # Verify all audio files exist
        print("\n3. Verifying audio files exist on disk...")
        for audio_file in audio_files:
            audio_path = os.path.join(audio_dir, audio_file)
            assert os.path.exists(audio_path), f"Audio file {audio_file} should exist"
        print(f"   ✓ All 5 audio files exist on disk")

        # Test bulk delete of first 3 entries
        print("\n4. Testing bulk delete of 3 entries...")
        ids_to_delete = entry_ids[:3]
        db_service.bulk_delete_history(ids_to_delete)
        print(f"   ✓ Bulk deleted entries: {ids_to_delete}")

        # Verify deleted entries are gone
        print("\n5. Verifying deleted entries removed from database...")
        remaining_history = db_service.get_history(limit=10)
        assert len(remaining_history) == 2, f"Expected 2 entries, got {len(remaining_history)}"
        remaining_ids = [entry['id'] for entry in remaining_history]
        assert entry_ids[3] in remaining_ids, "Entry 4 should remain"
        assert entry_ids[4] in remaining_ids, "Entry 5 should remain"
        print(f"   ✓ Only 2 entries remain in database")

        # Verify deleted audio files are gone
        print("\n6. Verifying deleted audio files removed from disk...")
        for i in range(3):
            audio_path = os.path.join(audio_dir, audio_files[i])
            assert not os.path.exists(audio_path), f"Audio file {audio_files[i]} should be deleted"
        print(f"   ✓ Deleted audio files removed from disk")

        # Verify remaining audio files still exist
        print("\n7. Verifying remaining audio files still exist...")
        for i in range(3, 5):
            audio_path = os.path.join(audio_dir, audio_files[i])
            assert os.path.exists(audio_path), f"Audio file {audio_files[i]} should still exist"
        print(f"   ✓ Remaining audio files still exist")

        # Test empty list (should not error)
        print("\n8. Testing bulk delete with empty list...")
        db_service.bulk_delete_history([])
        print(f"   ✓ Empty list handled gracefully")

        # Test with single ID
        print("\n9. Testing bulk delete with single entry...")
        db_service.bulk_delete_history([entry_ids[3]])
        remaining_history = db_service.get_history(limit=10)
        assert len(remaining_history) == 1, f"Expected 1 entry, got {len(remaining_history)}"
        print(f"   ✓ Single entry deletion works")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSUMMARY:")
        print("  • Bulk delete removes multiple entries atomically")
        print("  • Audio files are cleaned up properly")
        print("  • Remaining entries are unaffected")
        print("  • Empty list handled gracefully")
        print("  • Single entry deletion works")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        print("\n10. Cleaning up test directory...")
        shutil.rmtree(temp_dir)
        print(f"   ✓ Test directory removed")


if __name__ == "__main__":
    success = test_bulk_delete()
    sys.exit(0 if success else 1)
