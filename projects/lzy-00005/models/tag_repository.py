from models.database import get_db

class TagRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute(
            '''SELECT t.id, t.name, COUNT(nt.note_id) as note_count
               FROM tags t
               LEFT JOIN note_tags nt ON t.id = nt.tag_id
               GROUP BY t.id
               ORDER BY t.name'''
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_by_name(name):
        db = get_db()
        row = db.execute(
            'SELECT id, name FROM tags WHERE name = ?',
            (name,)
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def create(name):
        db = get_db()
        db.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (name,))
        db.commit()
        return TagRepository.get_by_name(name)

    @staticmethod
    def get_note_tags(note_id):
        db = get_db()
        rows = db.execute(
            '''SELECT t.id, t.name
               FROM tags t
               JOIN note_tags nt ON t.id = nt.tag_id
               WHERE nt.note_id = ?
               ORDER BY t.name''',
            (note_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def set_note_tags(note_id, tag_names):
        db = get_db()
        db.execute('DELETE FROM note_tags WHERE note_id = ?', (note_id,))
        for name in tag_names:
            tag = TagRepository.get_by_name(name)
            if not tag:
                tag = TagRepository.create(name)
            db.execute(
                'INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)',
                (note_id, tag['id'])
            )
        db.commit()
        return TagRepository.get_note_tags(note_id)
