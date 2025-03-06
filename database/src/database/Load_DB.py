import os
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure
import json

from dotenv import load_dotenv

# Initialisation du LLM avec l'API key
load_dotenv()

def main():
    print("Hello from the database service!")
    #Retrieve credentials from environment variables
    weaviate_url = os.getenv("WEAVIATE_URL")
    weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
    
    if not weaviate_url or not weaviate_api_key:
        raise ValueError("Missing WEAVIATE_URL or WEAVIATE_API_KEY environment variables.")
    
    # Connect to Weaviate Cloud
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )
    
    # Check if the connection is successful
    if client.is_ready():
        print("Connected to Weaviate Cloud successfully!")
    else:
        print("Failed to connect to Weaviate Cloud.")

    # Create a new schema
    if not client.collections.exists("Services"):
        print("Creating a new schema...")
        services = client.collections.create(
            name="Services",
            vectorizer_config=Configure.Vectorizer.text2vec_weaviate(), # Configure the Weaviate Embeddings integration
            generative_config=Configure.Generative.cohere()             # Configure the Cohere generative AI integration
        )


    # Populate
    print("Trying to load data.json...")
    try:
        with open("/home/olivier/projet/github-hackaton/database/src/database/data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            print("Data loaded successfully!")

        # Populate Weaviate with data
        with services.batch.dynamic() as batch:
            for d in data:
                print(f"Adding object: {d.get('name')}")
                batch.add_object({
                    "name": d.get("name"),
                    "description": d.get("description"),
                    "link": d.get("link"),
                })

        response = services.query.near_text(
            query="Fire",
            limit=2
        )
        client.close()

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading data.json: {e}")
        client.close()
        return
    
    client.close()

if __name__ == "__main__":
    main()
