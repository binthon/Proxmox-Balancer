import requests
from collections import OrderedDict
import urllib3
import time
from dotenv import load_dotenv
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()
PROXMOX_URL = os.getenv("PROXMOX_URL")
API_TOKEN = os.getenv("API_TOKEN")
HEADERS = {"Authorization": API_TOKEN}
NODE = "proxmox"  

def getResources():
    url = f"{PROXMOX_URL}/cluster/resources"
    try:
        response = requests.get(url, headers=HEADERS, verify=False)
        response.raise_for_status()
        data = response.json().get("data", [])

        nodes = [item for item in data if item["type"] == "node"]
        storages = [item for item in data if item["type"] == "storage" and "images" in item.get("content", "")]
        vimID = [item for item in data if item.get('type') in ['qemu', 'lxc']]
        lastID = max(vm['vmid'] for vm in vimID) if vimID else 0
        newID = lastID + 100
        
        totalRAM = sum(node.get("maxmem", 0) for node in nodes)
        usedRAM = sum(node.get("mem", 0) for node in nodes)
        freeRam  = totalRAM - usedRAM

        totalCPU = sum(node.get("maxcpu", 0) for node in nodes)
        usedCPU = sum(node.get("cpu", 0) * node.get("maxcpu", 0) for node in nodes)
        actualUsedCores = round(usedCPU * totalCPU,2)
        freeCPU = totalCPU - actualUsedCores

        totalDisk = sum(storage.get("maxdisk", 0) for storage in storages)
        usedDisk = sum(storage.get("disk", 0) for storage in storages)
        freeDisk = totalDisk - usedDisk



        return OrderedDict([
            ("usedCPU", round(usedCPU, 4)),
            ("realUsedCPU", actualUsedCores),
            ("freeCPU", freeCPU),
            ("totalCPU", totalCPU),
            ("usedDisk", usedDisk // (1024 * 1024 * 1024)),
            ("totalDisk", totalDisk // (1024 * 1024 * 1024)),
            ("freeDisk", freeDisk // (1024 * 1024 * 1024)),
            ("usedRam", usedRAM // (1024 * 1024)), 
            ("totalRam", totalRAM // (1024 * 1024)),
            ("freeRam", freeRam // (1024 * 1024)),
            ("newID", newID)  
        ])

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def getUserVM(username):
    url = f"{PROXMOX_URL}/cluster/resources"
    try:
        response = requests.get(url, headers=HEADERS, verify=False)
        response.raise_for_status()
        data = response.json().get("data", [])

        userVMS = []
        for item in data:
            if item.get("type") in ("qemu", "lxc"):
                vmName = item.get("name", "")
                vmID = item.get("vmid", "")
                vmType = item.get("type","")
                if vmName.startswith(f"{username}-"):
                    userVMS.append({
                        "ID": vmID,
                        "name": vmName,
                        "type": vmType
                    })

        return userVMS
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}
    

def getISONetwork():
    isoURL = f"{PROXMOX_URL}/nodes/{NODE}/storage/local/content"
    networkURL = f"{PROXMOX_URL}/nodes/{NODE}/network"

    try:
        isoRes = requests.get(isoURL, headers=HEADERS, verify=False)
        isoRes.raise_for_status()
        data = isoRes.json().get("data", [])
        isoFiles = [item.get("volid", "") for item in data if item.get("content") == "iso"]

        networkRes = requests.get(networkURL, headers=HEADERS, verify=False)
        networkRes.raise_for_status()
        netData = networkRes.json().get("data", [])
        networks = [net["iface"] for net in netData if net.get("type") == "bridge"]

        return {"isoFiles": isoFiles, "networks": networks}

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def createDisk(vmid, storage, size):
    url = f"{PROXMOX_URL}/nodes/{NODE}/storage/{storage}/content"
    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "vmid": vmid,
        "size": f"{size}G",
        "filename": f"vm-{vmid}-disk-0"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, verify=False)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to create disk: {str(e)} - Response: {response.text}"}

def startVm(vmid):
    urlStart = f"{PROXMOX_URL}/nodes/{NODE}/qemu/{vmid}/status/start"
    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(urlStart, headers=headers, json={}, verify=False)  
        response.raise_for_status()
        return True  
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to start VM: {str(e)} - Response: {response.text}"}


def createVM(vmid, vmname, memory, cores, disk, iso, network):
    vmStorage = "local-lvm"  
    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }

    diskCreation = createDisk(vmid, vmStorage, disk)
    if isinstance(diskCreation, dict) and "error" in diskCreation:
        return diskCreation  

    vmData = {
        "vmid": vmid,
        "name": vmname,
        "memory": memory,
        "cores": cores,
        "sockets": 1,
        "net0": f"virtio,bridge={network}",
        "ide2": f"{iso},media=cdrom",
        "ostype": "l26",  
        "scsihw": "virtio-scsi-pci",
        "boot": "order=scsi0;ide2;net0",
        "scsi0": f"{vmStorage}:vm-{vmid}-disk-0",  
        "onboot": 1,
        "kvm": 0  
    }

    urlVM = f"{PROXMOX_URL}/nodes/{NODE}/qemu"
    urlStatus = f"{PROXMOX_URL}/nodes/{NODE}/qemu/{vmid}/status/current"

    try:
        response = requests.post(urlVM, headers=headers, json=vmData, verify=False)
        response.raise_for_status()

        for _ in range(6):
            time.sleep(5)
            status_response = requests.get(urlStatus, headers=headers, verify=False)
            status_response.raise_for_status()
            vm_status = status_response.json().get("data", {}).get("status", "")

            if vm_status == "stopped":
                break

        startResult = startVm(vmid)
        if isinstance(startResult, dict) and "error" in startResult:
            return startResult  

        return {"success": f"Linux VM {vmname} (ID: {vmid}) created and started successfully!"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to create/start VM: {str(e)} - Response: {response.text}"}


def deleteVM(vmid):
    urlStop = f"{PROXMOX_URL}/nodes/{NODE}/qemu/{vmid}/status/stop"
    urlDelete = f"{PROXMOX_URL}/nodes/{NODE}/qemu/{vmid}"

    try:
        urlStatus = f"{PROXMOX_URL}/nodes/{NODE}/qemu/{vmid}/status/current"
        response = requests.get(urlStatus, headers=HEADERS, verify=False)
        response.raise_for_status()
        vmStatus = response.json().get("data", {}).get("status", "")

        if vmStatus == "running":
            stopResponse = requests.post(urlStop, headers=HEADERS, json={}, verify=False)
            stopResponse.raise_for_status()

            for _ in range(10): 
                time.sleep(3)
                response = requests.get(urlStatus, headers=HEADERS, verify=False)
                response.raise_for_status()
                vmStatus = response.json().get("data", {}).get("status", "")

                if vmStatus == "stopped":
                    break
            else:
                return {"error": f"VM {vmid} did not stop in time"}

        deleteResponse = requests.delete(urlDelete, headers=HEADERS, verify=False)
        deleteResponse.raise_for_status()
        return {"success": f"VM {vmid} deleted successfully"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to delete VM {vmid}: {str(e)}"}
