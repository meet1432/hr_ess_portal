// Weekly Timesheet View - Quick Entry Modal Functions
// These functions are called directly from onclick handlers in the HTML template

// Auto-select and show project info
window.onProjectChange = function() {
    const select = document.getElementById('defaultProject');
    const selectedOption = select.options[select.selectedIndex];
    const taskCount = selectedOption.getAttribute('data-task-count') || '0';

    const projectInfo = document.getElementById('projectInfo');
    if (projectInfo) {
        projectInfo.textContent =
            selectedOption.value ? `✓ ${taskCount} tasks available` : '— Select a project to see tasks —';
    }

    // Fetch and populate tasks
    if (selectedOption.value) {
        const projectId = selectedOption.value;
        fetch('/my/timesheets/get-tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('[name="csrf_token"]')?.value || ''
            },
            body: JSON.stringify({jsonrpc: '2.0', method: 'call', params: {project_id: parseInt(projectId)}})
        })
        .then(r => r.json())
        .then(data => {
            const taskSelect = document.getElementById('defaultTask');
            if (taskSelect) {
                taskSelect.innerHTML = '<option value="">— No Task (General) —</option>';
                taskSelect.disabled = false;

                if (data.result && data.result.tasks) {
                    data.result.tasks.forEach(task => {
                        const opt = document.createElement('option');
                        opt.value = task.id;
                        opt.textContent = task.name + (task.priority ? ' (' + ['Low','Med','High','Urgent'][parseInt(task.priority)] + ')' : '');
                        taskSelect.appendChild(opt);
                    });
                }
            }
        });
    } else {
        const taskSelect = document.getElementById('defaultTask');
        if (taskSelect) {
            taskSelect.innerHTML = '<option value="">— Select Task —</option>';
            taskSelect.disabled = true;
        }
    }
};

// Quick select button handler
window.selectProject = function(btn, projectId, projectName) {
    const select = document.getElementById('defaultProject');
    const projectId_val = btn.getAttribute('data-project-id');

    for (let i = 0; i < select.options.length; i++) {
        if (select.options[i].value === projectId_val) {
            select.selectedIndex = i;
            break;
        }
    }
    window.onProjectChange();
};

