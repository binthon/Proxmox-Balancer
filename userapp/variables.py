import json

def generateTfvars(vmid, username, vmname, memory, cores, disk):
    tfvars = {
        "resource_group": "Proxmox",
        "location": "eu-north",
        "username": username,
        "vmid": str(vmid),
        "vm_name": vmname,
        "vm_ram": memory,
        "vm_cores": cores,
        "vm_disk": disk
    }
    with open("infra/terraform.tfvars.json", "w") as f:
        json.dump(tfvars, f)
