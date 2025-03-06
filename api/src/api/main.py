import os
import json
import weaviate
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Retrieve credentials
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# FastAPI app
app = FastAPI()

# Initialize Weaviate client
if not WEAVIATE_URL or not WEAVIATE_API_KEY:
    raise ValueError("Missing WEAVIATE_URL or WEAVIATE_API_KEY environment variables.")

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=WEAVIATE_URL,
    auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
)

# Initialize OpenAI client
openai_client = ChatOpenAI(api_key=OPENAI_API_KEY)

# Define request model
class QueryRequest(BaseModel):
    user_query: str

@app.get("/")
def root():
    return {"message": "FastAPI is running!"}

@app.post("/query_services")
def query_services(request: QueryRequest):
    """
    Query Weaviate for relevant services based on user input
    """
    try:
        user_query = request.user_query
        
        # Step 1: Use OpenAI to refine the search query
        chat_response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an AI that refines search queries for a service database."},
                      {"role": "user", "content": f"Find relevant services for: {user_query}"}]
        )
        
        refined_query = chat_response.choices[0].message.content
        print(f"Refined query: {refined_query}")

        # Step 2: Query Weaviate for relevant services
        collection = client.collections.get("Services")
        response = collection.query.near_text(
            query=refined_query,
            limit=5  # Return top 5 results
        )

        if not response.objects:
            return {"message": "No relevant services found."}

        services = [{"name": obj.properties.get("name"), 
                     "description": obj.properties.get("description"), 
                     "link": obj.properties.get("link")} 
                    for obj in response.objects]

        return {"query": user_query, "refined_query": refined_query, "services": services}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run server with: uvicorn main:app --reload
