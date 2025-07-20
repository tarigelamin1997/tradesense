import { writable, derived } from 'svelte/store';
import { websocket } from './websocket';
import { browser } from '$app/environment';

export interface Notification {
	id: string;
	type: 'success' | 'error' | 'warning' | 'info';
	title: string;
	message: string;
	timestamp: Date;
	read: boolean;
}

function createNotificationStore() {
	const { subscribe, set, update } = writable<Notification[]>([]);
	
	let notificationCounter = 0;
	
	function addNotification(notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) {
		const newNotification: Notification = {
			...notification,
			id: `notif-${Date.now()}-${notificationCounter++}`,
			timestamp: new Date(),
			read: false
		};
		
		update(notifications => [newNotification, ...notifications]);
		
		// Auto-remove after 10 seconds for non-error notifications
		if (notification.type !== 'error') {
			setTimeout(() => {
				removeNotification(newNotification.id);
			}, 10000);
		}
		
		// Show browser notification if permitted
		if (browser && 'Notification' in window && Notification.permission === 'granted') {
			new Notification(notification.title, {
				body: notification.message,
				icon: '/favicon.ico'
			});
		}
	}
	
	function removeNotification(id: string) {
		update(notifications => notifications.filter(n => n.id !== id));
	}
	
	function markAsRead(id: string) {
		update(notifications => 
			notifications.map(n => 
				n.id === id ? { ...n, read: true } : n
			)
		);
	}
	
	function clearAll() {
		set([]);
	}
	
	// Subscribe to WebSocket notifications only in browser
	if (browser) {
		websocket.subscribe(ws => {
			if (ws.lastMessage?.type === 'notification') {
				const data = ws.lastMessage.data;
				addNotification({
					type: data.severity || 'info',
					title: data.title,
					message: data.message
				});
			}
			
			// Handle trade updates as notifications
			if (ws.lastMessage?.type === 'trade_update') {
				const data = ws.lastMessage.data;
				const action = data.action || 'updated';
				addNotification({
					type: 'success',
					title: `Trade ${action}`,
					message: `Trade ${data.trade?.symbol || ''} has been ${action}`
				});
			}
			
			// Handle performance alerts
			if (ws.lastMessage?.type === 'performance_alert') {
				const data = ws.lastMessage.data;
				addNotification({
					type: data.severity || 'warning',
					title: 'Performance Alert',
					message: data.message
				});
			}
		});
	}
	
	return {
		subscribe,
		addNotification,
		removeNotification,
		markAsRead,
		clearAll
	};
}

export const notifications = createNotificationStore();

// Derived store for unread count
export const unreadCount = derived(
	notifications,
	$notifications => $notifications.filter(n => !n.read).length
);

// IMPORTANT: Do not request notification permission at module level
// This prevents SSR errors on Vercel
// Request permission from components/layouts using requestNotificationPermission()
export function requestNotificationPermission() {
	if (browser && 'Notification' in window) {
		if (Notification.permission === 'default') {
			return Notification.requestPermission();
		}
	}
	return Promise.resolve(Notification.permission);
}