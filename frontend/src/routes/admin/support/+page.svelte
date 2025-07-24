<script lang="ts">
	import { 
		MessageSquare, Clock, CheckCircle, XCircle,
		AlertCircle, Search, Filter, User, Calendar
	} from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	interface SupportTicket {
		id: string;
		user: {
			name: string;
			email: string;
			tier: string;
		};
		subject: string;
		status: 'open' | 'in_progress' | 'resolved' | 'closed';
		priority: 'low' | 'medium' | 'high' | 'urgent';
		category: string;
		createdAt: Date;
		updatedAt: Date;
		assignedTo?: string;
		messages: number;
	}

	let tickets: SupportTicket[] = [
		{
			id: 'TICK-1234',
			user: {
				name: 'John Doe',
				email: 'john@example.com',
				tier: 'Professional'
			},
			subject: 'Unable to export trades to CSV',
			status: 'open',
			priority: 'high',
			category: 'Technical',
			createdAt: new Date('2024-01-22T10:00:00'),
			updatedAt: new Date('2024-01-22T10:00:00'),
			messages: 1
		},
		{
			id: 'TICK-1233',
			user: {
				name: 'Jane Smith',
				email: 'jane@example.com',
				tier: 'Starter'
			},
			subject: 'Question about subscription upgrade',
			status: 'in_progress',
			priority: 'medium',
			category: 'Billing',
			createdAt: new Date('2024-01-21T14:30:00'),
			updatedAt: new Date('2024-01-22T09:15:00'),
			assignedTo: 'Support Agent 1',
			messages: 3
		},
		{
			id: 'TICK-1232',
			user: {
				name: 'Bob Johnson',
				email: 'bob@example.com',
				tier: 'Enterprise'
			},
			subject: 'API rate limit increase request',
			status: 'resolved',
			priority: 'urgent',
			category: 'API',
			createdAt: new Date('2024-01-20T08:00:00'),
			updatedAt: new Date('2024-01-21T16:45:00'),
			assignedTo: 'Support Agent 2',
			messages: 5
		}
	];

	let searchQuery = '';
	let filterStatus = 'all';
	let filterPriority = 'all';
	let loading = false;

	$: filteredTickets = tickets.filter(ticket => {
		const matchesSearch = !searchQuery || 
			ticket.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
			ticket.user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			ticket.user.email.toLowerCase().includes(searchQuery.toLowerCase());
		
		const matchesStatus = filterStatus === 'all' || ticket.status === filterStatus;
		const matchesPriority = filterPriority === 'all' || ticket.priority === filterPriority;
		
		return matchesSearch && matchesStatus && matchesPriority;
	});

	$: stats = {
		open: tickets.filter(t => t.status === 'open').length,
		inProgress: tickets.filter(t => t.status === 'in_progress').length,
		resolved: tickets.filter(t => t.status === 'resolved').length,
		avgResponseTime: '2.5 hours'
	};

	function getStatusIcon(status: string) {
		switch (status) {
			case 'open': return AlertCircle;
			case 'in_progress': return Clock;
			case 'resolved': return CheckCircle;
			case 'closed': return XCircle;
			default: return MessageSquare;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'open': return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30';
			case 'in_progress': return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30';
			case 'resolved': return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30';
			case 'closed': return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30';
			default: return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/30';
		}
	}

	function getPriorityColor(priority: string) {
		switch (priority) {
			case 'urgent': return 'text-red-600 dark:text-red-400';
			case 'high': return 'text-orange-600 dark:text-orange-400';
			case 'medium': return 'text-yellow-600 dark:text-yellow-400';
			case 'low': return 'text-green-600 dark:text-green-400';
			default: return 'text-gray-600 dark:text-gray-400';
		}
	}

	function formatTime(date: Date) {
		const now = new Date();
		const diff = now.getTime() - date.getTime();
		const hours = Math.floor(diff / (1000 * 60 * 60));
		
		if (hours < 1) return 'Just now';
		if (hours < 24) return `${hours}h ago`;
		const days = Math.floor(hours / 24);
		if (days === 1) return 'Yesterday';
		return `${days} days ago`;
	}
</script>

