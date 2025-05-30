// Global variables
let map;
let markersLayer;
let currentRecommendations = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    initializeEventListeners();
    loadChatHistory();
});

// Initialize Leaflet map
function initializeMap() {
    // Initialize map centered on Vietnam
    map = L.map('map').setView([16.0583, 108.2772], 6);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Initialize markers layer
    markersLayer = L.layerGroup().addTo(map);
}

// Initialize event listeners
function initializeEventListeners() {
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    const clearChatButton = document.getElementById('clearChat');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');
    const showAllButton = document.getElementById('showAllLocations');
    const centerMapButton = document.getElementById('centerMap');
    const modal = document.getElementById('locationModal');
    const modalClose = document.querySelector('.modal-close');
    
    // Send message on button click
    sendButton.addEventListener('click', sendMessage);
    
    // Send message on Enter key
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Clear chat history
    clearChatButton.addEventListener('click', clearChat);
    
    // Quick suggestion buttons
    suggestionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const message = this.getAttribute('data-message');
            messageInput.value = message;
            sendMessage();
        });
    });
    
    // Map controls
    showAllButton.addEventListener('click', showAllLocations);
    centerMapButton.addEventListener('click', centerMap);
    
    // Modal controls
    modalClose.addEventListener('click', closeModal);
    window.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
}

// Send message to chatbot
async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Clear input
    messageInput.value = '';
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // Show loading
    showLoading(true);
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                user_id: 'anonymous'
            })
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        
        // Add bot response to chat
        addMessageToChat(data.response, 'bot');
        
        // Update recommendations
        updateRecommendations(data.recommendations);
        
        // Update map with new recommendations
        updateMapMarkers(data.recommendations);
        
    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.', 'bot');
    } finally {
        showLoading(false);
    }
}

// Add message to chat container
function addMessageToChat(message, sender) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = message.replace(/\n/g, '<br>');
    
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Update recommendations panel
function updateRecommendations(recommendations) {
    currentRecommendations = recommendations;
    const recommendationsList = document.getElementById('recommendationsList');
    
    if (!recommendations || recommendations.length === 0) {
        recommendationsList.innerHTML = '<p class="no-recommendations">Không tìm thấy khuyến nghị phù hợp.</p>';
        return;
    }
    
    recommendationsList.innerHTML = '';
    
    recommendations.forEach((rec, index) => {
        const item = document.createElement('div');
        item.className = 'recommendation-item';
        item.innerHTML = `
            <h4>${rec['location.name']}</h4>
            <p><i class="fas fa-map-marker-alt"></i> ${rec['location.region']}</p>
            <p><i class="fas fa-mountain"></i> ${rec['location.terrain']}</p>
            ${rec.score ? `<p><i class="fas fa-star"></i> Độ phù hợp: ${rec.score.toFixed(1)}/10</p>` : ''}
        `;
        
        item.addEventListener('click', () => {
            showLocationDetails(rec['location.name']);
            // Center map on this location
            if (rec['location.lat'] && rec['location.lon']) {
                map.setView([rec['location.lat'], rec['location.lon']], 10);
            }
        });
        
        recommendationsList.appendChild(item);
    });
}

