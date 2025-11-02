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
    return `<i class="material-icons" style="cursor:pointer; color:#3498db; font-size:20px; margin-right:5px;" onclick="${onclick}">edit</i>`;
}
function deleteIcon(onclick) {
    return `<i class="material-icons" style="cursor:pointer; color:#e74c3c; font-size:20px;" onclick="${onclick}">delete</i>`;
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


const helpBtn = document.getElementById('helpBtn');
const helpModal = document.getElementById('helpModal');
const closeHelpBtn = document.getElementById('closeHelpBtn');

helpBtn.addEventListener('click', () => {
    helpModal.classList.remove('hidden'); // Show modal
});

closeHelpBtn.addEventListener('click', () => {
    helpModal.classList.add('hidden'); // Hide modal
});

// Optional: click outside modal to close
helpModal.addEventListener('click', (e) => {
    if (e.target === helpModal) helpModal.classList.add('hidden');
});
