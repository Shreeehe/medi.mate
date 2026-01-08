import json
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import Config
from src.utils import setup_logger
from src.otc_data import OTC_LIST_DATA

logger = setup_logger(__name__)

class OTCManager:
    # Use the imported list
    OTC_LIST = OTC_LIST_DATA
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model=Config.GEMINI_MODEL_NAME, google_api_key=Config.GOOGLE_API_KEY)
        # Initialize Vector Store
        from src.vector_store import VectorStoreManager
        self.vector_store = VectorStoreManager()
        self.otc_namespace = "otc_medicines"
        self._initialize_otc_db()

    def _initialize_otc_db(self):
        """
        Ingests the OTC list into Pinecone if not already present.
        """
        try:
            # Check if namespace has stats (count > 0)
            # Pinecone stats might be expensive or slow to update, so we can just basic upsert
            # For simplicity, we just upsert every time on startup (idempotent)
            logger.info("Initializing OTC Vector DB...")
            
            # Use data from the class list or load from markdown if needed
            # For now, using the hardcoded list for reliability
            
            # Extract texts and metadatas from the list of dicts
            texts = [item['medicine_name'] for item in self.OTC_LIST]
            metadatas = []
            for item in self.OTC_LIST:
                meta = item.get('metadata', {}).copy()
                meta['source'] = 'general_otc_list'
                metadatas.append(meta)
            
            self.vector_store.add_texts(texts, metadatas, namespace=self.otc_namespace)
            logger.info("OTC List Ingested into Pinecone.")
            
        except Exception as e:
            logger.error(f"Failed to initialize OTC DB: {e}")

    def search_otc_db(self, query, top_k=10):
        """
        Searches the OTC vector database for similar medicines.
        """
        matches = self.vector_store.search(query, namespace=self.otc_namespace, top_k=top_k)
        results = []
        for m in matches:
             results.append({
                 "Medicine Name": m.metadata['text'],
                 "Type": m.metadata.get('type', 'Unknown'),
                 "Score": round(m.score, 2)
             })
        return results

    def get_otc_list(self):
        return self.OTC_LIST

    def check_medicines_with_llm(self, medicine_list):
        """
        Checks if the provided medicines are in the OTC list using Vector Search + LLM.
        """
        logger.info("Checking medicines against OTC list using Vector Search + LLM")
        
        results = {"otc_medicines": [], "consult_medicines": []}
        
        for med in medicine_list:
            # 1. Parse medicine name if it's a long string
            # The input might be a full line like "- Crocin (Qty: 10)..."
            # We trust the LLM/Extractor gave us decent strings, but let's just use the whole string for search
            med_str = str(med)
            
            # 2. Vector Search for candidates
            matches = self.vector_store.search(med_str, namespace=self.otc_namespace, top_k=3)
            candidates = [m.metadata['text'] for m in matches if m.score > 0.7] # Threshold
            
            if not candidates:
                 # No close semantic match found -> Consult
                 results["consult_medicines"].append({
                     "name": med_str.split('(')[0], # Simple cleanup
                     "reason": "No matching approved OTC medicine found in database."
                 })
                 continue
            
            # 3. LLM Verification
            # We ask the LLM: "Is [Medicine] equivalent to any of these [Candidates]?"
            candidates_str = "\n".join(candidates)
            
            prompt = f"""
            You are a medical assistant. Verify if the extracted medicine is strictly equivalent to any of the allowed OTC candidates found.

            Extracted Medicine: "{med_str}"

            Allowed OTC Candidates (from database):
            {candidates_str}

            Instructions:
            1. Determine if the 'Extracted Medicine' matches any 'Allowed OTC Candidate' (Brand or Generic).
            2. Match must be safe and exact (e.g., "Crocin" matches "Paracetamol").
            3. Return JSON.

            Output Format:
            {{
                "is_otc": true/false,
                "matched_candidate": "Name of matched OTC item" or null,
                "reason": "Brief explanation"
            }}
            """
            
            try:
                response = self.llm.invoke(prompt)
                content = response.content.replace("```json", "").replace("```", "").strip()
                verification = json.loads(content)
                
                name_clean = med_str.split(':')[0].strip("- ").strip()
                
                if verification.get("is_otc"):
                    results["otc_medicines"].append({
                        "name": name_clean,
                        "reason": f"Matched with {verification.get('matched_candidate')}"
                    })
                else:
                    results["consult_medicines"].append({
                        "name": name_clean,
                        "reason": verification.get("reason", "Not a valid match with allowed list")
                    })
                    
            except Exception as e:
                logger.error(f"Error checking medicine {med_str}: {e}")
                results["consult_medicines"].append({"name": med_str, "reason": "Error verifying safety"})

        return results
