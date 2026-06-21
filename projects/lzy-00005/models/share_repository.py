from models.database import get_db
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta


class ShareRepository:
    @staticmethod
    def generate_id():
        return uuid.uuid4().hex[:12]

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_password(password):
        if not password:
            return None
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_password(password_hash, password):
        if not password_hash:
            return True
        if not password:
            return False
        return hashlib.sha256(password.encode('utf-8')).hexdigest() == password_hash

    @staticmethod
    def create_share(note_id, permission='read', password=None, expires_at=None, created_by='local-user'):
        db = get_db()
        share_id = ShareRepository.generate_id()
        share_token = ShareRepository.generate_token()
        password_hash = ShareRepository.hash_password(password)
        now = datetime.now().isoformat()

        db.execute(
            '''INSERT INTO note_shares (id, note_id, share_token, permission, password_hash,
               expires_at, created_at, created_by, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)''',
            (share_id, note_id, share_token, permission, password_hash,
             expires_at, now, created_by)
        )
        db.commit()
        return ShareRepository.get_by_id(share_id)

    @staticmethod
    def get_by_id(share_id):
        db = get_db()
        row = db.execute(
            '''SELECT id, note_id, share_token, permission, password_hash, expires_at,
                      created_at, created_by, is_active
               FROM note_shares WHERE id = ?''',
            (share_id,)
        ).fetchone()
        return ShareRepository._serialize(row) if row else None

    @staticmethod
    def get_by_token(share_token):
        db = get_db()
        row = db.execute(
            '''SELECT id, note_id, share_token, permission, password_hash, expires_at,
                      created_at, created_by, is_active
               FROM note_shares WHERE share_token = ?''',
            (share_token,)
        ).fetchone()
        return ShareRepository._serialize(row) if row else None

    @staticmethod
    def get_by_note_id(note_id, include_inactive=False):
        db = get_db()
        query = '''SELECT id, note_id, share_token, permission, password_hash, expires_at,
                          created_at, created_by, is_active
                   FROM note_shares WHERE note_id = ?'''
        params = [note_id]
        if not include_inactive:
            query += ' AND is_active = 1'
        query += ' ORDER BY created_at DESC'
        rows = db.execute(query, params).fetchall()
        return [ShareRepository._serialize(row) for row in rows]

    @staticmethod
    def get_all_active():
        db = get_db()
        rows = db.execute(
            '''SELECT id, note_id, share_token, permission, password_hash, expires_at,
                      created_at, created_by, is_active
               FROM note_shares WHERE is_active = 1
               ORDER BY created_at DESC'''
        ).fetchall()
        return [ShareRepository._serialize(row) for row in rows]

    @staticmethod
    def revoke(share_id):
        db = get_db()
        db.execute(
            'UPDATE note_shares SET is_active = 0 WHERE id = ?',
            (share_id,)
        )
        db.commit()
        return ShareRepository.get_by_id(share_id)

    @staticmethod
    def delete(share_id):
        db = get_db()
        db.execute('DELETE FROM note_shares WHERE id = ?', (share_id,))
        db.commit()
        return True

    @staticmethod
    def delete_by_note_id(note_id):
        db = get_db()
        db.execute('DELETE FROM note_shares WHERE note_id = ?', (note_id,))
        db.commit()
        return True

    @staticmethod
    def is_valid(share):
        if not share or not share.get('is_active'):
            return False
        if share.get('expires_at'):
            try:
                expires = datetime.fromisoformat(share['expires_at'])
                if datetime.now() > expires:
                    return False
            except (ValueError, TypeError):
                pass
        return True

    @staticmethod
    def _serialize(row):
        if not row:
            return None
        data = dict(row)
        has_password = data.get('password_hash') is not None
        data['has_password'] = has_password
        del data['password_hash']
        return data
