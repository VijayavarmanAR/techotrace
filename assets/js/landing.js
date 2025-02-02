document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();

    // Check authentication first
    checkAuthentication();

    // Setup event listeners
    setupEventListeners();

    // Setup login modal
    setupLoginModal();
});

// Authentication check
function checkAuthentication() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (isLoggedIn === 'true')
         {
        // Redirect to home page if already logged in
        window.location.href = 'home.html';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Smooth scroll for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Get Started button handler
    const getStartedBtn = document.getElementById('getStartedBtn');
    if (getStartedBtn) {
        getStartedBtn.addEventListener('click', () => {
            const modal = document.getElementById('loginModal');
            modal.classList.remove('hidden');
            modal.classList.add('flex', 'modal-enter');
            document.body.style.overflow = 'hidden';

            // Focus on email input after modal opens
            setTimeout(() => {
                document.getElementById('email').focus();
            }, 300);
        });
    }

    // Navigation shadow on scroll
    window.addEventListener('scroll', () => {
        const nav = document.querySelector('nav');
        if (window.scrollY > 0) {
            nav.classList.add('shadow-lg');
        } else {
            nav.classList.remove('shadow-lg');
        }
    });
}

// Login Modal Functionality
function setupLoginModal() {
    const modal = document.getElementById('loginModal');
    const loginBtn = document.getElementById('loginBtn');
    const closeBtn = document.getElementById('closeModal');
    const loginForm = document.getElementById('loginForm');

    // Open modal
    loginBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        modal.classList.add('flex', 'modal-enter');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    });

    // Close modal
    closeBtn.addEventListener('click', closeModal);

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Escape key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });

    // Handle form submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const submitBtn = loginForm.querySelector('button[type="submit"]');

        try {
            // Disable submit button and show loading state
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader" class="animate-spin h-5 w-5 mx-auto"></i>';
            lucide.createIcons();

            // Use Firebase to authenticate user
            const userCredential = await auth.signInWithEmailAndPassword(email, password);
            
            // On successful login, store login status and show welcome message
            localStorage.setItem('isLoggedIn', 'true');
            alert(`Welcome, ${userCredential.user.email}`);
            
            // Redirect to home page after successful login
            window.location.href = '/home.html';

        } catch (error) {
            console.error('Login failed:', error);
            showError('username/password mismatch.');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.textContent = 'Sign In';
        }
    });

    function closeModal() {
        modal.classList.add('modal-exit');
        setTimeout(() => {
            modal.classList.remove('flex', 'modal-enter', 'modal-exit');
            modal.classList.add('hidden');
            document.body.style.overflow = ''; // Restore scrolling
        }, 300);
    }

    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'text-red-500 text-sm mt-2';
        errorDiv.textContent = message;

        const existingError = loginForm.querySelector('.text-red-500');
        if (existingError) {
            existingError.remove();
        }

        loginForm.appendChild(errorDiv);
    }
}

// Helper function to validate email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}
