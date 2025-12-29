/**
 * API Service for AI Clinical Pipeline
 */

const API_BASE = '/api';

/**
 * Full symptom analysis
 */
export async function analyzeSymptoms(data) {
    const response = await fetch(`${API_BASE}/analyze`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        throw new Error('Analysis failed');
    }

    return response.json();
}

/**
 * Chat message
 */
export async function sendChatMessage(message, sessionId = null) {
    const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message,
            session_id: sessionId,
        }),
    });

    if (!response.ok) {
        throw new Error('Chat failed');
    }

    return response.json();
}

/**
 * Get report by ID
 */
export async function getReport(reportId) {
    const response = await fetch(`${API_BASE}/reports/${reportId}`);

    if (!response.ok) {
        throw new Error('Report not found');
    }

    return response.json();
}

/**
 * Upload ICMR documents
 */
export async function uploadDocuments(files) {
    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });

    const response = await fetch(`${API_BASE}/upload-documents`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        throw new Error('Upload failed');
    }

    return response.json();
}

/**
 * Search knowledge base
 */
export async function searchKnowledge(query, topK = 5) {
    const response = await fetch(`${API_BASE}/knowledge/search?query=${encodeURIComponent(query)}&top_k=${topK}`);

    if (!response.ok) {
        throw new Error('Search failed');
    }

    return response.json();
}

/**
 * Get knowledge base stats
 */
export async function getKnowledgeStats() {
    const response = await fetch(`${API_BASE}/knowledge/stats`);

    if (!response.ok) {
        throw new Error('Failed to get stats');
    }

    return response.json();
}

/**
 * Health check
 */
export async function healthCheck() {
    const response = await fetch('/health');
    return response.json();
}

/**
 * WebSocket connection for real-time chat
 */
export function createChatWebSocket(sessionId, onMessage, onError) {
    const ws = new WebSocket(`ws://localhost:8000/ws/chat/${sessionId}`);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        onMessage(data);
    };

    ws.onerror = (error) => {
        onError(error);
    };

    return ws;
}
