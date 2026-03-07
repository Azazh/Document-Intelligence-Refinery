import concurrent.futures
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
    @staticmethod
    def extract_keywords(text, top_k=5):
            # Simple keyword extraction: most frequent non-stopword tokens
            import re
            from collections import Counter
            STOPWORDS = set([
                'the', 'and', 'of', 'to', 'in', 'a', 'for', 'on', 'with', 'as', 'by', 'at', 'from', 'is', 'an', 'be', 'are', 'this', 'that', 'it', 'or', 'was', 'were', 'has', 'have', 'but', 'not', 'which', 'can', 'will', 'may', 'all', 'any', 'if', 'so', 'do', 'does', 'did', 'than', 'then', 'such', 'their', 'its', 'also', 'more', 'other', 'into', 'no', 'we', 'our', 'you', 'your', 'they', 'them', 'he', 'she', 'his', 'her', 'about', 'over', 'under', 'out', 'up', 'down', 'who', 'what', 'when', 'where', 'why', 'how', 'been', 'being', 'because', 'should', 'would', 'could', 'must', 'shall', 'these', 'those', 'each', 'per', 'between', 'within', 'without', 'due', 'during', 'after', 'before', 'just', 'like', 'very', 'much', 'many', 'most', 'some', 'few', 'every', 'any', 'both', 'either', 'neither', 'one', 'two', 'three', 'first', 'second', 'third', 'new', 'old', 'same', 'different', 'own', 'used', 'using', 'use', 'made', 'make', 'makes', 'including', 'includes', 'included', 'including', 'among', 'amongst', 'through', 'throughout', 'across', 'against', 'towards', 'toward', 'upon', 'off', 'again', 'once', 'ever', 'never', 'always', 'often', 'sometimes', 'usually', 'rarely', 'seldom', 'now', 'still', 'yet', 'already', 'soon', 'later', 'early', 'recent', 'recently', 'long', 'short', 'high', 'low', 'large', 'small', 'big', 'little', 'great', 'greater', 'greatest', 'least', 'less', 'fewer', 'enough', 'too', 'such', 'own', 'same', 'next', 'last', 'past', 'future', 'current', 'former', 'latter', 'above', 'below', 'near', 'far', 'close', 'away', 'along', 'across', 'beside', 'behind', 'beyond', 'inside', 'outside', 'onto', 'upon', 'via', 'among', 'amid', 'amidst', 'despite', 'except', 'including', 'regarding', 'concerning', 'according', 'because', 'since', 'unless', 'although', 'though', 'whereas', 'while', 'whether', 'nor', 'either', 'neither', 'both', 'not', 'only', 'just', 'even', 'still', 'yet', 'already', 'soon', 'later', 'early', 'recent', 'recently', 'long', 'short', 'high', 'low', 'large', 'small', 'big', 'little', 'great', 'greater', 'greatest', 'least', 'less', 'fewer', 'enough', 'too', 'such', 'own', 'same', 'next', 'last', 'past', 'future', 'current', 'former', 'latter', 'above', 'below', 'near', 'far', 'close', 'away', 'along', 'across', 'beside', 'behind', 'beyond', 'inside', 'outside', 'onto', 'upon', 'via', 'among', 'amid', 'amidst', 'despite', 'except', 'including', 'regarding', 'concerning', 'according', 'because', 'since', 'unless', 'although', 'though', 'whereas', 'while', 'whether', 'nor', 'either', 'neither', 'both', 'not', 'only', 'just', 'even', 'still', 'yet', 'already', 'soon', 'later', 'early', 'recent', 'recently', 'long', 'short', 'high', 'low', 'large', 'small', 'big', 'little', 'great', 'greater', 'greatest', 'least', 'less', 'fewer', 'enough', 'too', 'such', 'own', 'same', 'next', 'last', 'past', 'future', 'current', 'former', 'latter', 'above', 'below', 'near', 'far', 'close', 'away', 'along', 'across', 'beside', 'behind', 'beyond', 'inside', 'outside', 'onto', 'upon', 'via', 'among', 'amid', 'amidst', 'despite', 'except', 'including', 'regarding', 'concerning', 'according', 'because', 'since', 'unless', 'although', 'though', 'whereas', 'while', 'whether', 'nor', 'either', 'neither', 'both', 'not', 'only', 'just', 'even', 'still', 'yet', 'already', 'soon', 'later', 'early', 'recent', 'recently', 'long', 'short', 'high', 'low', 'large', 'small', 'big', 'little', 'great', 'greater', 'greatest', 'least', 'less', 'fewer', 'enough', 'too', 'such', 'own', 'same', 'next', 'last', 'past', 'future', 'current', 'former', 'latter', 'above', 'below', 'near', 'far', 'close', 'away', 'along', 'across', 'beside', 'behind', 'beyond', 'inside', 'outside', 'onto', 'upon', 'via', 'among', 'amid', 'amidst', 'despite', 'except', 'including', 'regarding', 'concerning', 'according', 'because', 'since', 'unless', 'although', 'though', 'whereas', 'while', 'whether', 'nor', 'either', 'neither', 'both', 'not', 'only', 'just', 'even', 'still', 'yet', 'already', 'soon', 'later', 'early', 'recent', 'recently', 'long', 'short', 'high', 'low', 'large', 'small', 'big', 'little', 'great', 'greater', 'greatest', 'least', 'less', 'fewer', 'enough', 'too', 'such', 'own', 'same', 'next', 'last', 'past', 'future', 'current', 'former', 'latter', 'above', 'below', 'near', 'far', 'close', 'away', 'along', 'across', 'beside', 'behind', 'beyond', 'inside', 'outside', 'onto', 'upon', 'via', 'among', 'amid', 'amidst', 'despite', 'except', 'including', 'regarding', 'concerning', 'according', 'because', 'since', 'unless', 'although', 'though', 'whereas', 'while', 'whether', 'nor', 'either', 'neither', 'both', 'not', 'only', 'just', 'even', 'still', 'yet', 'already', 'soon', 'later', 'early', 'recent', 'recently', 'long', 'short', 'high', 'low', 'large', 'small', 'big', 'little', 'great', 'greater', 'greatest', 'least', 'less', 'fewer', 'enough', 'too', 'such', 'own', 'same', 'next', 'last', 'past', 'future', 'current', 'former', 'latter'])
            tokens = re.findall(r"\b\w+\b", text.lower())
            tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
            most_common = Counter(tokens).most_common(top_k)
            return [w for w, _ in most_common]

    BOILERPLATE_KEYWORDS = [
        "table of contents", "contents", "index", "footnote", "disclaimer", "confidential", "copyright", "all rights reserved"
    ]

    @staticmethod
    def is_boilerplate(text):
        text = text.lower()
        return any(keyword in text for keyword in PageIndexBuilder.BOILERPLATE_KEYWORDS)

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

    def build(self, ldu_list: List[LDU], doc_id: str = None, export_json: bool = True) -> PageIndexSection:
        """
        Build a PageIndex tree from LDUs.
        Args:
            ldu_list: List of LDUs (output of ChunkingEngine)
        Returns:
            PageIndexSection: Root section of the PageIndex tree
        """
        try:
            # Group LDUs by section and parent_section for hierarchy
            section_map: Dict[str, List[LDU]] = {}
            parent_map: Dict[str, str] = {}  # section -> parent_section
            for ldu in ldu_list:
                section = ldu.parent_section or "root"
                section_map.setdefault(section, []).append(ldu)
                if ldu.chunk_type == 'header' and ldu.content:
                    parent_map[ldu.content] = ldu.parent_section or "root"

            # Build section hierarchy: section -> [child_section_titles]
            children_map: Dict[str, list] = {}
            for child, parent in parent_map.items():
                children_map.setdefault(parent, []).append(child)

            def summarize_section(ldus, section_title):
                section_text = "\n".join(ldu.content for ldu in ldus)
                # Skip LLM for single-word/number/short/atomic sections
                import re
                sentences = re.split(r'(?<=[.!?]) +', section_text)
                num_sentences = sum(1 for s in sentences if len(s.strip().split()) > 3)
                if num_sentences < 2:
                    return f"[Skipped: not enough sentences for LLM summary: {section_title}]"
                # Pre-filter: skip boilerplate sections
                if self.is_boilerplate(section_title) or self.is_boilerplate(section_text):
                    return f"[Skipped boilerplate: {section_title}]"
                # Heuristic: If all LDUs are tables, use header+first row as summary
                if all(ldu.chunk_type == "table" for ldu in ldus):
                    headers = []
                    first_row = []
                    for ldu in ldus:
                        meta = ldu.metadata or {}
                        if "headers" in meta:
                            headers = meta["headers"]
                        if "rows" in meta and meta["rows"]:
                            first_row = meta["rows"][0]
                        if headers and first_row:
                            break
                    if headers:
                        summary = f"Table: {section_title}. Columns: {headers}. Example row: {first_row}"
                        return summary
                # Heuristic: If all LDUs are lists, use first 3 items
                if all(ldu.chunk_type == "list" for ldu in ldus):
                    items = []
                    for ldu in ldus:
                        meta = ldu.metadata or {}
                        if "items" in meta:
                            items.extend(meta["items"])
                        else:
                            items.extend(ldu.content.splitlines())
                        if len(items) >= 3:
                            break
                    summary = f"List: {section_title}. Top items: {items[:3]}"
                    return summary
                # Otherwise, fallback to hybrid: extract keywords, then LLM summary
                keywords = self.extract_keywords(section_text)
                if len(section_text) > 4000:
                    section_text = section_text[:4000] + "..."
                try:
                    summary = self.llm_provider.summarize(section_text, provider=self.llm_provider_name)
                    print(f"[DEBUG] LLM summary raw response for section '{section_title}': {summary}")
                except Exception as e:
                    summary = f"[LLM summary error: {e}]"
                if keywords:
                    return f"Keywords: {keywords}\nSummary: {summary}"
                else:
                    return summary

            # Parallelize summarization for all sections (root and children)
            root_ldus = section_map.get("root", ldu_list)
            section_args = [(ldus, section) for section, ldus in section_map.items() if section != "root"]

            summaries = {}
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Schedule all child section summaries in parallel
                future_to_section = {
                    executor.submit(summarize_section, ldus, section): (section, ldus)
                    for (ldus, section) in section_args
                }
                # Root summary (can be parallelized too, but usually just one)
                root_future = executor.submit(summarize_section, root_ldus, "Document Root")
                for future in concurrent.futures.as_completed(list(future_to_section.keys()) + [root_future]):
                    if future == root_future:
                        summaries["root"] = future.result()
                    else:
                        section, _ = future_to_section[future]
                        summaries[section] = future.result()

            # Add chunk_ids to each section

            def get_chunk_ids(ldus):
                # Always include LDU IDs if present, else fallback to index
                ids = []
                for idx, ldu in enumerate(ldus):
                    if hasattr(ldu, 'ldu_id') and ldu.ldu_id:
                        ids.append(ldu.ldu_id)
                    else:
                        ids.append(str(idx))
                return ids

            def extract_entities(ldus):
                # Simple keyword extraction for key_entities
                text = " ".join(ldu.content for ldu in ldus)
                return self.extract_keywords(text, top_k=7)

            def build_section(section_title):
                ldus = section_map.get(section_title, [])
                # Recursively build child sections
                child_titles = children_map.get(section_title, [])
                child_sections = [build_section(child) for child in child_titles]
                summary = summaries.get(section_title, "[Summary unavailable]")
                ldu_ids = [ldu.ldu_id for ldu in ldus if hasattr(ldu, 'ldu_id') and ldu.ldu_id]
                return PageIndexSection(
                    section_id=section_title,
                    title=section_title,
                    page_start=min(ldu.page_refs[0] for ldu in ldus if ldu.page_refs) if ldus else 1,
                    page_end=max(ldu.page_refs[-1] for ldu in ldus if ldu.page_refs) if ldus else 1,
                    child_sections=child_sections,
                    key_entities=extract_entities(ldus),
                    summary=summary,
                    data_types_present=list(set(ldu.chunk_type for ldu in ldus)),
                    chunk_ids=get_chunk_ids(ldus),
                    ldu_ids=ldu_ids
                )

            root = build_section("root")
            print(f"[DEBUG] Built PageIndex with {len(root.child_sections)} top-level sections (LLM summaries included, parallelized).")
            # Export as JSON if requested
            if export_json and doc_id:
                import os, json
                os.makedirs(".refinery/pageindex", exist_ok=True)
                out_path = f".refinery/pageindex/pageindex_{doc_id}.json"
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(root.model_dump(), f, ensure_ascii=False, indent=2)
                print(f"[DEBUG] PageIndex exported to {out_path}")
            return root
        except Exception as e:
            print(f"[ERROR] Exception in PageIndexBuilder.build: {e}")
            traceback.print_exc()
            raise
