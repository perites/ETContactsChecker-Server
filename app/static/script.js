let editingId = null;

async function loadContracts() {
    const res = await fetch('/api/contracts');
    const contracts = await res.json();
    const list = document.getElementById('contractsList');
    list.innerHTML = '';

    if (contracts.length === 0) {
        list.innerHTML = `<p style="text-align:center;">No contracts found</p>`;
        return;
    }

    for (const c of contracts) {
        const used = c.contacts_amount || 0;
        const limit = c.contacts_limit || 0;
        const percent = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
        const color = percent < 70 ? '#4CAF50' : percent < 90 ? '#FFC107' : '#e74c3c';
        const reached = limit > 0 && used >= limit;

        const item = document.createElement('div');
        item.className = 'contract-item' + (reached ? ' limit-reached' : '');
        item.innerHTML = `
            <div class="contract-top">
                <div class="contract-name">${c.name}</div>
                <div class="contract-icons">
                    ${editIcon(`editContract(${JSON.stringify(c).replace(/"/g, '&quot;')})`)}
                    ${deleteIcon(`deleteContract(${c.id})`)}
                </div>
            </div>
            <div class="contract-info">
                Contacts Now: ${used}
            </div>
            <div class="contract-info">
                Contacts Limit: ${limit}
            </div>
            <div class="usage-bar"><div class="usage-bar-inner" style="width:${percent}%; background-color:${color};"></div></div>
                 <div class="contract-updated-bottom">Last checked: ${c.last_checked ? c.last_checked : '—'}</div>


        `;
        list.appendChild(item);
    }
}

// SVG icons (edit, delete)
function editIcon(onclick) {
    return `<svg fill="#3498db" viewBox="0 0 24 24" onclick="${onclick}"><path d="M3 17.25V21h3.75l11.06-11.06-3.75-3.75L3 17.25zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.83 1.83 3.75 3.75 1.84-1.82z"/></svg>`;
}
function deleteIcon(onclick) {
    return `<svg fill="#e74c3c" viewBox="0 0 24 24" onclick="${onclick}"><path d="M16 9v10H8V9h8m-1.5-6h-5l-1 1H5v2h14V4h-4.5l-1-1z"/></svg>`;
}

function showForm(show = true, title = 'Add Contract') {
    document.getElementById('formOverlay').classList.toggle('hidden', !show);
    document.getElementById('formTitle').textContent = title;
}

function editContract(contract) {
    const form = document.getElementById('contractForm');
    editingId = contract.id;

    form.name.value = contract.name;
    form.sfmc_subdomain.value = contract.sfmc_subdomain || '';
    form.client_id.value = contract.client_id || '';
    form.client_secret.value = contract.client_secret || '';
    form.de_key.value = contract.de_key || '';
    form.contacts_limit.value = contract.contacts_limit || '';
    form.slack_users_ids.value = (contract.slack_users_ids || []).join(', ');

    showForm(true, 'Edit Contract');
}

async function deleteContract(id) {
    if (!confirm('Are you sure you want to delete this contract?')) return;
    const res = await fetch(`/api/contracts/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.success) loadContracts();
    else alert('Error deleting contract: ' + result.error);
}

const form = document.getElementById('contractForm');
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.slack_users_ids = data.slack_users_ids.split(',').map(x => x.trim()).filter(Boolean);

    let res;
    if (editingId) {
        res = await fetch(`/api/contracts/${editingId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
    } else {
        res = await fetch('/api/contracts', { method: 'POST', body: formData });
    }

    const result = await res.json();
    if (result.success) {
        showForm(false);
        form.reset();
        editingId = null;
        loadContracts();
    } else {
        alert('Error: ' + result.error);
    }
});

document.getElementById('addContractBtn').addEventListener('click', () => {
    editingId = null;
    form.reset();
    showForm(true, 'Add Contract');
});

document.getElementById('cancelBtn').addEventListener('click', () => showForm(false));

loadContracts();