// Update map markers
function updateMapMarkers(recommendations) {
    // Clear existing markers
    markersLayer.clearLayers();
    
    if (!recommendations || recommendations.length === 0) return;
    
    recommendations.forEach((rec, index) => {
        if (rec['location.lat'] && rec['location.lon']) {
            const marker = L.marker([rec['location.lat'], rec['location.lon']])
                .bindPopup(`
                    <div class="popup-location-name">${rec['location.name']}</div>
                    <div class="popup-location-details">
                        <p><strong>Vùng:</strong> ${rec['location.region']}</p>
                        <p><strong>Địa hình:</strong> ${rec['location.terrain']}</p>
                        ${rec.score ? `<p><strong>Độ phù hợp:</strong> ${rec.score.toFixed(1)}/10</p>` : ''}
                        <button onclick="showLocationDetails('${rec['location.name']}')" 
                                style="margin-top: 10px; padding: 5px 10px; background: #4facfe; color: white; border: none; border-radius: 5px; cursor: pointer;">
                            Xem chi tiết
                        </button>
                    </div>
                `);
            
            markersLayer.addLayer(marker);
        }
    });
    
    // Fit map to show all markers
    if (markersLayer.getLayers().length > 0) {
        const group = new L.featureGroup(markersLayer.getLayers());
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Show location details modal
async function showLocationDetails(locationName) {
    try {
        showLoading(true);
        
        const response = await fetch(`/location/${encodeURIComponent(locationName)}`);
        if (!response.ok) {
            throw new Error('Failed to fetch location details');
        }
        
        const data = await response.json();
        
        document.getElementById('modalLocationName').textContent = locationName;
        
        const detailsDiv = document.getElementById('locationDetails');
        detailsDiv.innerHTML = `
            <div style="margin-bottom: 20px;">
                <h4><i class="fas fa-info-circle"></i> Thông tin cơ bản</h4>
                <p><strong>Vùng:</strong> ${data.location_info.region}</p>
                <p><strong>Địa hình:</strong> ${data.location_info.terrain}</p>
                <p><strong>Tọa độ:</strong> ${data.location_info.latitude.toFixed(4)}, ${data.location_info.longitude.toFixed(4)}</p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h4><i class="fas fa-chart-line"></i> Thông số thời tiết trung bình</h4>
                <p><strong>Nhiệt độ:</strong> ${data.overall_averages.temperature.toFixed(1)}°C</p>
                <p><strong>Lượng mưa:</strong> ${data.overall_averages.precipitation.toFixed(1)}mm</p>
                <p><strong>Độ ẩm:</strong> ${data.overall_averages.humidity.toFixed(1)}%</p>
                <p><strong>Tốc độ gió:</strong> ${data.overall_averages.wind_speed.toFixed(1)} km/h</p>
                <p><strong>Chỉ số UV:</strong> ${data.overall_averages.uv_index.toFixed(1)}</p>
            </div>
            
            <div>
                <h4><i class="fas fa-calendar"></i> Thống kê theo tháng</h4>
                <div style="max-height: 200px; overflow-y: auto;">
                    ${Object.entries(data.monthly_averages).map(([month, stats]) => `
                        <div style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                            <strong>Tháng ${month}:</strong>
                            Nhiệt độ ${stats['day.avgtemp_c'].toFixed(1)}°C, 
                            Mưa ${stats['day.totalprecip_mm'].toFixed(1)}mm, 
                            Độ ẩm ${stats['day.avghumidity'].toFixed(1)}%
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        document.getElementById('locationModal').style.display = 'block';
        
    } catch (error) {
        console.error('Error fetching location details:', error);
        alert('Không thể tải thông tin chi tiết. Vui lòng thử lại.');
    } finally {
        showLoading(false);
    }
}

// Close modal
function closeModal() {
    document.getElementById('locationModal').style.display = 'none';
}

// Show/hide loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    overlay.style.display = show ? 'flex' : 'none';
}

// Clear chat history
function clearChat() {
    const chatContainer = document.getElementById('chatContainer');
    chatContainer.innerHTML = `
        <div class="welcome-message">
            <div class="bot-message">
                <div class="message-content">
                    <p>Xin chào! Tôi là chatbot tư vấn du lịch Việt Nam. 🇻🇳</p>
                    <p>Hãy cho tôi biết bạn muốn đi du lịch vào thời gian nào và thích loại thời tiết như thế nào?</p>
                    <p><strong>Ví dụ:</strong> "Tôi muốn đi du lịch tháng 11, thích khí hậu mát mẻ và ít mưa"</p>
                </div>
            </div>
        </div>
    `;
    
    // Clear recommendations
    updateRecommendations([]);
    markersLayer.clearLayers();
}

// Show all locations on map
async function showAllLocations() {
    try {
        showLoading(true);
        
        const response = await fetch('/clusters');
        if (!response.ok) {
            throw new Error('Failed to fetch cluster data');
        }
        
        const data = await response.json();
        
        // Clear existing markers
        markersLayer.clearLayers();
        
        // Add markers for all locations from clusters
        data.clusters.forEach(cluster => {
            cluster.locations.forEach(locationName => {
                // This is a simplified version - in a real app, you'd need location coordinates
                // For now, we'll just show the current recommendations
            });
        });
        
    } catch (error) {
        console.error('Error fetching all locations:', error);
    } finally {
        showLoading(false);
    }
}

// Center map on Vietnam
function centerMap() {
    map.setView([16.0583, 108.2772], 6);
}

// Load chat history (optional feature)
async function loadChatHistory() {
    try {
        const response = await fetch('/history?limit=5');
        if (response.ok) {
            const history = await response.json();
            // You can implement chat history loading here if needed
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
    }
}
