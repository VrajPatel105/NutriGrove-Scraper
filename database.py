import json
import os
from dotenv import load_dotenv
from supabase import create_client, Client

class SupabaseUploader:
    def __init__(self, database_name="cleaned_data"):
        load_dotenv()

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            print("Error: Missing Supabase credentials in .env file")
            exit()

        self.supabase = create_client(url, key)
        self.database_name = database_name
    
    def upload_json_file(self, file_path):
        # Load your cleaned JSON data
        with open(file_path, 'r') as f:
            data = json.load(f)

        # If your data is a list of objects, insert each one
        if isinstance(data, list):
            for item in data:
                result = self.supabase.table(self.database_name).insert({"data": item}).execute()
                print(f"Inserted record with ID: {result.data[0]['id']}")

        # If your data is a single object, insert it
        else:
            result = self.supabase.table(self.database_name).insert({"data": data}).execute()
            print(f"Inserted record with ID: {result.data[0]['id']}")