// Quick entry modal - prefill if entry exists
window.openQuickEntry = function(projectId, date, taskId) {
    let modal = document.getElementById('quickEntryModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'quickEntryModal';
        modal.className = 'edit-modal';
        modal.innerHTML = `
            <div class="edit-modal-content">
                <h3>Quick Entry</h3>
                <div class="edit-form-group">
                    <label>Hours *</label>
                    <input type="number" id="modalHours" placeholder="0.00" step="0.25" min="0.25" max="24" required style="width:100%;padding:0.5rem;border:1px solid #ddd;border-radius:4px;"/>
                </div>
                <div class="edit-form-group">
                    <label>Description (optional)</label>
                    <input type="text" id="modalDescription" placeholder="What did you work on?" style="width:100%;padding:0.5rem;border:1px solid #ddd;border-radius:4px;"/>
                </div>
                <input type="hidden" id="modalProjectId"/>
                <input type="hidden" id="modalDate"/>
                <input type="hidden" id="modalTaskId"/>
                <input type="hidden" id="modalEntryId"/>
                <input type="hidden" id="modalIsSubmitted"/>
                <div class="edit-modal-buttons">
                    <button class="btn-cancel" onclick="closeQuickEntryModal()">Cancel</button>
                    <button class="btn-save" onclick="saveQuickEntry()">Save Entry</button>
                    <button id="modalDeleteBtn" class="btn-delete" onclick="deleteQuickEntry()" style="background:#e74c3c;display:none;">Delete</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Set modal values
    document.getElementById('modalProjectId').value = projectId;
    document.getElementById('modalDate').value = date;
    document.getElementById('modalTaskId').value = taskId || '';
    document.getElementById('modalHours').value = '';
    document.getElementById('modalDescription').value = '';
    document.getElementById('modalEntryId').value = '';
    document.getElementById('modalIsSubmitted').value = '';

    // Hide delete button initially
    document.getElementById('modalDeleteBtn').style.display = 'none';
    document.getElementById('modalHours').disabled = false;

    // Check if entry exists for this date/project/task
    fetch('/my/timesheets/get-entry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: {
                date: date,
                project_id: projectId,
                task_id: taskId || null
            }
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.result && data.result.entry) {
            const entry = data.result.entry;
            document.getElementById('modalEntryId').value = entry.id;
            document.getElementById('modalHours').value = entry.hours;
            document.getElementById('modalDescription').value = entry.description || '';
            document.getElementById('modalIsSubmitted').value = entry.is_submitted ? '1' : '0';

            // Only allow edit/delete if NOT submitted
            if (!entry.is_submitted) {
                document.getElementById('modalDeleteBtn').style.display = 'inline-block';
            } else {
                document.getElementById('modalHours').disabled = true;
                document.getElementById('modalDescription').disabled = true;
                document.querySelector('.btn-save').disabled = true;
                document.querySelector('.btn-save').textContent = 'Submitted (Read-only)';
            }
        }
    });

    modal.classList.add('active');
    document.getElementById('modalHours').focus();
};

window.closeQuickEntryModal = function() {
    const modal = document.getElementById('quickEntryModal');
    if (modal) {
        modal.classList.remove('active');
    }
};

window.saveQuickEntry = function() {
    const hours = parseFloat(document.getElementById('modalHours').value);
    const date = document.getElementById('modalDate').value;
    const projectId = parseInt(document.getElementById('modalProjectId').value);
    const taskId = document.getElementById('modalTaskId').value ? parseInt(document.getElementById('modalTaskId').value) : null;
    const description = document.getElementById('modalDescription').value;
    const entryId = document.getElementById('modalEntryId').value;
    const isSubmitted = document.getElementById('modalIsSubmitted').value === '1';

    if (isSubmitted) {
        alert('This entry is submitted and cannot be modified. Please unsubmit to edit.');
        return;
    }

    if (!hours || hours <= 0) {
        alert('Please enter valid hours');
        return;
    }

    const payload = {
        jsonrpc: '2.0',
        method: 'call',
        params: {
            project_id: projectId,
            task_id: taskId,
            date: date,
            hours: hours,
            description: description,
            entry_id: entryId || null
        }
    };

    fetch('/my/timesheets/quick-entry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
        if (data.result) {
            window.closeQuickEntryModal();
            location.reload();
        } else if (data.error) {
            alert('Error: ' + (data.error.data?.message || 'Failed to save entry'));
        }
    })
    .catch(e => {
        alert('Error saving entry: ' + e.message);
    });
};

// Delete timesheet entry
window.deleteQuickEntry = function() {
    if (!confirm('Delete this timesheet entry?')) {
        return;
    }

    const entryId = parseInt(document.getElementById('modalEntryId').value);
    const isSubmitted = document.getElementById('modalIsSubmitted').value === '1';

    if (isSubmitted) {
        alert('This entry is submitted and cannot be deleted. Please unsubmit first.');
        return;
    }

    const payload = {
        jsonrpc: '2.0',
        method: 'call',
        params: {
            timesheet_id: entryId
        }
    };

    fetch('/my/timesheets/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('[name="csrf_token"]')?.value || ''
        },
        body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .then(data => {
        if (data.result && data.result.success) {
            window.closeQuickEntryModal();
            location.reload();
        } else {
            alert('Error: ' + (data.error?.data?.message || 'Failed to delete entry'));
        }
    })
    .catch(e => alert('Error: ' + e.message));
};

// Setup event listeners when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Project search functionality
    const searchInput = document.getElementById('projectSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const select = document.getElementById('defaultProject');
            const options = select.querySelectorAll('option');

            options.forEach(option => {
                if (option.value === '') {
                    option.style.display = 'block';
                } else {
                    const projectName = option.textContent.toLowerCase();
                    option.style.display = projectName.includes(searchTerm) ? 'block' : 'none';
                }
            });
        });
    }

    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            window.closeQuickEntryModal();
        }
    });
});