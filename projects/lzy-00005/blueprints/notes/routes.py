from flask import Blueprint, request, jsonify
from blueprints.notes.services import NoteService
from blueprints.notes.version_services import VersionService
from blueprints.notes.share_services import ShareService

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('', methods=['GET'])
def list_notes():
    notes = NoteService.get_all_notes()
    return jsonify(notes)

@notes_bp.route('/<note_id>', methods=['GET'])
def get_note(note_id):
    note = NoteService.get_note(note_id)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(note)

@notes_bp.route('', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400
    title = data['title']
    content = data.get('content', '')
    tags = data.get('tags', [])
    note = NoteService.create_note(title, content, tags)
    return jsonify(note), 201

@notes_bp.route('/<note_id>', methods=['PUT'])
def update_note(note_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    title = data.get('title')
    content = data.get('content')
    tags = data.get('tags')
    note = NoteService.update_note(note_id, title, content, tags)
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(note)

@notes_bp.route('/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    result = NoteService.delete_note(note_id)
    if not result:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify({'message': 'Note deleted successfully'})

@notes_bp.route('/tags', methods=['GET'])
def list_tags():
    tags = NoteService.get_all_tags()
    return jsonify(tags)

@notes_bp.route('/tags/<tag_name>', methods=['GET'])
def get_notes_by_tag(tag_name):
    notes = NoteService.get_notes_by_tag(tag_name)
    return jsonify(notes)


@notes_bp.route('/<note_id>/versions', methods=['GET'])
def get_note_versions(note_id):
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', default=0, type=int)
    result = VersionService.get_note_versions(note_id, limit=limit, offset=offset)
    if not result:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(result)

@notes_bp.route('/<note_id>/versions/<version_id>', methods=['GET'])
def get_version(note_id, version_id):
    result = VersionService.get_version(version_id)
    if not result:
        return jsonify({'error': 'Version not found'}), 404
    if result['note_id'] != note_id:
        return jsonify({'error': 'Version does not belong to this note'}), 400
    return jsonify(result)

@notes_bp.route('/<note_id>/versions/<version_id>/restore', methods=['POST'])
def restore_version(note_id, version_id):
    data = request.get_json() or {}
    confirm = data.get('confirm', False)
    if not confirm:
        return jsonify({
            'error': 'Confirmation required',
            'message': '请确认要回退到此版本，当前未保存的修改将丢失'
        }), 400
    restored_note = VersionService.restore_version(note_id, version_id)
    if not restored_note:
        return jsonify({'error': 'Failed to restore version. Note or version not found.'}), 404
    return jsonify({
        'message': '版本回退成功',
        'note': restored_note
    })

@notes_bp.route('/<note_id>/versions/<version_id>', methods=['DELETE'])
def delete_version(note_id, version_id):
    result = VersionService.delete_version(version_id)
    if not result:
        return jsonify({'error': 'Version not found'}), 404
    return jsonify({'message': 'Version deleted successfully'})


@notes_bp.route('/shares', methods=['GET'])
def list_all_shares():
    shares = ShareService.get_all_shares()
    return jsonify(shares)

@notes_bp.route('/<note_id>/shares', methods=['GET'])
def get_note_shares(note_id):
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    result = ShareService.get_note_shares(note_id, include_inactive=include_inactive)
    if not result:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(result)

@notes_bp.route('/<note_id>/shares', methods=['POST'])
def create_share(note_id):
    data = request.get_json() or {}
    permission = data.get('permission', 'read')
    password = data.get('password')
    expires_days_raw = data.get('expires_days')
    expires_days = int(expires_days_raw) if expires_days_raw is not None else None
    expires_at = data.get('expires_at')

    if permission not in ('read', 'write'):
        return jsonify({'error': 'Invalid permission. Must be "read" or "write"'}), 400

    share = ShareService.create_share(
        note_id=note_id,
        permission=permission,
        password=password,
        expires_days=expires_days,
        expires_at=expires_at
    )
    if not share:
        return jsonify({'error': 'Note not found or invalid parameters'}), 404
    return jsonify(share), 201

@notes_bp.route('/shares/<share_id>', methods=['GET'])
def get_share(share_id):
    from models.share_repository import ShareRepository
    share = ShareRepository.get_by_id(share_id)
    if not share:
        return jsonify({'error': 'Share not found'}), 404
    share['is_valid'] = ShareRepository.is_valid(share)
    return jsonify(share)

@notes_bp.route('/shares/<share_id>/revoke', methods=['POST'])
def revoke_share(share_id):
    share = ShareService.revoke_share(share_id)
    if not share:
        return jsonify({'error': 'Share not found'}), 404
    return jsonify({'message': '分享已撤销', 'share': share})

@notes_bp.route('/shares/<share_id>', methods=['DELETE'])
def delete_share(share_id):
    result = ShareService.delete_share(share_id)
    if not result:
        return jsonify({'error': 'Share not found'}), 404
    return jsonify({'message': 'Share deleted successfully'})


@notes_bp.route('/shared/<share_token>', methods=['GET'])
def access_shared_note(share_token):
    password = request.args.get('password')
    result = ShareService.access_share(share_token, password=password)
    if 'error' in result:
        status = result.pop('status', 400)
        return jsonify(result), status
    return jsonify(result)

@notes_bp.route('/shared/<share_token>', methods=['PUT'])
def update_shared_note(share_token):
    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')
    password = data.get('password')

    if title is None and content is None:
        return jsonify({'error': 'No data provided'}), 400

    result = ShareService.update_shared_note(share_token, title=title, content=content, password=password)
    if 'error' in result:
        status = result.pop('status', 400)
        return jsonify(result), status
    return jsonify(result)
