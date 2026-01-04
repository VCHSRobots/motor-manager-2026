// Authentication utility functions for token management

/**
 * Wrapper around fetch that automatically handles token refresh
 * and logout on expiration
 */
async function authFetch(url, options = {}) {
    const authToken = localStorage.getItem('auth_token');
    
    // Add authorization header if token exists
    if (authToken) {
        options.headers = {
            ...options.headers,
            'Authorization': `Bearer ${authToken}`
        };
    }
    
    try {
        const response = await fetch(url, options);
        
        // Check for refreshed token in response headers
        const newToken = response.headers.get('X-New-Token');
        if (newToken) {
            localStorage.setItem('auth_token', newToken);
        }
        
        // Handle 401 Unauthorized (token expired or invalid)
        if (response.status === 401) {
            const errorData = await response.json().catch(() => ({}));
            if (errorData.detail && errorData.detail.includes('expired')) {
                alert('Your session has expired. Please login again.');
                logout();
            } else if (errorData.detail && errorData.detail.includes('Invalid token')) {
                alert('Invalid session. Please login again.');
                logout();
            }
            throw new Error(errorData.detail || 'Unauthorized');
        }
        
        return response;
    } catch (error) {
        throw error;
    }
}

/**
 * Logout function that clears local storage and redirects to login
 */
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    window.location.href = '/login-page';
}

/**
 * Check if user is logged in
 */
function isLoggedIn() {
    return localStorage.getItem('auth_token') !== null;
}

/**
 * Get current user info from localStorage
 */
function getCurrentUser() {
    return {
        username: localStorage.getItem('username'),
        role: localStorage.getItem('role'),
        token: localStorage.getItem('auth_token')
    };
}
