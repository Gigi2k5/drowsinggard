const DEFAULT_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

export class ApiClient {
	constructor(baseUrl = DEFAULT_BASE_URL) {
		this.baseUrl = baseUrl.replace(/\/$/, '');
	}

	async request(path, options = {}) {
		const url = `${this.baseUrl}${path}`;
		
		// Récupérer le token d'authentification
		const token = localStorage.getItem('authToken');
		
		// Préparer les headers avec authentification si disponible
		const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}
		
		// Préparer les options de fetch
		const fetchOptions = {
			headers,
			...options
		};
		
		// Convertir le body en JSON si présent
		if (options.body && typeof options.body === 'object') {
			fetchOptions.body = JSON.stringify(options.body);
		}
		
		const response = await fetch(url, fetchOptions);
		const data = await response.json().catch(() => null);
		
		if (!response.ok) {
			throw new Error((data && (data.error || data.message)) || `HTTP ${response.status}: ${response.statusText}`);
		}
		return data;
	}

	predict(image) {
		return this.request('/predict', { method: 'POST', body: JSON.stringify({ image }) });
	}

	saveSession(session) {
		return this.request('/save_session', { method: 'POST', body: JSON.stringify(session) });
	}

	getSessions(limit = 10) {
		const params = new URLSearchParams({ limit: String(limit) });
		return this.request(`/get_sessions?${params.toString()}`);
	}

	deleteSession(id) {
		return this.request(`/delete_session/${id}`, { method: 'DELETE' });
	}

	clearSessions() {
		return this.request('/clear_sessions', { method: 'DELETE' });
	}

	health() {
		return this.request('/health');
	}
}

export const api = new ApiClient();


