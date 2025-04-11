from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
import os

SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
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

