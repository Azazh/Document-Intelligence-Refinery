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
from src.agents.llm_provider import LLMProvider


class PageIndexBuilder:
    def query_pageindex(self, pageindex_root: PageIndexSection, query: str, top_k: int = 3) -> List[PageIndexSection]:
        """
        Traverse the PageIndex tree and return the top-k most relevant sections for the query.
        Uses LLM or embedding similarity to section summaries and titles.
        Args:
            pageindex_root: Root PageIndexSection
            query: User query string
            top_k: Number of sections to return
        Returns:
            List[PageIndexSection]: Top-k relevant sections
        """
        # Gather all sections (root + children, flat for now)
        def gather_sections(section: PageIndexSection) -> List[PageIndexSection]:
            sections = [section]
            for child in section.child_sections:
                sections.extend(gather_sections(child))
            return sections

        all_sections = gather_sections(pageindex_root)

        # Compute similarity between query and each section (title + summary)
        scored_sections = []
        for section in all_sections:
            text = (section.title or "") + ". " + (section.summary or "")
            try:
                # Use LLMProvider to score relevance (fallback: simple keyword match)
                prompt = f"Given the user query: '{query}', rate the relevance of the following section (title and summary) on a scale of 1 (not relevant) to 10 (highly relevant).\nSection: {text}\nRelevance score:"
                score_str = self.llm_provider.chat([
                    {"role": "system", "content": "You are a helpful assistant that rates section relevance for document navigation."},
                    {"role": "user", "content": prompt}
                ], temperature=0.0, max_tokens=2, provider=self.llm_provider_name)
                try:
                    score = float(score_str.strip().split()[0])
                except Exception:
                    score = 0.0
            except Exception:
                # Fallback: simple keyword overlap
                score = sum(1 for word in query.lower().split() if word in text.lower())
            scored_sections.append((score, section))

        # Sort by score descending and return top_k
        scored_sections.sort(reverse=True, key=lambda x: x[0])
        return [s for _, s in scored_sections[:top_k]]
    """
    Builds a PageIndex tree from a list of LDUs, with LLM summaries for each section.
    """
    def __init__(self, llm_provider=None, llm_provider_name="ollama"):
        self.llm_provider = llm_provider or LLMProvider()
        self.llm_provider_name = llm_provider_name

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

            def summarize_section(ldus, section_title):
                # Concatenate content for summary prompt (truncate if too long)
                section_text = "\n".join(ldu.content for ldu in ldus)
                if len(section_text) > 4000:
                    section_text = section_text[:4000] + "..."
                try:
                    summary = self.llm_provider.summarize(section_text, provider=self.llm_provider_name)
                except Exception as e:
                    summary = f"[LLM summary error: {e}]"
                return summary

            # Create root section
            root_ldus = section_map.get("root", ldu_list)
            root_summary = summarize_section(root_ldus, "Document Root")
            root = PageIndexSection(
                section_id="root",
                title="Document Root",
                page_start=min(ldu.page_refs[0] for ldu in ldu_list if ldu.page_refs),
                page_end=max(ldu.page_refs[-1] for ldu in ldu_list if ldu.page_refs),
                child_sections=[],
                key_entities=[],
                summary=root_summary,
                data_types_present=list(set(ldu.chunk_type for ldu in ldu_list))
            )
            # Add child sections
            for section, ldus in section_map.items():
                if section == "root":
                    continue
                section_summary = summarize_section(ldus, section)
                child = PageIndexSection(
                    section_id=section,
                    title=section,
                    page_start=min(ldu.page_refs[0] for ldu in ldus if ldu.page_refs),
                    page_end=max(ldu.page_refs[-1] for ldu in ldus if ldu.page_refs),
                    child_sections=[],
                    key_entities=[],
                    summary=section_summary,
                    data_types_present=list(set(ldu.chunk_type for ldu in ldus))
                )
                root.child_sections.append(child)
            print(f"[DEBUG] Built PageIndex with {len(root.child_sections)} sections (LLM summaries included).")
            return root
        except Exception as e:
            print(f"[ERROR] Exception in PageIndexBuilder.build: {e}")
            traceback.print_exc()
            raise
