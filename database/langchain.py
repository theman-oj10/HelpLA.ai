from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.chains import RetrievalQA
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Check for OpenAI API Key
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY not found. Please set this environment variable.")

# Global variable to store our initialized RAG pipeline
qa_chain = None
documents_processed = False

# Path to your knowledge base documents
DOCS_DIRECTORY = "knowledge_base"

def initialize_rag_pipeline():
    """Initialize the RAG pipeline with documents from the knowledge base."""
    global qa_chain, documents_processed
    
    try:
        # Check if knowledge base directory exists, create if not
        if not os.path.exists(DOCS_DIRECTORY):
            os.makedirs(DOCS_DIRECTORY)
            logger.warning(f"Created empty knowledge base directory: {DOCS_DIRECTORY}")
            # Create a sample document if no documents exist
            with open(os.path.join(DOCS_DIRECTORY, "sample_info.txt"), "w") as f:
                f.write("This is sample information about LA wildfire recovery resources.\n")
                f.write("FEMA provides assistance for temporary housing and home repairs.\n")
                f.write("The Red Cross offers emergency shelter and supplies.\n")
                f.write("Insurance claims should be filed as soon as possible with documentation of damages.\n")
        
        # Load documents from the directory
        logger.info(f"Loading documents from {DOCS_DIRECTORY}")
        loader = DirectoryLoader(DOCS_DIRECTORY, glob="**/*.txt", loader_cls=TextLoader)
        documents = loader.load()
        
        if not documents:
            logger.warning("No documents found in the knowledge base directory.")
            return False
            
        logger.info(f"Loaded {len(documents)} documents")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        logger.info(f"Split into {len(texts)} chunks")
        
        # Create vector store
        embeddings = OpenAIEmbeddings()
        db = Chroma.from_documents(documents=texts, embedding=embeddings)
        
        # Create retriever
        retriever = db.as_retriever(search_kwargs={"k": 3})
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(temperature=0.2),
            chain_type="stuff",
            retriever=retriever,
        )
        
        documents_processed = True
        logger.info("RAG pipeline initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing RAG pipeline: {str(e)}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint to check if the API is running."""
    return jsonify({"status": "healthy", "rag_initialized": documents_processed})

@app.route('/api/query', methods=['POST'])
def query():
    """Endpoint to process user queries through the RAG pipeline."""
    global qa_chain, documents_processed
    
    # Initialize RAG pipeline if not done already
    if not documents_processed:
        success = initialize_rag_pipeline()
        if not success:
            return jsonify({
                "error": "Failed to initialize RAG pipeline. Check server logs for details.",
                "response": "I'm having trouble accessing my knowledge base. Please try again later."
            }), 500
    
    # Get query from request
    data = request.json
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    user_query = data['query']
    logger.info(f"Received query: {user_query}")
    
    try:
        # Get enhanced context if available (optional)
        context = data.get('context', '')
        
        # Enhance query with context if provided
        enhanced_query = user_query
        if context:
            enhanced_query = f"Context: {context}\nQuery: {user_query}"
            
        # Process query through RAG pipeline
        response = qa_chain.invoke({"query": enhanced_query})
        
        # Extract source documents
        source_docs = []
        if hasattr(response, 'source_documents'):
            for doc in response.source_documents:
                source_docs.append({
                    "content": doc.page_content[:200] + "...",  # Preview of content
                    "source": doc.metadata.get("source", "Unknown")
                })
        
        # Prepare response
        result = {
            "response": response["result"] if isinstance(response, dict) else str(response),
            "sources": source_docs,
            "query": user_query
        }
        
        logger.info(f"Returning response for query: {user_query}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            "error": str(e),
            "response": "I encountered an error while processing your request. Please try again."
        }), 500

@app.route('/api/add-document', methods=['POST'])
def add_document():
    """Endpoint to add a new document to the knowledge base."""
    try:
        data = request.json
        if not data or 'content' not in data or 'filename' not in data:
            return jsonify({"error": "Content and filename are required"}), 400
            
        content = data['content']
        filename = data['filename']
        
        # Ensure filename has .txt extension
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        # Ensure directory exists
        if not os.path.exists(DOCS_DIRECTORY):
            os.makedirs(DOCS_DIRECTORY)
        
        # Write content to file
        file_path = os.path.join(DOCS_DIRECTORY, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Reinitialize RAG pipeline with new document
        global documents_processed
        documents_processed = False  # Force reinitialization
        initialize_rag_pipeline()
        
        return jsonify({"status": "success", "message": f"Document {filename} added successfully"})
        
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize RAG pipeline on startup
    initialize_rag_pipeline()
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)