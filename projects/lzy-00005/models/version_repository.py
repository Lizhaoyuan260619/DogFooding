from models.database import get_db
from datetime import datetime


class VersionRepository:
    @staticmethod
    def create_version(note_id, title, content, change_summary=None, modified_by='local-user'):
        db = get_db()
        now = datetime.now().isoformat()
        cursor = db.execute(
            '''INSERT INTO note_versions (note_id, title, content, change_summary, modified_by, created_at)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (note_id, title, content, change_summary, modified_by, now)
        )
        db.commit()
        return VersionRepository.get_by_id(cursor.lastrowid)

    @staticmethod
    def get_by_id(version_id):
        db = get_db()
        row = db.execute(
            '''SELECT id, note_id, title, content, change_summary, modified_by, created_at
               FROM note_versions WHERE id = ?''',
            (version_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_note_id(note_id, limit=None, offset=0):
        db = get_db()
        query = '''SELECT id, note_id, title, content, change_summary, modified_by, created_at
                   FROM note_versions WHERE note_id = ?
                   ORDER BY created_at DESC'''
        params = [note_id]
        if limit:
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
        rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def count_by_note_id(note_id):
        db = get_db()
        row = db.execute(
            'SELECT COUNT(*) as cnt FROM note_versions WHERE note_id = ?',
            (note_id,)
        ).fetchone()
        return row['cnt'] if row else 0

    @staticmethod
    def delete(version_id):
        db = get_db()
        db.execute('DELETE FROM note_versions WHERE id = ?', (version_id,))
        db.commit()
        return True

    @staticmethod
    def delete_by_note_id(note_id):
        db = get_db()
        db.execute('DELETE FROM note_versions WHERE note_id = ?', (note_id,))
        db.commit()
        return True
