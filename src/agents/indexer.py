"""
PageIndexBuilder: Builds a hierarchical PageIndex tree from LDUs.

Approach/Methodology:
- Groups LDUs by section headers and page ranges.
- Builds PageIndexSection tree with parent/child relationships.
- Adds debug prints and error location indicators for traceability.
"""
from typing import List, Dict, Any
from src.models.models import LDU, PageIndexSection
import traceback
import uuid

class PageIndexBuilder:
    """
    Builds a PageIndex tree from a list of LDUs.
    """
    def __init__(self):
        pass

    def build(self, ldu_list: List[LDU]) -> PageIndexSection:
        """
        Build a PageIndex tree from LDUs.
        Args:
            ldu_list: List of LDUs (output of ChunkingEngine)
        Returns:
            PageIndexSection: Root section of the PageIndex tree
        """
        try:
            # Group LDUs by parent_section (simple flat tree for demo)
            section_map: Dict[str, List[LDU]] = {}
            for ldu in ldu_list:
                section = ldu.parent_section or "root"
                section_map.setdefault(section, []).append(ldu)
            # Create root section
            root = PageIndexSection(
                section_id="root",
                title="Document Root",
                page_start=min(ldu.page_refs[0] for ldu in ldu_list if ldu.page_refs),
                page_end=max(ldu.page_refs[-1] for ldu in ldu_list if ldu.page_refs),
                child_sections=[],
                key_entities=[],
                summary="Document root section",
                data_types_present=list(set(ldu.chunk_type for ldu in ldu_list))
            )
            # Add child sections
            for section, ldus in section_map.items():
                if section == "root":
                    continue
                child = PageIndexSection(
                    section_id=section,
                    title=section,
                    page_start=min(ldu.page_refs[0] for ldu in ldus if ldu.page_refs),
                    page_end=max(ldu.page_refs[-1] for ldu in ldus if ldu.page_refs),
                    child_sections=[],
                    key_entities=[],
                    summary=f"Section {section}",
                    data_types_present=list(set(ldu.chunk_type for ldu in ldus))
                )
                root.child_sections.append(child)
            print(f"[DEBUG] Built PageIndex with {len(root.child_sections)} sections.")
            return root
        except Exception as e:
            print(f"[ERROR] Exception in PageIndexBuilder.build: {e}")
            traceback.print_exc()
            raise
