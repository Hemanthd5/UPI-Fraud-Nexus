/**
 * Automatic Geolocation Detection for UPI Fraud Detection System
 * Uses Browser Geolocation API and IP-based fallback
 */

// Fetch location data and populate the form field
function detectAndFetchLocation() {
    const cityField = document.getElementById('transaction_city');
    
    // If browser supports geolocation
    if (navigator.geolocation) {
        // Show loading indicator
        showLocationStatus('Detecting location...', 'info');
        
        navigator.geolocation.getCurrentPosition(
            function(position) {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;
                
                console.log('Browser geolocation obtained:', latitude, longitude);
                
                // Send coordinates to backend to get city/state
                fetchLocationFromCoordinates(latitude, longitude);
            },
            function(error) {
                // If user denies permission or error occurs, fall back to IP-based geolocation
                console.warn('Geolocation permission denied or error:', error.message);
                fetchLocationFromIP();
            },
            {
                enableHighAccuracy: false,
                timeout: 8000,  // 8 seconds timeout
                maximumAge: 300000  // Use cached position if less than 5 minutes old
            }
        );
    } else {
        // Browser doesn't support geolocation, fall back to IP
        console.warn('Browser does not support geolocation');
        fetchLocationFromIP();
    }
}

// Fetch location from coordinates using backend
function fetchLocationFromCoordinates(latitude, longitude) {
    console.log('Attempting to fetch location from coordinates...');
    
    fetch('/get_location_from_coords', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
        })
    })
    .then(response => {
        console.log('Coordinates response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Location data from coordinates:', data);
        if (data.city && data.city !== 'Unknown') {
            populateLocationFields(data.city, data.state);
            showLocationStatus('Location detected via GPS!', 'success');
        } else {
            // If reverse geocoding failed, fall back to IP
            console.log('Coordinates lookup failed, falling back to IP');
            fetchLocationFromIP();
        }
    })
    .catch(error => {
        console.error('Error fetching location from coordinates:', error);
        console.log('Falling back to IP-based geolocation...');
        fetchLocationFromIP();
    });
}

// Fetch location from IP address
function fetchLocationFromIP() {
    console.log('Attempting to fetch location from IP...');
    
    fetch('/get_location_from_ip', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('IP response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Location data from IP:', data);
        if (data.city && data.city !== 'Unknown') {
            populateLocationFields(data.city, data.state);
            if (data.source === 'local') {
                showLocationStatus('Using local network IP. Please enter city manually or use GPS.', 'warning');
            } else {
                showLocationStatus('Location detected via IP.', 'success');
            }
        } else {
            showLocationStatus('Could not detect location automatically. Please enter manually.', 'warning');
        }
    })
    .catch(error => {
        console.error('Error fetching location from IP:', error);
        showLocationStatus('Could not detect location. Please enter manually.', 'error');
    });
}

// Populate location fields in the form
function populateLocationFields(city, state) {
    const cityField = document.getElementById('transaction_city');
    
    if (city && city !== 'Unknown') {
        cityField.value = city;
        cityField.disabled = false;  // Allow user to override if needed
        console.log('City field populated with:', city);
    }
    
    // Store state for later use if needed
    if (state && state !== 'Unknown') {
        sessionStorage.setItem('transaction_state', state);
    }
}

// Show location status message
function showLocationStatus(message, type) {
    const statusElement = document.getElementById('location-status');
    
    if (!statusElement) {
        console.log('Status element not found');
        return;  // Element doesn't exist, skip
    }
    
    statusElement.textContent = message;
    statusElement.className = 'location-status ' + type;
    statusElement.style.display = 'block';
    
    console.log('Status message:', type, message);
    
    // Auto-hide success/info messages after 4 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 4000);
    }
}

// Initialize location detection when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded, checking for transaction_city field...');
    
    const cityField = document.getElementById('transaction_city');
    
    if (cityField) {
        console.log('transaction_city field found, starting auto-detection...');
        // Auto-detect location when page loads
        detectAndFetchLocation();
        
        // Also allow manual re-detection via a button if it exists
        const detectBtn = document.getElementById('detect-location-btn');
        if (detectBtn) {
            console.log('Detect button found, attaching click handler...');
            detectBtn.addEventListener('click', function(e) {
                e.preventDefault();
                detectAndFetchLocation();
            });
        }
    } else {
        console.log('transaction_city field not found on this page');
    }
});

// Allow manual location refresh
function manualLocationRefresh() {
    const cityField = document.getElementById('transaction_city');
    cityField.value = '';  // Clear current value
    detectAndFetchLocation();  // Re-detect
}