<svelte:head>
	<title>Support Tickets - Admin Dashboard</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-white dark:bg-gray-800 shadow-sm">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
				Support Management
			</h1>
			<p class="text-gray-600 dark:text-gray-400 mt-1">
				Manage customer support tickets and inquiries
			</p>
		</div>
	</div>

	<!-- Stats -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
		<div class="grid grid-cols-1 md:grid-cols-4 gap-4">
			<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm text-gray-600 dark:text-gray-400">Open Tickets</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">{stats.open}</p>
					</div>
					<div class="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-lg">
						<AlertCircle class="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
					</div>
				</div>
			</div>
			
			<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm text-gray-600 dark:text-gray-400">In Progress</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">{stats.inProgress}</p>
					</div>
					<div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
						<Clock class="h-6 w-6 text-blue-600 dark:text-blue-400" />
					</div>
				</div>
			</div>
			
			<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm text-gray-600 dark:text-gray-400">Resolved Today</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">{stats.resolved}</p>
					</div>
					<div class="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
						<CheckCircle class="h-6 w-6 text-green-600 dark:text-green-400" />
					</div>
				</div>
			</div>
			
			<div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm">
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm text-gray-600 dark:text-gray-400">Avg Response</p>
						<p class="text-2xl font-bold text-gray-900 dark:text-white">{stats.avgResponseTime}</p>
					</div>
					<div class="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
						<MessageSquare class="h-6 w-6 text-purple-600 dark:text-purple-400" />
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Filters -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-4">
		<div class="flex flex-col md:flex-row gap-4">
			<div class="flex-1 relative">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search tickets..."
					class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
				/>
				<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
			</div>
			
			<select
				bind:value={filterStatus}
				class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
			>
				<option value="all">All Status</option>
				<option value="open">Open</option>
				<option value="in_progress">In Progress</option>
				<option value="resolved">Resolved</option>
				<option value="closed">Closed</option>
			</select>
			
			<select
				bind:value={filterPriority}
				class="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
			>
				<option value="all">All Priorities</option>
				<option value="urgent">Urgent</option>
				<option value="high">High</option>
				<option value="medium">Medium</option>
				<option value="low">Low</option>
			</select>
		</div>
	</div>

	<!-- Tickets Table -->
	<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
		{#if loading}
			<div class="flex justify-center py-12">
				<LoadingSpinner size="lg" />
			</div>
		{:else}
			<div class="bg-white dark:bg-gray-800 shadow-sm rounded-lg overflow-hidden">
				<table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
					<thead class="bg-gray-50 dark:bg-gray-900">
						<tr>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
								Ticket
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
								Customer
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
								Status
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
								Priority
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
								Assigned To
							</th>
							<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
								Updated
							</th>
							<th class="relative px-6 py-3">
								<span class="sr-only">Actions</span>
							</th>
						</tr>
					</thead>
					<tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
						{#each filteredTickets as ticket}
							<tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
								<td class="px-6 py-4 whitespace-nowrap">
									<div>
										<p class="text-sm font-medium text-gray-900 dark:text-white">
											{ticket.id}
										</p>
										<p class="text-sm text-gray-600 dark:text-gray-400 truncate max-w-xs">
											{ticket.subject}
										</p>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<div class="flex items-center">
										<div class="flex-shrink-0 h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
											<User class="h-4 w-4 text-gray-500 dark:text-gray-400" />
										</div>
										<div class="ml-3">
											<p class="text-sm font-medium text-gray-900 dark:text-white">
												{ticket.user.name}
											</p>
											<p class="text-xs text-gray-500 dark:text-gray-400">
												{ticket.user.tier}
											</p>
										</div>
									</div>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full {getStatusColor(ticket.status)}">
										<svelte:component this={getStatusIcon(ticket.status)} class="h-3 w-3" />
										{ticket.status.replace('_', ' ')}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap">
									<span class="text-sm font-medium capitalize {getPriorityColor(ticket.priority)}">
										{ticket.priority}
									</span>
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
									{ticket.assignedTo || 'Unassigned'}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
									{formatTime(ticket.updatedAt)}
								</td>
								<td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
									<a href="/admin/support/{ticket.id}" class="text-blue-600 dark:text-blue-400 hover:underline">
										View
									</a>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
				
				{#if filteredTickets.length === 0}
					<div class="text-center py-12">
						<MessageSquare class="h-12 w-12 text-gray-400 mx-auto mb-4" />
						<p class="text-gray-500 dark:text-gray-400">No tickets found</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>