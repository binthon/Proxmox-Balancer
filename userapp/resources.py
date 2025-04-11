from proxmox import getProxmoxVMIDs, getProxmoxResources, getProxmoxVMs
from azureVM import getAzureVMID, getAzureVM

def getResources():
    proxmoxData = getProxmoxResources()
    proxmoxID = getProxmoxVMIDs()
    azureID = getAzureVMID()

    IDS = proxmoxID + azureID
    lastID = max(IDS) if IDS else 100
    newID = lastID + 1

    proxmoxData["newID"] = newID
    return proxmoxData

def getAllUserVM(username):
    proxmox_vms = getProxmoxVMs(username)
    azure_vms = getAzureVM(username)
    if isinstance(proxmox_vms, dict) and "error" in proxmox_vms:
        proxmox_vms = []
    if isinstance(azure_vms, dict) and "error" in azure_vms:
        azure_vms = []
    return proxmox_vms + azure_vms
