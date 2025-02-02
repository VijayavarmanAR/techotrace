// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons
    lucide.createIcons();
    
    // Initialize the application
    initializeApp();
});

// State Management
const state = {
    user: {
        name: "John Doe",
        email: "john.doe@company.com",
        role: "Senior Digital Forensics Investigator",
        lastLogin: "2024-11-19T08:30:00",
        notifications: 3
    },
    recentActivities: [
        {
            id: 1,
            type: "update",
            description: "Updated Case #2024-11-001 - Added new evidence items",
            timestamp: "2024-11-19T10:15:00"
        },
        {
            id: 2,
            type: "create",
            description: "Created new Case #2024-11-002 - Incident Response",
            timestamp: "2024-11-19T09:45:00"
        },
        {
            id: 3,
            type: "close",
            description: "Closed Case #2024-11-000 - Investigation complete",
            timestamp: "2024-11-18T16:30:00"
        }
    ]
};

// Initialize Application
function initializeApp() {
    // Setup event listeners
    setupEventListeners();
    
    // Initial render
    updateUserInterface();
    
    // Check authentication
    checkAuthentication();
}

// Event Listeners Setup
function setupEventListeners() {
    // Logout button
    document.getElementById('logoutButton').addEventListener('click', handleLogout);
    
    // Quick action buttons
    setupQuickActionListeners();
}

// Authentication Check
function checkAuthentication() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn) {
        window.location.href = 'landing.html';
    }
}

// Logout Handler
async function handleLogout() {
    try {
        const logoutButton = document.getElementById('logoutButton');
        logoutButton.disabled = true;
        logoutButton.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 animate-spin"></i>';
        lucide.createIcons();

        await new Promise(resolve => setTimeout(resolve, 1000));
        
        localStorage.clear();
        window.location.href = 'landing.html';
    } catch (error) {
        console.error('Logout failed:', error);
        alert('Failed to logout. Please try again.');
    }
}

// Quick Actions Setup
function setupQuickActionListeners() {
    // Set up action buttons
    const actionButtons = {
        'newCaseButton': '/new-case',
        'openCasesButton': '/existing-cases',
        'completedCasesButton': '/completed-cases'
    };

    Object.entries(actionButtons).forEach(([id, path]) => {
        const button = document.getElementById(id);
        if (button) {
            button.addEventListener('click', () => navigate(path));
        }
    });
}

// UI Update Functions
function updateUserInterface() {
    // Update user information
    const elements = {
        'userName': state.user.name,
        'welcomeName': state.user.name,
        'userRole': state.user.role,
        'lastLogin': formatDate(state.user.lastLogin),
        'notificationCount': state.user.notifications
    };

    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
    
    // Update recent activities
    updateRecentActivities();
}

function updateRecentActivities() {
    const activitiesContainer = document.getElementById('recentActivities');
    if (!activitiesContainer) return;

    activitiesContainer.innerHTML = '';
    
    state.recentActivities.forEach(activity => {
        const activityElement = createActivityElement(activity);
        activitiesContainer.appendChild(activityElement);
    });
}

// Helper Functions
function createActivityElement(activity) {
    const div = document.createElement('div');
    div.className = 'flex items-start space-x-4 p-3 bg-gray-50 rounded-lg activity-card';
    
    div.innerHTML = `
        <div class="p-2 bg-white rounded-full activity-icon ${activity.type}">
            ${getActivityIcon(activity.type)}
        </div>
        <div class="flex-1">
            <p class="text-sm">${sanitizeHTML(activity.description)}</p>
            <p class="text-xs text-gray-500 mt-1">${formatDate(activity.timestamp)}</p>
        </div>
    `;
    
    return div;
}

function getActivityIcon(type) {
    const iconMap = {
        'update': '<i data-lucide="activity" class="h-4 w-4 text-blue-500"></i>',
        'create': '<i data-lucide="plus" class="h-4 w-4 text-green-500"></i>',
        'close': '<i data-lucide="check-square" class="h-4 w-4 text-purple-500"></i>'
    };
    
    return iconMap[type] || '<i data-lucide="clock" class="h-4 w-4 text-gray-500"></i>';
}
document.addEventListener("DOMContentLoaded", () => {
    const logoutButton = document.getElementById("logoutButton");

    // Ensure the button exists before attaching the event listener
    if (logoutButton) {
        logoutButton.addEventListener("click", () => {
            firebase.auth().signOut()
                .then(() => {
                    console.log("User successfully logged out.");
                    window.location.href = "landing.html"; // Redirect to login page after logging out
                })
                .catch((error) => {
                    console.error("Error during logout: ", error);
                    alert("An error occurred while logging out. Please try again.");
                });
        });
    } else {
        console.error("Logout button not found on the page.");
    }
});

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function navigate(path) {
    window.location.href = path;
}

// Security
function sanitizeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
