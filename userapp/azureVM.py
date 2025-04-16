from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
AZUREDEVOPS_ORG = os.getenv("AZDO_ORG")               
AZUREDEVOPS_PROJECT = os.getenv("AZDO_PROJECT")       
AZUREDEVOPS_PIPELINE_ID = os.getenv("AZDO_PIPELINE_ID")  
AZUREDEVOPS_PAT = os.getenv("AZDO_PAT")               
credential = DefaultAzureCredential()
compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

# === Maszyny wraz z tagiem określającym ID ===
def getAzureVM(username):
    vms = []
    for vm in compute_client.virtual_machines.list_all():
        vmName = vm.name
        tags = vm.tags or {}

        if vmName.startswith(f"{username}-"):
            try:
                vmid = int(tags.get(username, "n/a"))  
            except (ValueError, IndexError):
                vmid = "n/a"

            vm_info = {
                "ID": vmid,     
                "name": vmName,    
                "type": "azure"
            }
            vms.append(vm_info)
    return vms

# === Pobieranie ID żeby dynamicznie dawał +1 dla następnej maszyny ===
def getAzureVMID():
    ids = []
    for vm in compute_client.virtual_machines.list_all():
        tags = vm.tags or {}
        for value in tags.values():
            try:
                ids.append(int(value))
            except (ValueError, TypeError):
                continue
    return ids


def triggerPipeline(tfvars_path="../infra/terraform.tfvars.json"):
    url = f"https://dev.azure.com/{AZUREDEVOPS_ORG}/{AZUREDEVOPS_PROJECT}/_apis/pipelines/{AZUREDEVOPS_PIPELINE_ID}/runs?api-version=7.0"

    pat_bytes = f":{AZUREDEVOPS_PAT}".encode("utf-8")
    auth_header = base64.b64encode(pat_bytes).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_header}"
    }

    with open(tfvars_path, "r") as f:
        tfvars_content = f.read()

    payload = {
        "resources": {
            "repositories": {
                "self": {
                    "refName": "refs/heads/main"
                }
            }
        },
        "templateParameters": {
        "tfvarsContent": tfvars_content  
    }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)

    try:
        response.raise_for_status()
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e), "details": response.text}

