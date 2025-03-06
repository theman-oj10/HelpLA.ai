import os
import weaviate
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from weaviate.classes.init import Auth
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Retrieve credentials
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"WEAVIATE_URL: {WEAVIATE_URL}")
print(f"WEAVIATE_API_KEY: {WEAVIATE_API_KEY}")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")

class Service(BaseModel):
    """Service for help"""

    name: str = Field(..., description="Name of the service")
    description: str = Field(..., description="Description of the service")
    link: str = Field(..., description="Link to URL")


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
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)

# Define prompt templates
prompt_refine_query = PromptTemplate(
    input_variables=["user_query"],
    template="""
    You are an AI that refines search queries for a service database.
    Given the user query: "{user_query}", provide a refined search query.
    Explain what services you found and present them to the user with a link.
    """
)

prompt_organize_services = PromptTemplate(
    input_variables=["services"],
    template="""
    You are an AI that organizes service information in a user-friendly format.
    
    Given the following list of services:
    {services}

    Format them in a clear and structured way that is easy for the user to read.
    """
)

@app.get("/")
def root():
    return {"message": "FastAPI is running!"}

@app.post("/query_services")
def query_services(request):
    """
    Query Weaviate for relevant services based on user input
    """
    try:
        user_query = request.user_query

        # Step 1: Use OpenAI to refine the search query
        chain_refine = prompt_refine_query | llm
        refined_response = chain_refine.invoke({"user_query": user_query})
        refined_query = refined_response.refined_query

        print(f"Refined query: {refined_query}")

        # Step 2: Query Weaviate for relevant services
        collection = client.collections.get("Services")
        response = collection.query.near_text(
            query=refined_query,
            limit=5  # Return top 5 results
        )

        if not response.objects:
            return {"message": "No relevant services found."}

        services = [Service(
            name=obj.properties.get("name"),
            description=obj.properties.get("description"),
            link=obj.properties.get("link")
        ) for obj in response.objects]

        # Step 3: Organize services in a user-friendly format
        chain_organize = prompt_organize_services | llm
        organized_response = chain_organize.invoke({"services": [s.dict() for s in services]})
        print(f"Organized response: {organized_response}")
        print(f"Services")

        return {"query": user_query, "refined_query": refined_query, "response": organized_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run server with: uvicorn main:app --reload
