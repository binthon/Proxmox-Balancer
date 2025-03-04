from azure.cosmos import CosmosClient
from werkzeug.security import generate_password_hash
import urllib3
from dotenv import load_dotenv
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = 'Proxmox'
CONTAINER_NAME = 'Users'


client = CosmosClient(COSMOS_URL, credential=COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)


def getUser(username):
    user = None
    for item in container.query_items(
            query="SELECT * FROM users WHERE users.username = @username",
            parameters=[{"name": "@username", "value": username}],
            enable_cross_partition_query=True):
        user = item
        break
    return user

def addUser(username, password, user_type):
    user = {
        'id': str(getNextID()),
        'userType': user_type,
        'username': username,
        'password': generate_password_hash(password)
    }
    container.upsert_item(user)
    return user

def getNextID():
    max_id = 0
    for item in container.query_items(
            query="SELECT VALUE users.id FROM users",
            enable_cross_partition_query=True):
        max_id = max(max_id, int(item))
    return max_id + 1
