from models.version_repository import VersionRepository
from models.note_repository import NoteRepository


class VersionService:
    @staticmethod
    def get_note_versions(note_id, limit=None, offset=0):
        note = NoteRepository.get_by_id(note_id)
        if not note:
            return None
        versions = VersionRepository.get_by_note_id(note_id, limit=limit, offset=offset)
        total = VersionRepository.count_by_note_id(note_id)
        return {
            'note': note,
            'versions': versions,
            'total': total
        }

    @staticmethod
    def get_version(version_id):
        version = VersionRepository.get_by_id(version_id)
        if not version:
            return None
        note = NoteRepository.get_by_id(version['note_id'])
        return {
            'version': version,
            'note_id': version['note_id'],
            'note_title': note['title'] if note else None
        }

    @staticmethod
    def restore_version(note_id, version_id):
        note = NoteRepository.get_by_id(note_id)
        version = VersionRepository.get_by_id(version_id)
        if not note or not version:
            return None
        if version['note_id'] != note_id:
            return None
        restored_note = NoteRepository.restore_version(note_id, version_id)
        return restored_note

    @staticmethod
    def delete_version(version_id):
        version = VersionRepository.get_by_id(version_id)
        if not version:
            return False
        VersionRepository.delete(version_id)
        return True
