document.addEventListener("DOMContentLoaded", () => {
    const listContainersBtn = document.getElementById("list-containers");
    const tableBody = document.querySelector("#container-table tbody");
    const startBtn = document.getElementById("start-container");
    const stopBtn = document.getElementById("stop-container");
    const startSelect = document.getElementById("start-container-select");
    const stopSelect = document.getElementById("stop-container-select");

    const updateTable = (data) => {
        // Clear the table body
        tableBody.innerHTML = "";
        for (const [service, status] of Object.entries(data)) {
            const row = document.createElement("tr");
            const serviceCell = document.createElement("td");
            const statusCell = document.createElement("td");

            serviceCell.textContent = service;
            statusCell.textContent = status;

            row.appendChild(serviceCell);
            row.appendChild(statusCell);
            tableBody.appendChild(row);
        }
    };

    listContainersBtn.addEventListener("click", () => {
        fetch("/containers")
            .then((response) => response.json())
            .then((data) => updateTable(data))
            .catch((error) => {
                tableBody.innerHTML = `<tr><td colspan="2">Error: ${error}</td></tr>`;
            });
    });

    startBtn.addEventListener("click", () => {
        const containerName = startSelect.value;
        fetch("/containers/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: containerName }),
        })
            .then((response) => response.json())
            .then((data) => alert(data.message))
            .catch((error) => alert(`Error: ${error}`));
    });

    stopBtn.addEventListener("click", () => {
        const containerName = stopSelect.value;
        fetch("/containers/stop", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: containerName }),
        })
            .then((response) => response.json())
            .then((data) => alert(data.message))
            .catch((error) => alert(`Error: ${error}`));
    });
});
