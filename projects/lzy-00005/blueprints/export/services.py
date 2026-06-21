from models.note_repository import NoteRepository
from models.link_repository import LinkRepository
from models.tag_repository import TagRepository
import re

class ExportService:
    @staticmethod
    def export_note(note_id, visited=None):
        if visited is None:
            visited = set()
        if note_id in visited:
            return ''
        visited.add(note_id)

        note = NoteRepository.get_by_id(note_id)
        if not note:
            return ''

        tags = TagRepository.get_note_tags(note_id)
        outgoing = LinkRepository.get_outgoing_links(note_id)
        incoming = LinkRepository.get_incoming_links(note_id)

        parts = []
        parts.append(f'# {note["title"]}')
        parts.append('')
        parts.append(f'**ID**: {note["id"]}')
        parts.append(f'**Created**: {note["created_at"]}')
        parts.append(f'**Updated**: {note["updated_at"]}')
        if tags:
            tag_str = ', '.join([f'`{t["name"]}`' for t in tags])
            parts.append(f'**Tags**: {tag_str}')
        parts.append('')
        parts.append('---')
        parts.append('')
        parts.append(note['content'])
        parts.append('')

        if outgoing:
            parts.append('---')
            parts.append('')
            parts.append('## Outgoing Links')
            parts.append('')
            for link in outgoing:
                parts.append(f'- [[{link["id"]}]] {link["title"]}')
            parts.append('')

        if incoming:
            parts.append('---')
            parts.append('')
            parts.append('## Incoming Links')
            parts.append('')
            for link in incoming:
                parts.append(f'- [[{link["id"]}]] {link["title"]}')
            parts.append('')

        linked_ids = set()
        for link in outgoing + incoming:
            if link['id'] not in visited:
                linked_ids.add(link['id'])

        for linked_id in linked_ids:
            parts.append('')
            parts.append('<hr style="border: 2px solid #333; margin: 2rem 0;">')
            parts.append('')
            parts.append(ExportService.export_note(linked_id, visited))

        return '\n'.join(parts)

    @staticmethod
    def export_all():
        notes = NoteRepository.get_all()
        if not notes:
            return '# No notes to export\n'
        return ExportService.export_note(notes[0]['id'])
