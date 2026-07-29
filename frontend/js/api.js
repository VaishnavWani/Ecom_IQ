// frontend/js/api.js
// Handles communication with the FastAPI backend

const API_URL = 'http://localhost:8000/investigate';

/**
 * Sends a query to the backend investigation API.
 * @param {string} query The natural language query.
 * @returns {Promise<Object>} The API response (scope and report).
 */
async function fetchInvestigation(query) {
  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, include_raw_data: false })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'API request failed');
    }

    return await res.json();
  } catch (error) {
    console.error("API Error:", error);
    throw error;
  }
}
