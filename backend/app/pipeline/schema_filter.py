import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from app.database.schema_extractor import SchemaExtractor

class SchemaFilter:
    def __init__(self, schema_extractor: SchemaExtractor):
        self.schema_extractor = schema_extractor
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = None
        self.table_names = []
        self._build_index()

    def _build_index(self):
        descriptions = self.schema_extractor.get_table_descriptions()
        if not descriptions:
            return
            
        self.table_names = [d.table_name for d in descriptions]
        texts = [d.description for d in descriptions]
        
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        dimension = embeddings.shape[1]
        
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(np.array(embeddings))

    def get_relevant_tables(self, question: str, top_k: int = 6, threshold: float = None) -> list[str]:
        if not self.index:
            return self.table_names
            
        query_embedding = self.model.encode([question], normalize_embeddings=True)
        scores, indices = self.index.search(np.array(query_embedding), top_k)
        
        relevant_tables = []
        for score, idx in zip(scores[0], indices[0]):
            if threshold is None or score >= threshold:
                relevant_tables.append(self.table_names[idx])
                
        if not relevant_tables:
            return self.table_names  # fallback
            
        return relevant_tables

    def format_schema_for_prompt(self, relevant_tables: list[str]) -> tuple[str, str, str]:
        context = self.schema_extractor.get_schema_context()
        
        schema_dict = {t: context.tables.get(t) for t in relevant_tables if t in context.tables}
        schema_context = json.dumps(schema_dict, indent=2)
        
        rel_dict = {t: context.relationships.get(t) for t in relevant_tables if t in context.relationships}
        relationships = json.dumps(rel_dict, indent=2)
        
        val_dict = {t: context.sample_values.get(t) for t in relevant_tables if t in context.sample_values}
        sample_values = json.dumps(val_dict, indent=2)
        
        return schema_context, relationships, sample_values
