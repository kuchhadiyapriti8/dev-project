function handleSectionClick(section) {
    document.querySelectorAll('.user-reservation, .user-history, .edit-profile, .change-password, .user-deactivate').forEach(el => el.style.display = 'none');
    document.getElementById(section).style.display = 'block';

    // Update active button
    document.querySelectorAll('.controls .button-tertiary, .controls li').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.controls [onclick="handleSectionClick('${section}')"]`).classList.add('active');
}

function handleSaveEdit(event) {
    event.preventDefault();
    alert('Save profile changes');
}

function handleChangePassword(event) {
    event.preventDefault();
    alert('Change password');
}

function handleDeactivate() {
    alert('Deactivate account');
}

function handleCancelEdit() {
    handleSectionClick('reservations');
}

function handleCancelChangePassword() {
    handleSectionClick('reservations');
}

function handleCancelDeactivate() {
    handleSectionClick('reservations');
}