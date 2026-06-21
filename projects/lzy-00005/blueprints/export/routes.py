from flask import Blueprint, request, jsonify, Response
from blueprints.export.services import ExportService

export_bp = Blueprint('export', __name__)

@export_bp.route('/<note_id>', methods=['GET'])
def export_note(note_id):
    content = ExportService.export_note(note_id)
    filename = f'zettelkasten-{note_id}.md'
    return Response(
        content,
        mimetype='text/markdown',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@export_bp.route('', methods=['GET'])
def export_all():
    content = ExportService.export_all()
    filename = 'zettelkasten-export.md'
    return Response(
        content,
        mimetype='text/markdown',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
