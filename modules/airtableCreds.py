from google.cloud import storage
import json
import tempfile


class AirtableCreds:
    def __init__(self,credentials_bucket:str,credentials_file:str):
        self.credentials_bucket = credentials_bucket
        self.credentials_file = credentials_file
        self.credentials = None
        self.client = None

    def download_credentials(self):
        # Initialize the storage client and get the bucket and blob objects
        storage_client = storage.Client()
        bucket = storage_client.bucket(self.credentials_bucket)
        blob = bucket.blob(self.credentials_file)

        # Create a temporary file to store the downloaded credentials
        temp_file = tempfile.NamedTemporaryFile()

        # Download the credentials file to the temporary file
        blob.download_to_filename(temp_file.name)

        # Read the contents of the temporary file
        with open(temp_file.name, 'r') as f:
            credentials_data = json.load(f)

        # Return the credentials data
        return credentials_data