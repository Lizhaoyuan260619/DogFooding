from models.database import get_db
import uuid
from datetime import datetime

class NoteRepository:
    @staticmethod
    def generate_id():
        return uuid.uuid4().hex[:12]

    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute(
            'SELECT id, title, content, created_at, updated_at FROM notes ORDER BY updated_at DESC'
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_id(note_id):
        db = get_db()
        row = db.execute(
            'SELECT id, title, content, created_at, updated_at FROM notes WHERE id = ?',
            (note_id,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(title, content=''):
        db = get_db()
        note_id = NoteRepository.generate_id()
        now = datetime.now().isoformat()
        db.execute(
            'INSERT INTO notes (id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
            (note_id, title, content, now, now)
        )
        db.commit()
        return NoteRepository.get_by_id(note_id)

    @staticmethod
    def update(note_id, title=None, content=None):
        db = get_db()
        note = NoteRepository.get_by_id(note_id)
        if not note:
            return None
        new_title = title if title is not None else note['title']
        new_content = content if content is not None else note['content']
        now = datetime.now().isoformat()
        db.execute(
            'UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?',
            (new_title, new_content, now, note_id)
        )
        db.commit()
        return NoteRepository.get_by_id(note_id)

    @staticmethod
    def delete(note_id):
        db = get_db()
        db.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        db.commit()
        return True

    @staticmethod
    def search(query):
        db = get_db()
        if len(query) >= 2:
            rows = db.execute(
                '''SELECT n.id, n.title, n.content, n.created_at, n.updated_at
                   FROM notes_fts fts
                   JOIN notes n ON fts.id = n.id
                   WHERE notes_fts MATCH ?
                   ORDER BY rank''',
                (query,)
            ).fetchall()
            if rows:
                return [dict(row) for row in rows]
        rows = db.execute(
            '''SELECT id, title, content, created_at, updated_at
               FROM notes
               WHERE title LIKE ? OR content LIKE ?
               ORDER BY updated_at DESC''',
            (f'%{query}%', f'%{query}%')
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_tag(tag_name):
        db = get_db()
        rows = db.execute(
            '''SELECT n.id, n.title, n.content, n.created_at, n.updated_at
               FROM notes n
               JOIN note_tags nt ON n.id = nt.note_id
               JOIN tags t ON nt.tag_id = t.id
               WHERE t.name = ?
               ORDER BY n.updated_at DESC''',
            (tag_name,)
        ).fetchall()
        return [dict(row) for row in rows]
