// Theme Toggle Function with AJAX Loader
function toggleTheme() {
  const html = document.documentElement;
  const themeToggle = document.getElementById('themeToggle');
  const currentTheme = html.getAttribute('data-theme');
  
  // Show loader
  if (typeof showAjaxLoader === 'function') {
    showAjaxLoader('Switching theme...');
  }
  
  // Add a small delay for smooth transition
  setTimeout(() => {
    if (currentTheme === 'dark') {
      html.removeAttribute('data-theme');
      if (themeToggle) themeToggle.textContent = '🌙';
      localStorage.setItem('theme', 'light');
    } else {
      html.setAttribute('data-theme', 'dark');
      if (themeToggle) themeToggle.textContent = '☀️';
      localStorage.setItem('theme', 'dark');
    }
    
    // Hide loader after theme is applied
    setTimeout(() => {
      if (typeof hideAjaxLoader === 'function') {
        hideAjaxLoader();
      }
    }, 300);
  }, 100);
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', function() {
  const savedTheme = localStorage.getItem('theme');
  const themeToggle = document.getElementById('themeToggle');
  
  if (savedTheme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    if (themeToggle) themeToggle.textContent = '☀️';
  } else {
    if (themeToggle) themeToggle.textContent = '🌙';
  }
});

// General Feedback Form Submission
function initGeneralFeedbackForm() {
  const form = document.getElementById('generalFeedbackForm');
  if (!form) return;
  
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const name = this.querySelector('.feedback-name-input').value;
    const email = this.querySelector('.feedback-email-input').value;
    const message = this.querySelector('.feedback-message-input').value;
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('email', email);
    formData.append('message', message);
    
    fetch('/submit-general-feedback', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert(data.message);
        form.reset();
      } else {
        alert('Error: ' + data.message);
      }
    })
    .catch(error => {
      console.error('Error:', error);
      alert('An error occurred while submitting feedback');
    });
  });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initGeneralFeedbackForm);
