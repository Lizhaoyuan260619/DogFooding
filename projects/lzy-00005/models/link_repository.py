from models.database import get_db
import re

class LinkRepository:
    @staticmethod
    def parse_links(content):
        pattern = r'\[\[([a-f0-9]{12})\]\]'
        return re.findall(pattern, content)

    @staticmethod
    def get_outgoing_links(note_id):
        db = get_db()
        rows = db.execute(
            '''SELECT n.id, n.title, n.created_at, n.updated_at
               FROM notes n
               JOIN links l ON n.id = l.target_id
               WHERE l.source_id = ?
               ORDER BY n.title''',
            (note_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_incoming_links(note_id):
        db = get_db()
        rows = db.execute(
            '''SELECT n.id, n.title, n.created_at, n.updated_at
               FROM notes n
               JOIN links l ON n.id = l.source_id
               WHERE l.target_id = ?
               ORDER BY n.title''',
            (note_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def update_links(note_id, content):
        db = get_db()
        db.execute('DELETE FROM links WHERE source_id = ?', (note_id,))
        target_ids = LinkRepository.parse_links(content)
        for target_id in set(target_ids):
            if target_id != note_id:
                db.execute(
                    'INSERT OR IGNORE INTO links (source_id, target_id) VALUES (?, ?)',
                    (note_id, target_id)
                )
        db.commit()

    @staticmethod
    def get_all_links():
        db = get_db()
        rows = db.execute(
            'SELECT source_id, target_id FROM links'
        ).fetchall()
        return [dict(row) for row in rows]
