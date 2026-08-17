import axios from 'axios'
import { apiBase } from './apiBase'

const api = axios.create({ baseURL: apiBase })

export default api
