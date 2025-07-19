<script lang="ts">
	import { notifications, unreadCount } from '$lib/stores/notifications';
	import { Bell, X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-svelte';
	import { fly, fade } from 'svelte/transition';
	
	let showNotifications = false;
	
	function getIcon(type: string) {
		switch (type) {
			case 'success': return CheckCircle;
			case 'error': return AlertCircle;
			case 'warning': return AlertTriangle;
			default: return Info;
		}
	}
	
	function getIconColor(type: string) {
		switch (type) {
			case 'success': return '#10b981';
			case 'error': return '#ef4444';
			case 'warning': return '#f59e0b';
			default: return '#3b82f6';
		}
	}
	
	function handleNotificationClick(id: string) {
		notifications.markAsRead(id);
	}
	
	function handleRemove(id: string) {
		notifications.removeNotification(id);
	}
	
	function handleClearAll() {
		notifications.clearAll();
		showNotifications = false;
	}
	
	// Close when clicking outside
	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.notification-center')) {
			showNotifications = false;
		}
	}
</script>

<svelte:window on:click={handleClickOutside} />

<div class="notification-center">
	<button 
		class="notification-bell"
		class:has-unread={$unreadCount > 0}
		on:click|stopPropagation={() => showNotifications = !showNotifications}
		aria-label="Notifications {$unreadCount > 0 ? `(${$unreadCount} unread)` : ''}"
		aria-expanded={showNotifications}
		aria-haspopup="true"
	>
		<Bell size={20} />
		{#if $unreadCount > 0}
			<span class="badge">{$unreadCount}</span>
		{/if}
	</button>
	
	{#if showNotifications}
		<div 
			class="notification-dropdown"
			transition:fly={{ y: -10, duration: 200 }}
			on:click|stopPropagation
			role="dialog"
			aria-label="Notifications panel"
		>
			<div class="dropdown-header">
				<h3>Notifications</h3>
				{#if $notifications.length > 0}
					<button class="clear-all" on:click={handleClearAll}>
						Clear all
					</button>
				{/if}
			</div>
			
			<div class="notification-list">
				{#if $notifications.length === 0}
					<div class="empty-state">
						<Bell size={32} />
						<p>No notifications</p>
					</div>
				{:else}
					{#each $notifications as notification (notification.id)}
						<button 
							class="notification-item"
							class:unread={!notification.read}
							on:click={() => handleNotificationClick(notification.id)}
							transition:fade={{ duration: 200 }}
							aria-label="Mark notification as read"
						>
							<div class="notification-icon">
								<svelte:component 
									this={getIcon(notification.type)} 
									size={20} 
									color={getIconColor(notification.type)}
								/>
							</div>
							<div class="notification-content">
								<h4>{notification.title}</h4>
								<p>{notification.message}</p>
								<span class="timestamp">
									{notification.timestamp.toLocaleTimeString()}
								</span>
							</div>
							<button 
								class="remove-btn"
								on:click|stopPropagation={() => handleRemove(notification.id)}
								aria-label="Remove notification"
							>
								<X size={16} />
							</button>
						</button>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.notification-center {
		position: relative;
	}
	
	.notification-bell {
		position: relative;
		background: none;
		border: none;
		padding: 0.5rem;
		cursor: pointer;
		color: #666;
		transition: color 0.2s;
		border-radius: 50%;
	}
	
	.notification-bell:hover {
		color: #333;
		background: #f3f4f6;
	}
	
	.notification-bell.has-unread {
		color: #3b82f6;
	}
	
	.badge {
		position: absolute;
		top: 0;
		right: 0;
		background: #ef4444;
		color: white;
		font-size: 0.7rem;
		font-weight: 600;
		padding: 0.125rem 0.375rem;
		border-radius: 10px;
		min-width: 18px;
		text-align: center;
	}
	
	.notification-dropdown {
		position: absolute;
		top: 100%;
		right: 0;
		margin-top: 0.5rem;
		width: 380px;
		max-width: 90vw;
		background: white;
		border-radius: 12px;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
		z-index: 1000;
		overflow: hidden;
	}
	
	.dropdown-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 1.5rem;
		border-bottom: 1px solid #e5e7eb;
	}
	
	.dropdown-header h3 {
		margin: 0;
		font-size: 1.125rem;
		color: #111827;
	}
	
	.clear-all {
		background: none;
		border: none;
		color: #6b7280;
		font-size: 0.875rem;
		cursor: pointer;
		transition: color 0.2s;
	}
	
	.clear-all:hover {
		color: #3b82f6;
	}
	
	.notification-list {
		max-height: 400px;
		overflow-y: auto;
	}
	
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 3rem 1.5rem;
		color: #9ca3af;
	}
	
	.empty-state p {
		margin: 0;
		font-size: 0.875rem;
	}
	
	.notification-item {
		display: flex;
		gap: 1rem;
		padding: 1rem 1.5rem;
		border-bottom: 1px solid #f3f4f6;
		cursor: pointer;
		transition: background-color 0.2s;
		position: relative;
		width: 100%;
		background: transparent;
		border: none;
		text-align: left;
		font-family: inherit;
	}
	
	.notification-item:hover {
		background: #f9fafb;
	}
	
	.notification-item.unread {
		background: #f0f9ff;
	}
	
	.notification-item.unread::before {
		content: '';
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		width: 3px;
		background: #3b82f6;
	}
	
	.notification-icon {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		background: #f3f4f6;
		border-radius: 50%;
	}
	
	.notification-content {
		flex: 1;
		min-width: 0;
	}
	
	.notification-content h4 {
		margin: 0 0 0.25rem 0;
		font-size: 0.875rem;
		font-weight: 600;
		color: #111827;
	}
	
	.notification-content p {
		margin: 0 0 0.25rem 0;
		font-size: 0.875rem;
		color: #6b7280;
		line-height: 1.4;
	}
	
	.timestamp {
		font-size: 0.75rem;
		color: #9ca3af;
	}
	
	.remove-btn {
		position: absolute;
		top: 1rem;
		right: 1rem;
		background: none;
		border: none;
		color: #9ca3af;
		cursor: pointer;
		padding: 0.25rem;
		border-radius: 4px;
		opacity: 0;
		transition: all 0.2s;
	}
	
	.notification-item:hover .remove-btn {
		opacity: 1;
	}
	
	.remove-btn:hover {
		background: #f3f4f6;
		color: #6b7280;
	}
	
	@media (max-width: 640px) {
		.notification-dropdown {
			position: fixed;
			top: auto;
			bottom: 0;
			left: 0;
			right: 0;
			width: 100%;
			max-width: 100%;
			border-radius: 12px 12px 0 0;
			max-height: 70vh;
		}
		
		.notification-list {
			max-height: calc(70vh - 60px);
		}
	}
</style>