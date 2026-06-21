from models.note_repository import NoteRepository
from models.link_repository import LinkRepository

class GraphService:
    @staticmethod
    def get_graph_data():
        notes = NoteRepository.get_all()
        links = LinkRepository.get_all_links()

        nodes = []
        for note in notes:
            nodes.append({
                'id': note['id'],
                'title': note['title']
            })

        edges = []
        for link in links:
            edges.append({
                'source': link['source_id'],
                'target': link['target_id']
            })

        return {
            'nodes': nodes,
            'edges': edges
        }
