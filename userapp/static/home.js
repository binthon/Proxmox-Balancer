function validateForm() {
    const vmid = document.getElementById('vmid').value.trim();
    const vmname = document.getElementById('vmname').value.trim();
    const memory = document.getElementById('memory').value.trim();
    const cores = document.getElementById('cores').value.trim();
    const disk = document.getElementById('disk').value.trim();
    const iso = document.getElementById('iso').value.trim();
    
    const networkRadios = document.querySelectorAll('input[name="network"]');
    const isNetworkSelected = Array.from(networkRadios).some(radio => radio.checked);

    

    const isValid = vmid !== '' && vmname !== `${username}-` && vmname !== `${username}` && memory !== '' &&
                    cores !== '' && disk !== '' && iso !== '' && isNetworkSelected;

    document.getElementById('create-button').disabled = !isValid;
}


document.addEventListener('DOMContentLoaded', () => {
    const user = username;  
    const vmNameField = document.getElementById('vmname');

    window.updateVMName = () => {
        const prefix = user;
        let currentValue = vmNameField.value;
        if (!currentValue.startsWith(prefix)) {
            vmNameField.value = prefix;
            return;
        }
        const suffix = currentValue.substring(prefix.length ); 

        if (suffix.length === 0) {
            vmNameField.value = prefix;
            return;
        }
        if (!suffix.startsWith('-')) {      
            vmNameField.value = prefix + '-' + suffix;
        }
    };
});

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".deleteButton").forEach(button => {
        button.addEventListener("click", function () {
            let vmID = this.getAttribute("data-vmid");

            if (!vmID) {
                alert("Error: VM ID not found!");
                return;
            }

            if (confirm(`Are you sure you want to delete VM ID: ${vmID}?`)) {
                fetch("/delete_vm", {  
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ vmid: vmID }) 
                })
                .then(response => response.json()) 
                .then(data => {
                    if (data.success) {
                        alert(data.success);
                        location.reload(); 
                    } else {
                        alert("Error: " + data.error);
                    }
                })
                .catch(error => console.error("Fetch error:", error));
            }
        });
    });
});
