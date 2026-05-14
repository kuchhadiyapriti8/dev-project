document.addEventListener("DOMContentLoaded", function () {
    const storedFullName = sessionStorage.getItem('fullName');
    const storedUserType = sessionStorage.getItem('user_type');

    const loginLogoutButton = document.getElementById("login-logout-button").getElementsByTagName('a')[0];
    const signupButton = document.getElementById("signup-button");

    if (storedFullName) {
        loginLogoutButton.textContent = 'Logout';
        signupButton.style.display = 'none';
    } else {
        loginLogoutButton.textContent = 'Logout';
    }

    const welcomeMessage = document.getElementById("welcome-message");
    const userName = document.getElementById("user-name");

    if (storedFullName) {
        welcomeMessage.textContent = storedUserType === "admin" ? "Welcome Admin" : "Welcome Back!";
        userName.textContent = storedFullName;
    }

    document.getElementById("menu-icon").addEventListener("click", function () {
        const navMenu = document.getElementById("nav-menu");
        navMenu.classList.toggle("active");
        this.classList.toggle("fa-times");
    });
});

function handleClick() {
    const navMenu = document.getElementById("nav-menu");
    navMenu.classList.toggle("active");
    const menuIcon = document.getElementById("menu-icon");
    menuIcon.classList.toggle("fa-times");
}
