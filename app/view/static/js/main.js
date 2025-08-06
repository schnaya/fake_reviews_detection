function escapeHTML(str) {
    if (str === null || str === undefined) {
        return '';
    }
    return str.toString()
        .replace(/&/g, '&')
        .replace(/</g, '<')
        .replace(/>/g, '>')
        .replace(/"/g, '"');
}


function showAlert(message, type = 'info', duration = 4000) {
    const alertContainer = document.getElementById('alert-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${escapeHTML(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    alertContainer.appendChild(alert);

    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, duration);
}

function checkAuth() {
    return currentUser !== null;
}


async function handleLogout() {
    try {
        const response = await fetch('/api/auth/logout', { method: 'POST' });
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_role');
        window.location.href = response.url;
    } catch (error) {
        showAlert('Не удалось выйти из системы.', 'danger');
        console.error('Logout failed:', error);
    }
}


document.addEventListener('DOMContentLoaded', () => {
    const authNav = document.getElementById('auth-nav');
    const navCreateProduct = document.getElementById('nav-create-product');

    if (checkAuth()) {
        authNav.innerHTML = `<button onclick="handleLogout()" class="btn btn-outline-primary">Выйти</button>`;
        if (navCreateProduct) navCreateProduct.style.display = 'block';

    } else {
        authNav.innerHTML = `
            <a href="/login" class="btn btn-outline-primary me-2">Войти</a>
            <a href="/register" class="btn btn-primary">Регистрация</a>
        `;
        if (navCreateProduct) navCreateProduct.style.display = 'none';
    }
});