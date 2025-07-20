import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';

type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface WebSocketMessage {
	type: 'trade_update' | 'price_update' | 'notification' | 'market_status';
	data: any;
	timestamp: string;
}

interface WebSocketState {
	status: WebSocketStatus;
	lastMessage: WebSocketMessage | null;
	error: string | null;
}

function createWebSocketStore() {
	const { subscribe, set, update } = writable<WebSocketState>({
		status: 'disconnected',
		lastMessage: null,
		error: null
	});

	let ws: WebSocket | null = null;
	let reconnectTimer: NodeJS.Timeout | null = null;
	let reconnectAttempts = 0;
	const maxReconnectAttempts = 5;
	const reconnectDelay = 3000;

	function connect() {
		if (!browser) return;
		
		// Get WebSocket URL from environment or use default
		const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
		
		try {
			update(state => ({ ...state, status: 'connecting', error: null }));
			
			ws = new WebSocket(wsUrl);
			
			ws.onopen = () => {
				console.log('WebSocket connected');
				reconnectAttempts = 0;
				update(state => ({ ...state, status: 'connected' }));
				
				// Send authentication if needed
				const token = browser ? localStorage.getItem('authToken') : null;
				if (token && ws) {
					ws.send(JSON.stringify({
						type: 'auth',
						token
					}));
				}
			};
			
			ws.onmessage = (event) => {
				try {
					const message: WebSocketMessage = JSON.parse(event.data);
					update(state => ({ ...state, lastMessage: message }));
					
					// Handle different message types
					handleMessage(message);
				} catch (error) {
					console.error('Failed to parse WebSocket message:', error);
				}
			};
			
			ws.onerror = (error) => {
				console.error('WebSocket error:', error);
				update(state => ({ 
					...state, 
					status: 'error', 
					error: 'WebSocket connection error' 
				}));
			};
			
			ws.onclose = () => {
				console.log('WebSocket disconnected');
				update(state => ({ ...state, status: 'disconnected' }));
				
				// Attempt to reconnect
				if (reconnectAttempts < maxReconnectAttempts) {
					reconnectAttempts++;
					console.log(`Reconnecting... (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
					
					reconnectTimer = setTimeout(() => {
						connect();
					}, reconnectDelay * reconnectAttempts);
				} else {
					update(state => ({ 
						...state, 
						error: 'Failed to reconnect after multiple attempts' 
					}));
				}
			};
			
		} catch (error) {
			console.error('Failed to create WebSocket connection:', error);
			update(state => ({ 
				...state, 
				status: 'error', 
				error: 'Failed to create WebSocket connection' 
			}));
		}
	}
	
	function disconnect() {
		if (reconnectTimer) {
			clearTimeout(reconnectTimer);
			reconnectTimer = null;
		}
		
		if (ws && ws.readyState === WebSocket.OPEN) {
			ws.close();
		}
		
		ws = null;
		reconnectAttempts = 0;
	}
	
	function send(message: any) {
		if (ws && ws.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify(message));
		} else {
			console.error('WebSocket is not connected');
		}
	}
	
	function handleMessage(message: WebSocketMessage) {
		// This function can be extended to handle different message types
		// and update relevant stores
		switch (message.type) {
			case 'trade_update':
				// Update trade store with new trade data
				console.log('Trade update:', message.data);
				break;
			case 'price_update':
				// Update price data
				console.log('Price update:', message.data);
				break;
			case 'notification':
				// Show notification to user
				console.log('Notification:', message.data);
				break;
			case 'market_status':
				// Update market status
				console.log('Market status:', message.data);
				break;
		}
	}
	
	return {
		subscribe,
		connect,
		disconnect,
		send
	};
}

export const websocket = createWebSocketStore();

// Derived store for connection status
export const wsConnected = derived(
	websocket,
	$ws => $ws.status === 'connected'
);

// Derived store for latest trade updates
export const tradeUpdates = derived(
	websocket,
	$ws => $ws.lastMessage?.type === 'trade_update' ? $ws.lastMessage.data : null
);

// Derived store for price updates
export const priceUpdates = derived(
	websocket,
	$ws => $ws.lastMessage?.type === 'price_update' ? $ws.lastMessage.data : null
);

// IMPORTANT: Connection should be initiated from components/layouts, not at module level
// This prevents SSR errors on Vercel
// Use websocket.connect() in onMount() or +layout.svelte