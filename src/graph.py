from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import Config
from src.vector_store import VectorStoreManager
from src.memory import MemoryManager
from src.utils import setup_logger, remove_stopwords

logger = setup_logger(__name__)

class GraphState(TypedDict):
    question: str
    prescription_id: Optional[str] # None for Global, ID for Local
    session_id: str
    language: str # New field
    # history_summary: str # Removed
    context: List[str]
    answer: str

class RAGGraph:
    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.memory = MemoryManager()
        self.llm = ChatGoogleGenerativeAI(model=Config.GEMINI_MODEL_NAME, google_api_key=Config.GOOGLE_API_KEY)

    def retrieve(self, state: GraphState):
        """
        Retrieve relevant chunks from Pinecone.
        """
        logger.info("Node: Retrieve")
        question = state["question"]
        prescription_id = state.get("prescription_id")
        
        # Search Pinecone
        results = self.vector_store.search(question, prescription_id=prescription_id)
        
        # Extract text from results
        context = [match.metadata["text"] for match in results]
        
        return {"context": context}

    def generate(self, state: GraphState):
        """
        Generate answer using Gemini.
        """
        logger.info("Node: Generate")
        question = state["question"]
        context = state["context"]
        language = state.get("language", "English") # Default to English
        # summary = state["history_summary"] # Removed
        
        context_str = "\n\n".join(context)
        
        # Fetch History
        history = self.memory.get_history(state["session_id"], limit=5)
        # Apply stop word removal 
        history_str = "\n".join([f"{msg['role'].capitalize()}: {remove_stopwords(msg['content'])}" for msg in history])
        
        prompt = f"""
        You are a helpful medical assistant. Answer the user's question based on the provided context and chat history.
        
        IMPORTANT INSTRUCTIONS:
        1. Answer in the following language: {language}
        2. If the user asks about a medicine ("What is this for?"), provide TWO things:
           a) The specific instructions from the prescription (dosage, timing).
           b) General medical knowledge about what the medicine is commonly used for (e.g., "Paracetamol is commonly used for fever and pain relief").
        
        Context from Prescriptions:
        {context_str}
        
        Chat History:
        {history_str}
        
        User Question: {question}
        
        Answer:
        """
        
        response = self.llm.invoke(prompt)
        # Add to memory manually here since we removed the summarize node
        self.memory.add_message(state["session_id"], "user", question)
        self.memory.add_message(state["session_id"], "ai", response.content)
        
        return {"answer": response.content}

    def build_graph(self):
        """
        Builds the LangGraph workflow.
        """
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("generate", self.generate)
        
        # Define edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)
        
        return workflow.compile()

