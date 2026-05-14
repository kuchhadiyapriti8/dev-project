document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const username = document.getElementById('username');
    const password = document.getElementById('password');
    const email = document.getElementById('email');
    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const birthDate = document.getElementById('birthDate');
    const location = document.getElementById('location');
  
    form.addEventListener('submit', (e) => {
      clearErrors();
  
      let valid = true;
  
      if (!username.value.trim()) {
        showError(username, 'Username is required');
        valid = false;
      }
  
      if (!password.value.trim()) {
        showError(password, 'Password is required');
        valid = false;
      } else if (!isValidPassword(password.value.trim())) {
        showError(password, 'Password must be at least 8 characters long and include a mix of uppercase, lowercase, numbers, and special characters');
        valid = false;
      }
  
      if (!email.value.trim()) {
        showError(email, 'Email is required');
        valid = false;
      } else if (!isValidEmail(email.value.trim())) {
        showError(email, 'Please enter a valid email address');
        valid = false;
      }
  
      if (!firstName.value.trim()) {
        showError(firstName, 'First Name is required');
        valid = false;
      }
  
      if (!lastName.value.trim()) {
        showError(lastName, 'Last Name is required');
        valid = false;
      }
  
      if (!birthDate.value) {
        showError(birthDate, 'Birth Date is required');
        valid = false;
      }
  
      if (!location.value.trim()) {
        showError(location, 'Location is required');
        valid = false;
      }
  
      if (!valid) {
        e.preventDefault();
      }
    });
  
    function showError(input, message) {
      const errorElement = input.nextElementSibling;
      errorElement.textContent = message;
      errorElement.classList.add('visible');
    }
  
    function clearErrors() {
      document.querySelectorAll('.error').forEach(errorElement => {
        errorElement.textContent = '';
        errorElement.classList.remove('visible');
      });
    }
  
    function isValidEmail(email) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return emailRegex.test(email);
    }
  
    function isValidPassword(password) {
      const passwordRegex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
      return passwordRegex.test(password);
    }
  
    // Optional: Toggle password visibility
    // const passwordIcon = document.getElementById('passwordIcon');
    // passwordIcon.addEventListener('click', () => {
    //   if (password.type === 'password') {
    //     password.type = 'text';
    //     passwordIcon.classList.remove('fa-eye');
    //     passwordIcon.classList.add('fa-eye-slash');
    //   } else {
    //     password.type = 'password';
    //     passwordIcon.classList.remove('fa-eye-slash');
    //     passwordIcon.classList.add('fa-eye');
    //   }
    // });
    function handleSectionClick(section) {
      document.querySelectorAll('.user-reservation, .user-history, .edit-profile, .change-password, .user-deactivate').forEach(el => el.style.display = 'none');
      document.getElementById(section).style.display = 'block';

      // Update active button
      document.querySelectorAll('.controls .button-tertiary, .controls li').forEach(btn => btn.classList.remove('active'));
      document.querySelector(`.controls [onclick="handleSectionClick('${section}')"]`).classList.add('active');
  }
  });
  