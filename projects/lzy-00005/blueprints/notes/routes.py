from flask import Blueprint, request, jsonify
from blueprints.notes.services import NoteService

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
