__version__ = "1.0.0"

from .database import Database
from .organizer import OrganizerEngine
from .rule_engine import RuleEngine, RuleMatcher, FileInfo, RuleCondition
from .templates import TemplateManager
from .file_operator import FileOperator, FileOperation, ActionType, FileOperationException
from .scanner import FileScanner, ScanResult, FileNode, DirectoryStats
from .recommender import SmartRecommender, RecommendationResult, Recommendation, RecommendedStructure, StructureDiff
from .incremental import IncrementalAnalyzer, ScanSnapshot, IncrementalDiff, FileChange
from .exporter import RuleExporter, ExportOptions
from .smart_recommend import SmartRecommenderEngine, SmartAnalyzeResult

__all__ = [
    "Database",
    "OrganizerEngine",
    "RuleEngine",
    "RuleMatcher",
    "FileInfo",
    "RuleCondition",
    "TemplateManager",
    "FileOperator",
    "FileOperation",
    "ActionType",
    "FileOperationException",
    "FileScanner",
    "ScanResult",
    "FileNode",
    "DirectoryStats",
    "SmartRecommender",
    "RecommendationResult",
    "Recommendation",
    "RecommendedStructure",
    "StructureDiff",
    "IncrementalAnalyzer",
    "ScanSnapshot",
    "IncrementalDiff",
    "FileChange",
    "RuleExporter",
    "ExportOptions",
    "SmartRecommenderEngine",
    "SmartAnalyzeResult",
]
