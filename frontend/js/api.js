/**
 * API Integration for Fashion Wardrobe
 * Handles all communication with FastAPI backend
 */

const API_URL = 'http://localhost:8000';

// ==================== Auth (Option A: single admin) ====================
const AUTH_TOKEN_KEY = 'wardrobe_token';

function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function setToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

function removeToken() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
}

function isLoggedIn() {
    return !!getToken();
}

function logout() {
    removeToken();
    window.location.href = 'login.html';
}

/**
 * Login with username and password. Returns { success, token }.
 * Store token with setToken() and use in requests if you add protected endpoints.
 */
async function login(username, password) {
    const response = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
    }
    return data;
}

// ==================== Display Helpers ====================

/** Format category for display: replace underscores with spaces (e.g. long_sleeve → long sleeve) */
function formatCategoryForDisplay(cat) {
    if (!cat || typeof cat !== 'string') return '';
    return cat.replace(/_/g, ' ');
}

/** Simplified display name: leather_jacket/denim_jacket → Jacket, others stay descriptive */
function getDisplayCategory(cat) {
    if (!cat || typeof cat !== 'string') return '';
    if (cat === 'leather_jacket' || cat === 'denim_jacket') return 'Jacket';
    return formatCategoryForDisplay(cat);
}

// ==================== Items API ====================

/**
 * Upload image and process with AI pipeline
 */
async function uploadItem(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_URL}/api/items/upload`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }
    
    return await response.json();
}

/**
 * Get all items with optional filters
 */
async function getItems(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.category && filters.category !== 'All Categories') {
        params.append('category', filters.category);
    }
    if (filters.category_group) {
        params.append('category_group', filters.category_group);
    }
    if (filters.color && filters.color !== 'All Colors') {
        params.append('color', filters.color);
    }
    if (filters.material && filters.material !== 'All Materials') {
        params.append('material', filters.material);
    }
    if (filters.search) {
        params.append('search', filters.search);
    }
    if (filters.page) {
        params.append('page', filters.page);
    }
    if (filters.limit) {
        params.append('limit', filters.limit);
    }
    
    const url = `${API_URL}/api/items${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url);
    
    if (!response.ok) {
        throw new Error('Failed to fetch items');
    }
    
    return await response.json();
}

/**
 * Get single item by ID
 */
async function getItem(itemId) {
    const response = await fetch(`${API_URL}/api/items/${itemId}`);
    
    if (!response.ok) {
        throw new Error('Item not found');
    }
    
    return await response.json();
}

/**
 * Update item with user data
 */
async function updateItem(itemId, data) {
    const response = await fetch(`${API_URL}/api/items/${itemId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Update failed');
    }
    
    return await response.json();
}

/**
 * Delete item
 */
async function deleteItem(itemId) {
    const response = await fetch(`${API_URL}/api/items/${itemId}`, {
        method: 'DELETE'
    });
    
    if (!response.ok) {
        throw new Error('Delete failed');
    }
    
    return await response.json();
}

/**
 * Get item image URL
 */
function getItemImageUrl(itemId, type = 'segmented') {
    return `${API_URL}/api/items/${itemId}/image?type=${type}`;
}

/**
 * Get statistics
 */
async function getStatistics() {
    const response = await fetch(`${API_URL}/api/stats`);
    
    if (!response.ok) {
        throw new Error('Failed to fetch statistics');
    }
    
    return await response.json();
}

// ==================== Outfits API ====================

async function saveOutfitToAPI(data) {
    const response = await fetch(`${API_URL}/api/outfits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to save outfit');
    }
    return await response.json();
}

async function getOutfits() {
    const response = await fetch(`${API_URL}/api/outfits`);
    if (!response.ok) throw new Error('Failed to fetch outfits');
    return await response.json();
}

async function getOutfit(outfitId) {
    const response = await fetch(`${API_URL}/api/outfits/${outfitId}`);
    if (!response.ok) throw new Error('Outfit not found');
    return await response.json();
}

async function updateOutfitAPI(outfitId, data) {
    const response = await fetch(`${API_URL}/api/outfits/${outfitId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to update outfit');
    }
    return await response.json();
}

async function deleteOutfitAPI(outfitId) {
    const response = await fetch(`${API_URL}/api/outfits/${outfitId}`, { method: 'DELETE' });
    if (!response.ok) throw new Error('Failed to delete outfit');
    return await response.json();
}

// ==================== Feedback & Recommendation API ====================

async function sendFeedback(data) {
    const response = await fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to send feedback');
    }
    return await response.json();
}

async function getSuggestion() {
    const response = await fetch(`${API_URL}/api/feedback/suggest`);
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'No suggestion available');
    }
    return await response.json();
}

// ==================== Helper Functions ====================

/**
 * Show loading spinner
 */
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

/**
 * Hide loading spinner
 */
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

/**
 * Show error message
 */
function showError(message, duration = 3000) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-xl z-50 animate-fade-in';
    toast.innerHTML = `
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
            <span class="font-bold">${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, duration);
}

/**
 * Show success message
 */
function showSuccess(message, duration = 3000) {
    const toast = document.createElement('div');
    toast.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-xl z-50 animate-fade-in';
    toast.innerHTML = `
        <div class="flex items-center space-x-2">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <span class="font-bold">${message}</span>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, duration);
}

/**
 * Format confidence as percentage
 */
function formatConfidence(confidence) {
    return `${(confidence * 100).toFixed(1)}%`;
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
