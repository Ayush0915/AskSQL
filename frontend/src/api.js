import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60 seconds — LLM calls can take a while
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Submit a natural-language question to the AskSQL pipeline.
 * @param {string} question - The NL question from the user.
 * @returns {Promise<{success, sql, explanation, results, error, retries_used}>}
 */
export async function askQuestion(question) {
  const response = await apiClient.post('/api/query', { question })
  return response.data
}

/**
 * Fetch the schema browser list (table names, descriptions, columns).
 * @returns {Promise<{tables: Array<{table_name, description, columns}>}>}
 */
export async function fetchSchema() {
  const response = await apiClient.get('/api/schema')
  return response.data
}

/**
 * Health check for the backend.
 * @returns {Promise<{status: string}>}
 */
export async function healthCheck() {
  const response = await apiClient.get('/api/health')
  return response.data
}
