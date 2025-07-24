<script lang="ts">
	import { 
		Plus, Search, Filter, Clock, CheckCircle, 
		AlertCircle, MessageSquare, ChevronRight
	} from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	interface Ticket {
		id: string;
		subject: string;
		status: 'open' | 'in_progress' | 'resolved' | 'closed';
		priority: 'low' | 'medium' | 'high' | 'urgent';
		createdAt: Date;
		updatedAt: Date;
		lastMessage: string;
		unreadCount: number;
	}

	let tickets: Ticket[] = [
		{
			id: '1',
			subject: 'Unable to import trades from Interactive Brokers',
			status: 'in_progress',
			priority: 'high',
			createdAt: new Date('2024-01-20'),
			updatedAt: new Date('2024-01-21'),
			lastMessage: 'We\'re looking into this issue and will update you soon.',
			unreadCount: 1
		},
		{
			id: '2',
			subject: 'Question about subscription billing',
			status: 'resolved',
			priority: 'medium',
			createdAt: new Date('2024-01-18'),
			updatedAt: new Date('2024-01-19'),
			lastMessage: 'Your subscription has been updated successfully.',
			unreadCount: 0
		}
	];

	let searchQuery = '';
	let filterStatus = 'all';
	let loading = false;

	$: filteredTickets = tickets.filter(ticket => {
		const matchesSearch = !searchQuery || 
			ticket.subject.toLowerCase().includes(searchQuery.toLowerCase());
		const matchesStatus = filterStatus === 'all' || ticket.status === filterStatus;
		return matchesSearch && matchesStatus;
	});

	function getStatusIcon(status: string) {
		switch (status) {
			case 'open':
			case 'in_progress':
				return AlertCircle;
			case 'resolved':
			case 'closed':
				return CheckCircle;
			default:
				return Clock;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'open':
				return 'text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30';
			case 'in_progress':
				return 'text-blue-600 dark:text-blue-400 bg-blue-100 dark:bg-blue-900/30';
			case 'resolved':
				return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
			case 'closed':
				return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30';
			default:
				return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-900/30';
		}
	}

	function getPriorityColor(priority: string) {
		switch (priority) {
			case 'urgent':
				return 'text-red-600 dark:text-red-400';
			case 'high':
				return 'text-orange-600 dark:text-orange-400';
			case 'medium':
				return 'text-yellow-600 dark:text-yellow-400';
			case 'low':
				return 'text-gray-600 dark:text-gray-400';
			default:
				return 'text-gray-600 dark:text-gray-400';
		}
	}

	function formatDate(date: Date) {
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const days = Math.floor(diff / (1000 * 60 * 60 * 24));
		
		if (days === 0) return 'Today';
		if (days === 1) return 'Yesterday';
		if (days < 7) return `${days} days ago`;
		return date.toLocaleDateString();
	}
</script>

<svelte:head>
	<title>Support Tickets - TradeSense</title>
	<meta name="description" content="View and manage your support tickets with TradeSense." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center justify-between">
				<div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						Support Tickets
					</h1>
					<p class="text-gray-600 dark:text-gray-400 mt-1">
						Track and manage your support requests
					</p>
				</div>
				<button
					on:click={() => goto('/support/tickets/new')}
					class="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
				>
					<Plus class="h-5 w-5" />
					New Ticket
				</button>
			</div>
		</div>
	</div>

	<!-- Filters -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
		<div class="flex flex-col sm:flex-row gap-4">
			<!-- Search -->
			<div class="flex-1 relative">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search tickets..."
					class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				/>
				<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
			</div>

			<!-- Status Filter -->
			<div class="flex items-center gap-2">
				<Filter class="h-5 w-5 text-gray-400" />
				<select
					bind:value={filterStatus}
					class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
				>
					<option value="all">All Status</option>
					<option value="open">Open</option>
					<option value="in_progress">In Progress</option>
					<option value="resolved">Resolved</option>
					<option value="closed">Closed</option>
				</select>
			</div>
		</div>
	</div>

	<!-- Tickets List -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
		{#if loading}
			<div class="flex justify-center py-12">
				<LoadingSpinner size="lg" />
			</div>
		{:else if filteredTickets.length === 0}
			<div class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg">
				<MessageSquare class="h-12 w-12 text-gray-400 mx-auto mb-4" />
				<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
					No tickets found
				</h3>
				<p class="text-gray-600 dark:text-gray-400 mb-6">
					{#if searchQuery}
						No tickets match your search criteria.
					{:else if filterStatus !== 'all'}
						No {filterStatus.replace('_', ' ')} tickets.
					{:else}
						You haven't created any support tickets yet.
					{/if}
				</p>
				{#if filteredTickets.length === 0 && !searchQuery && filterStatus === 'all'}
					<button
						on:click={() => goto('/support/tickets/new')}
						class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
					>
						<Plus class="h-5 w-5" />
						Create Your First Ticket
					</button>
				{/if}
			</div>
		{:else}
			<div class="space-y-4">
				{#each filteredTickets as ticket}
					<a
						href="/support/tickets/{ticket.id}"
						class="block bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow p-6"
					>
						<div class="flex items-start justify-between">
							<div class="flex-1">
								<div class="flex items-start gap-4">
									<div class="p-2 rounded-lg {getStatusColor(ticket.status)}">
										<svelte:component this={getStatusIcon(ticket.status)} class="h-5 w-5" />
									</div>
									<div class="flex-1">
										<div class="flex items-center gap-3 mb-2">
											<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
												{ticket.subject}
											</h3>
											{#if ticket.unreadCount > 0}
												<span class="px-2 py-1 bg-blue-600 text-white text-xs rounded-full">
													{ticket.unreadCount} new
												</span>
											{/if}
										</div>
										<p class="text-gray-600 dark:text-gray-400 mb-3">
											{ticket.lastMessage}
										</p>
										<div class="flex items-center gap-4 text-sm">
											<span class="capitalize px-2 py-1 rounded {getStatusColor(ticket.status)}">
												{ticket.status.replace('_', ' ')}
											</span>
											<span class="capitalize {getPriorityColor(ticket.priority)}">
												{ticket.priority} priority
											</span>
											<span class="text-gray-500 dark:text-gray-400">
												Updated {formatDate(ticket.updatedAt)}
											</span>
										</div>
									</div>
								</div>
							</div>
							<ChevronRight class="h-5 w-5 text-gray-400 shrink-0" />
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Help Section -->
	<section class="py-16 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20">
		<div class="max-w-4xl mx-auto text-center">
			<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
				Need immediate assistance?
			</h2>
			<p class="text-gray-600 dark:text-gray-400 mb-6">
				Check our knowledge base for instant answers or start a live chat.
			</p>
			<div class="flex flex-wrap justify-center gap-4">
				<a
					href="/support/kb"
					class="px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium border border-gray-300 dark:border-gray-600"
				>
					Browse Knowledge Base
				</a>
				<button
					class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
				>
					Start Live Chat
				</button>
			</div>
		</div>
	</section>
</div>