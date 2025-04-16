import json
import os
# === Generowanie zmienny pod terraform ===
def generateTfvars(vmid, username, vmname, memory, cores, disk):
    tfvars = {
        "resource_group": "Proxmox",
        "location": "eu-north",
        "username": username,
        "vmid": str(vmid),
        "vm_name": vmname,
        "vm_ram": memory,
        "vm_cores": cores,
        "vm_disk": disk,
        "admin_username": os.getenv("TF_ADMIN_USERNAME"),
        "admin_password": os.getenv("TF_ADMIN_PASSWORD"),

        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "client_secret": os.getenv("AZURE_CLIENT_SECRET"),
        "tenant_id": os.getenv("AZURE_TENANT_ID"),
        "subscription_id": os.getenv("AZURE_SUBSCRIPTION_ID")
    }

    with open("../infra/terraform.tfvars.json", "w") as f:
        json.dump(tfvars, f, indent=2)
        f.flush()
        os.fsync(f.fileno())


