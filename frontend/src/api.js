import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 120 seconds — LLM schema description generation and parsing can take a bit longer
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Submit a natural-language question to the AskSQL pipeline.
 * @param {string} question - The NL question from the user.
 * @param {string} sessionId - The session ID.
 * @returns {Promise<{success, sql, explanation, results, error, retries_used}>}
 */
export async function askQuestion(question, sessionId) {
  const response = await apiClient.post('/api/query', { 
    question,
    session_id: sessionId 
  })
  return response.data
}

/**
 * Fetch the schema browser list (table names, descriptions, columns) for the session.
 * @param {string} sessionId - The session ID.
 * @returns {Promise<{tables: Array<{table_name, description, columns}>}>}
 */
export async function fetchSchema(sessionId) {
  const response = await apiClient.get(`/api/schema?session_id=${sessionId}`)
  return response.data
}

/**
 * Upload dataset CSV files to the session.
 * @param {string} sessionId - The session ID.
 * @param {FileList|Array<File>} files - The list of CSV files.
 * @returns {Promise<{status, tables: Array}>}
 */
export async function uploadDataset(sessionId, files) {
  const formData = new FormData()
  formData.append('session_id', sessionId)
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i])
  }
  
  const response = await apiClient.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

/**
 * Clears the session dataset from the server.
 * @param {string} sessionId - The session ID.
 * @returns {Promise<{status}>}
 */
export async function clearDataset(sessionId) {
  const response = await apiClient.post('/api/clear', { session_id: sessionId })
  return response.data
}

/**
 * Loads the pre-packaged Olist e-commerce sample dataset into the session.
 * @param {string} sessionId - The session ID.
 * @returns {Promise<{status, tables: Array}>}
 */
export async function loadSampleDataset(sessionId) {
  const response = await apiClient.post('/api/sample', { session_id: sessionId })
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
