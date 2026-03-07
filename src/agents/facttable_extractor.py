import psycopg2
from psycopg2.extras import execute_values
from typing import List
from src.models.models import LDU
import re

class FactTableExtractor:
    """
    Extracts key-value numerical facts from LDUs and inserts them into a PostgreSQL FactTable.
    """
    def __init__(self, dbname="refinery_ai_document_intelligence", user="postgres", password="5492460", host="localhost", port=5432):
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
        self.ensure_table()

    def ensure_table(self):
        with self.conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS fact_table (
                    id SERIAL PRIMARY KEY,
                    document_name TEXT,
                    page_number INT,
                    key TEXT,
                    value TEXT,
                    year INT,
                    bbox JSONB,
                    content_hash TEXT
                )
            ''')
            self.conn.commit()

    def extract_facts(self, ldu_list: List[LDU], document_name: str):
        """
        Extracts facts from LDUs and inserts them into the fact_table.
        """
        fact_rows = []
        for ldu in ldu_list:
            # Only extract from tables and text blocks likely to contain facts
            if ldu.chunk_type in ("table", "text"):
                # Simple regex for key-value pairs (e.g., Revenue: $4.2B)
                matches = re.findall(r"([A-Za-z0-9\s\-]+):\s*([\$€¥£]?[\d,.]+[A-Za-z%]*)", ldu.content)
                for key, value in matches:
                    year = self._extract_year(ldu.content)
                    bbox = ldu.bounding_box.model_dump() if ldu.bounding_box else None
                    fact_rows.append((
                        document_name,
                        ldu.page_refs[0] if ldu.page_refs else None,
                        key.strip(),
                        value.strip(),
                        year,
                        bbox,
                        ldu.content_hash
                    ))
            # Optionally, add more sophisticated extraction for tables
        if fact_rows:
            self._insert_facts(fact_rows)

    def _insert_facts(self, rows):
        with self.conn.cursor() as cur:
            execute_values(cur, '''
                INSERT INTO fact_table (document_name, page_number, key, value, year, bbox, content_hash)
                VALUES %s
            ''', rows)
            self.conn.commit()

    def _extract_year(self, text):
        match = re.search(r"(20\d{2})", text)
        return int(match.group(1)) if match else None

    def close(self):
        self.conn.close()
