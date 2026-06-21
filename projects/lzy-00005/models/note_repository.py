from models.database import get_db
from models.version_repository import VersionRepository
import uuid
from datetime import datetime


def generate_change_summary(old_title, new_title, old_content, new_content):
    changes = []
    if old_title != new_title:
        old_t = old_title or '(空标题)'
        new_t = new_title or '(空标题)'
        changes.append(f'标题: "{old_t}" → "{new_t}"')
    if old_content != new_content:
        old_len = len(old_content or '')
        new_len = len(new_content or '')
        diff = new_len - old_len
        if diff > 0:
            changes.append(f'内容增加 {diff} 字符')
        elif diff < 0:
            changes.append(f'内容减少 {abs(diff)} 字符')
        else:
            changes.append('内容修改')
    return '; '.join(changes) if changes else '未检测到修改'


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
    def create(title, content='', save_version=True):
        db = get_db()
        note_id = NoteRepository.generate_id()
        now = datetime.now().isoformat()
        db.execute(
            'INSERT INTO notes (id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
            (note_id, title, content, now, now)
        )
        db.commit()
        if save_version:
            VersionRepository.create_version(
                note_id, title, content,
                change_summary='创建笔记',
                modified_by='local-user'
            )
        return NoteRepository.get_by_id(note_id)

    @staticmethod
    def update(note_id, title=None, content=None, save_version=True):
        db = get_db()
        note = NoteRepository.get_by_id(note_id)
        if not note:
            return None
        old_title = note['title']
        old_content = note['content']
        new_title = title if title is not None else old_title
        new_content = content if content is not None else old_content

        if old_title == new_title and old_content == new_content:
            return note

        now = datetime.now().isoformat()
        db.execute(
            'UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?',
            (new_title, new_content, now, note_id)
        )
        db.commit()

        if save_version:
            summary = generate_change_summary(old_title, new_title, old_content, new_content)
            VersionRepository.create_version(
                note_id, new_title, new_content,
                change_summary=summary,
                modified_by='local-user'
            )
        return NoteRepository.get_by_id(note_id)

    @staticmethod
    def restore_version(note_id, version_id):
        note = NoteRepository.get_by_id(note_id)
        version = VersionRepository.get_by_id(version_id)
        if not note or not version:
            return None
        if version['note_id'] != note_id:
            return None
        return NoteRepository.update(
            note_id,
            title=version['title'],
            content=version['content'],
            save_version=True
        )

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
