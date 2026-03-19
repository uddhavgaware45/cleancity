let map = L.map('map').setView([19.0760, 72.8777], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

let marker;

// Click map to select location
map.on('click', function(e) {
    if (marker) map.removeLayer(marker);
    marker = L.marker(e.latlng).addTo(map);

    document.getElementById("lat").value = e.latlng.lat;
    document.getElementById("lng").value = e.latlng.lng;
});

// Submit form
document.getElementById("reportForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();

    let formData = new FormData(e.target);

    await fetch('/report', {
        method: 'POST',
        body: formData
    });

    alert("Issue Reported!");
    loadIssues();
});

// Load issues
async function loadIssues() {
    let res = await fetch('/issues');
    let data = await res.json();

    let html = "";

    data.forEach(i => {
        html += `
        <div class="card">
            <h3>${i.category}</h3>
            <p>${i.description}</p>
            <img src="/uploads/${i.image}" width="100%">
            <p>👍 ${i.votes} | Status: ${i.status || "pending"}</p>
            <button onclick="upvote(${i.id})">Upvote</button>
        </div>
        `;

        if(i.lat && i.lng){
            L.marker([i.lat, i.lng])
            .addTo(map)
            .bindPopup(`<b>${i.category}</b><br>${i.description}`);
        }
    });

    document.getElementById("issues").innerHTML = html;
}

// Upvote
async function upvote(id) {
    await fetch('/upvote/' + id, { method: 'POST' });
    loadIssues();
}

// Load on start
loadIssues();