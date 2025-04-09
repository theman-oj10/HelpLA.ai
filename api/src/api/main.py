import os
import weaviate
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from weaviate.classes.init import Auth
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from fastapi.middleware.cors import CORSMiddleware
# Load environment variables
load_dotenv()

# Retrieve credentials
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

print(f"WEAVIATE_URL: {WEAVIATE_URL}")
print(f"WEAVIATE_API_KEY: {WEAVIATE_API_KEY[:5]}..." if WEAVIATE_API_KEY else "None")
print(f"OPENAI_API_KEY: {OPENAI_API_KEY[:5]}..." if OPENAI_API_KEY else "None")

# Define models
class Service(BaseModel):
    name: str
    description: str
    link: str

class QueryRequest(BaseModel):
    user_query: str

class ServiceResponse(BaseModel):
    formatted_response: str
    services: list[Service] = []

# FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Weaviate client
def get_weaviate_client():
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
    )
    try:
        yield client
    finally:
        client.close()

# Initialize OpenAI client
llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0.2)

# Sample data model for bulk import
class BulkServiceImport(BaseModel):
    services: list[Service]

# Endpoints
@app.get("/")
def root():
    return {"message": "FastAPI is running!"}

@app.post("/query_services")
async def query_services(
    request: QueryRequest, 
    client: weaviate.WeaviateClient = Depends(get_weaviate_client)
):
    """
    Query Weaviate for relevant services based on user input
    """
    try:
        user_query = request.user_query
        print(f"Processing query: {user_query}")
        
        # Get the Services collection
        try:
            collection = client.collections.get("Services")
        except Exception as e:
            print(f"Error accessing Services collection: {str(e)}")
            # If collection doesn't exist, return a helpful message
            formatted_response = "Sorry, our services database is not available. Please try again later or contact support."
            return ServiceResponse(
                formatted_response=formatted_response,
                services=[]
            )
        
        # Query Weaviate with enhanced options
        response = collection.query.near_text(
            query=user_query,
            limit=3,
            certainty=0.5  # Lower certainty threshold to get more matches
        )
        
        # Print raw response for debugging
        print(f"Found {len(response.objects) if response.objects else 0} services")
        for i, obj in enumerate(response.objects or []):
            print(f"Service {i+1}: {obj.properties.get('name')}")
        
        # Process results
        if not response.objects:
            # No results found in Weaviate
            prompt = ChatPromptTemplate.from_template(
                "The user asked about: '{query}'\n\n"
                "We don't have specific services in our database for this query.\n"
                "Provide a helpful response explaining we don't have matching services "
                "and ask for more details about what they're looking for."
            )
            chain = prompt | llm
            formatted_response = chain.invoke({"query": user_query}).content
            
            return ServiceResponse(
                formatted_response=formatted_response,
                services=[]
            )
        else:
            # Extract services from Weaviate response
            services = []
            services_text = ""
            
            for obj in response.objects:
                service = Service(
                    name=obj.properties.get("name", "Unknown Service"),
                    description=obj.properties.get("description", "No description available"),
                    link=obj.properties.get("link", "#")
                )
                services.append(service)
                services_text += f"- {service.name}: {service.description} (Link: {service.link})\n"
        
            # Generate response with very specific instructions to include links
            prompt = ChatPromptTemplate.from_template(
                "You are a customer service assistant for a disaster recovery and assistance platform.\n\n"
                "User query: '{query}'\n\n"
                "Based on this query, we found these relevant services:\n"
                "{services_text}\n\n"
                "Instructions (FOLLOW THESE EXACTLY):\n"
                "1. Start by saying 'Based on your query about {query}, I found several services that can help.'\n"
                "2. Then list EACH service by name and explain specifically how it addresses their needs\n"
                "3. For EACH service, mention its link using the exact URLs included above\n"
                "4. Mention EVERY service by its EXACT name as provided above\n"
                "5. Be conversational but focused on the specific services\n"
                "6. Do not invent any services not listed above\n\n"
                "Your response:"
            )
            
            chain = prompt | llm
            formatted_response = chain.invoke({
                "query": user_query,
                "services_text": services_text
            }).content
            
            return ServiceResponse(
                formatted_response=formatted_response,
                services=services
            )

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add data management endpoint (no hardcoded data)
@app.post("/add_service")
async def add_service(
    service: Service,
    client: weaviate.WeaviateClient = Depends(get_weaviate_client)
):
    try:
        # Ensure the collection exists
        try:
            collection = client.collections.get("Services")
        except:
            collection = client.collections.create(
                name="Services",
                properties=[
                    {"name": "name", "dataType": ["text"]},
                    {"name": "description", "dataType": ["text"]},
                    {"name": "link", "dataType": ["text"]}
                ]
            )
            print("Created Services collection")
        
        # Add the service to Weaviate
        service_data = {
            "name": service.name,
            "description": service.description,
            "link": service.link
        }
        
        result = collection.data.insert(service_data)
        
        return {
            "status": "success",
            "message": f"Added service: {service.name}",
            "id": result
        }
        
    except Exception as e:
        print(f"Error adding service: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get all services endpoint
@app.get("/list_services")
async def list_services(
    client: weaviate.WeaviateClient = Depends(get_weaviate_client)
):
    try:
        # Get the Services collection
        try:
            collection = client.collections.get("Services")
        except Exception as e:
            print(f"Error accessing Services collection: {str(e)}")
            return {"status": "error", "message": "Services collection does not exist", "services": []}
        
        # Fetch all services
        results = collection.query.fetch_objects(limit=100)
        
        services = []
        for obj in results.objects:
            service = {
                "name": obj.properties.get("name", "Unknown Service"),
                "description": obj.properties.get("description", "No description available"),
                "link": obj.properties.get("link", "#"),
                "id": obj.uuid
            }
            services.append(service)
        
        return {
            "status": "success",
            "message": f"Found {len(services)} services",
            "services": services
        }
        
    except Exception as e:
        print(f"Error listing services: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete service endpoint
@app.delete("/delete_service/{service_id}")
async def delete_service(
    service_id: str,
    client: weaviate.WeaviateClient = Depends(get_weaviate_client)
):
    try:
        # Get the Services collection
        try:
            collection = client.collections.get("Services")
        except Exception as e:
            print(f"Error accessing Services collection: {str(e)}")
            raise HTTPException(status_code=404, detail="Services collection does not exist")
        
        # Delete the service
        try:
            collection.data.delete_by_id(service_id)
            return {"status": "success", "message": f"Deleted service with ID: {service_id}"}
        except Exception as e:
            print(f"Error deleting service: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Service with ID {service_id} not found")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))