from models.share_repository import ShareRepository
from models.note_repository import NoteRepository
from models.tag_repository import TagRepository
from models.link_repository import LinkRepository
from models.version_repository import VersionRepository
from datetime import datetime, timedelta


class ShareService:
    @staticmethod
    def create_share(note_id, permission='read', password=None, expires_days=None, expires_at=None):
        note = NoteRepository.get_by_id(note_id)
        if not note:
            return None
        if permission not in ('read', 'write'):
            return None

        if expires_days and not expires_at:
            expires_at = (datetime.now() + timedelta(days=expires_days)).isoformat()

        share = ShareRepository.create_share(
            note_id=note_id,
            permission=permission,
            password=password,
            expires_at=expires_at
        )
        return share

    @staticmethod
    def get_note_shares(note_id, include_inactive=False):
        note = NoteRepository.get_by_id(note_id)
        if not note:
            return None
        shares = ShareRepository.get_by_note_id(note_id, include_inactive=include_inactive)
        for share in shares:
            share['is_valid'] = ShareRepository.is_valid(share)
        return {
            'note': note,
            'shares': shares
        }

    @staticmethod
    def get_all_shares():
        shares = ShareRepository.get_all_active()
        result = []
        for share in shares:
            note = NoteRepository.get_by_id(share['note_id'])
            share_data = dict(share)
            share_data['note_title'] = note['title'] if note else None
            share_data['is_valid'] = ShareRepository.is_valid(share)
            result.append(share_data)
        return result

    @staticmethod
    def revoke_share(share_id):
        share = ShareRepository.get_by_id(share_id)
        if not share:
            return None
        return ShareRepository.revoke(share_id)

    @staticmethod
    def delete_share(share_id):
        share = ShareRepository.get_by_id(share_id)
        if not share:
            return False
        ShareRepository.delete(share_id)
        return True

    @staticmethod
    def access_share(share_token, password=None):
        share = ShareRepository.get_by_token(share_token)
        if not share:
            return {'error': '分享链接不存在', 'status': 404}

        if not share.get('is_active'):
            return {'error': '分享链接已被撤销', 'status': 403}

        if share.get('expires_at'):
            try:
                expires = datetime.fromisoformat(share['expires_at'])
                if datetime.now() > expires:
                    return {'error': '分享链接已过期', 'status': 403}
            except (ValueError, TypeError):
                pass

        if share.get('has_password'):
            from models.database import get_db
            db = get_db()
            row = db.execute(
                'SELECT password_hash FROM note_shares WHERE share_token = ?',
                (share_token,)
            ).fetchone()
            if row and row['password_hash']:
                if not password:
                    return {'error': '需要访问密码', 'status': 401, 'require_password': True}
                if not ShareRepository.verify_password(row['password_hash'], password):
                    return {'error': '密码错误', 'status': 403, 'require_password': True}

        note = NoteRepository.get_by_id(share['note_id'])
        if not note:
            return {'error': '笔记不存在或已被删除', 'status': 404}

        note_data = {
            'id': note['id'],
            'title': note['title'],
            'content': note['content'],
            'created_at': note['created_at'],
            'updated_at': note['updated_at'],
            'tags': TagRepository.get_note_tags(note['id']),
            'permission': share['permission']
        }
        return {
            'note': note_data,
            'share': {
                'id': share['id'],
                'permission': share['permission'],
                'has_password': share.get('has_password', False),
                'expires_at': share.get('expires_at')
            }
        }

    @staticmethod
    def update_shared_note(share_token, title=None, content=None, password=None):
        access_result = ShareService.access_share(share_token, password)
        if 'error' in access_result:
            return access_result

        if access_result['share']['permission'] != 'write':
            return {'error': '权限不足，此分享为只读', 'status': 403}

        note_id = access_result['note']['id']
        old_note = NoteRepository.get_by_id(note_id)
        new_title = title if title is not None else old_note['title']
        new_content = content if content is not None else old_note['content']

        if old_note['title'] == new_title and old_note['content'] == new_content:
            return access_result

        from models.note_repository import generate_change_summary
        summary = generate_change_summary(old_note['title'], new_title, old_note['content'], new_content)
        VersionRepository.create_version(
            note_id, new_title, new_content,
            change_summary=f'[通过分享链接修改] {summary}',
            modified_by='share-guest'
        )

        note = NoteRepository.update(note_id, title=title, content=content, save_version=False)
        note_data = {
            'id': note['id'],
            'title': note['title'],
            'content': note['content'],
            'created_at': note['created_at'],
            'updated_at': note['updated_at'],
            'tags': TagRepository.get_note_tags(note['id']),
            'permission': access_result['share']['permission']
        }
        return {
            'note': note_data,
            'share': access_result['share']
        }
