from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from src.config import Config
from src.utils import setup_logger
import time

logger = setup_logger(__name__)

class VectorStoreManager:
    """
    Manages interactions with Pinecone Vector DB.
    """
    def __init__(self):
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.index_name = Config.PINECONE_INDEX_NAME
        
        # Initialize Embeddings
        if Config.GOOGLE_API_KEY:
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=Config.GOOGLE_API_KEY)
        else:
            logger.warning("Google API Key missing for embeddings.")
            self.embeddings = None

        self._ensure_index()
        self.index = self.pc.Index(self.index_name)

    def _ensure_index(self):
        """Creates the index if it doesn't exist."""
        if self.index_name not in self.pc.list_indexes().names():
            logger.info(f"Creating Pinecone index: {self.index_name}")
            try:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=768,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=Config.PINECONE_ENV
                    )
                )
                time.sleep(5) # Wait for initialization
            except Exception as e:
                logger.error(f"Failed to create index: {e}")
                pass

    def add_texts(self, texts, metadata_list, namespace=None):
        """
        Generic method to add texts to Pinecone.
        """
        if not self.embeddings:
            return False

        vectors = []
        for i, text in enumerate(texts):
            # Create a unique ID based on hash or index + namespace
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            vector_id = f"{namespace}_{text_hash}" if namespace else f"{text_hash}"
            
            embedding = self.embeddings.embed_query(text)
            
            meta = metadata_list[i].copy() if i < len(metadata_list) else {}
            meta["text"] = text
            
            vectors.append((vector_id, embedding, meta))

        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            self.index.upsert(vectors=batch, namespace=namespace)
        
        logger.info(f"Stored {len(vectors)} texts in namespace '{namespace}'")
        return True

    def add_prescription(self, prescription_id, text_chunks, metadata):
        """
        Embeds and stores prescription chunks.
        """
        if not self.embeddings:
            return False

        vectors = []
        for i, chunk in enumerate(text_chunks):
            vector_id = f"{prescription_id}_{i}"
            embedding = self.embeddings.embed_query(chunk)
            
            # Combine chunk metadata with global metadata
            chunk_metadata = metadata.copy()
            chunk_metadata["text"] = chunk
            chunk_metadata["chunk_id"] = i
            chunk_metadata["prescription_id"] = prescription_id
            
            vectors.append((vector_id, embedding, chunk_metadata))

        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            self.index.upsert(vectors=batch)
        
        logger.info(f"Stored {len(vectors)} chunks for prescription {prescription_id}")
        return True

    def search(self, query, prescription_id=None, namespace=None, top_k=5):
        """
        Searches for relevant chunks.
        If prescription_id is provided, filters by that ID (Local Search).
        Otherwise, searches globally or in a specific namespace.
        """
        if not self.embeddings:
            return []

        query_embedding = self.embeddings.embed_query(query)
        
        filter_dict = {}
        if prescription_id:
            filter_dict = {"prescription_id": {"$eq": prescription_id}}

        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict if prescription_id else None,
            namespace=namespace
        )
        
        return results.matches
