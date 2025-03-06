import os
import weaviate
from weaviate.classes.init import Auth
from dotenv import load_dotenv

# Initialisation du LLM avec l'API key
load_dotenv()

def main():
    print("Hello from the database service!")
    # Retrieve credentials from environment variables
    # weaviate_url = os.getenv("WEAVIATE_URL")
    # weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    
    # if not weaviate_url or not weaviate_api_key:
    #     raise ValueError("Missing WEAVIATE_URL or WEAVIATE_API_KEY environment variables.")
    
    # # Connect to Weaviate Cloud
    # client = weaviate.connect_to_weaviate_cloud(
    #     cluster_url=weaviate_url,
    #     auth_credentials=Auth.api_key(weaviate_api_key),
    # )
    
    # # Check if the connection is successful
    # if client.is_ready():
    #     print("Connected to Weaviate Cloud successfully!")
    # else:
    #     print("Failed to connect to Weaviate Cloud.")

if __name__ == "__main__":
    main()
