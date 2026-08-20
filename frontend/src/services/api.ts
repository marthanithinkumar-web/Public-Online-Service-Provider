import axios from 'axios'
import { apiBase } from './apiBase'

// Shared API client: bounded waits prevent Render cold starts or a broken
// connection from leaving any screen in an endless loading state.
const api = axios.create({
  baseURL: apiBase,
  timeout: 15000,
  headers: { Accept: 'application/json' },
})

export default api
