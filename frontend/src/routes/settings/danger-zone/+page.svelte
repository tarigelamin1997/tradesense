<script lang="ts">
	import { 
		AlertTriangle, Trash2, Archive, Download, 
		Power, Lock, Shield, X
	} from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	let showDeleteModal = false;
	let showDeactivateModal = false;
	let deleteConfirmation = '';
	let loading = false;

	const dangerousActions = [
		{
			id: 'export',
			title: 'Export All Data',
			description: 'Download all your data before making any destructive changes',
			icon: Download,
			action: exportAllData,
			variant: 'warning'
		},
		{
			id: 'archive',
			title: 'Archive Account',
			description: 'Temporarily disable your account. You can reactivate it anytime.',
			icon: Archive,
			action: () => showDeactivateModal = true,
			variant: 'warning'
		},
		{
			id: 'delete',
			title: 'Delete Account',
			description: 'Permanently delete your account and all associated data. This cannot be undone.',
			icon: Trash2,
			action: () => showDeleteModal = true,
			variant: 'danger'
		}
	];

	async function exportAllData() {
		loading = true;
		// Simulate export
		await new Promise(resolve => setTimeout(resolve, 2000));
		loading = false;
		// In production, this would trigger a download
		console.log('Exporting all data...');
	}

	async function deactivateAccount() {
		loading = true;
		// Simulate API call
		await new Promise(resolve => setTimeout(resolve, 1500));
		loading = false;
		showDeactivateModal = false;
		// In production, this would deactivate the account and log out
		await goto('/');
	}

	async function deleteAccount() {
		if (deleteConfirmation !== 'DELETE MY ACCOUNT') return;
		
		loading = true;
		// Simulate API call
		await new Promise(resolve => setTimeout(resolve, 2000));
		loading = false;
		showDeleteModal = false;
		// In production, this would delete the account and redirect
		await goto('/');
	}
</script>

<svelte:head>
	<title>Danger Zone - Settings</title>
	<meta name="description" content="Manage sensitive account actions for your TradeSense account." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Header -->
	<div class="bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
			<div class="flex items-center gap-3">
				<div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
					<AlertTriangle class="h-6 w-6 text-red-600 dark:text-red-400" />
				</div>
				<div>
					<h1 class="text-2xl font-bold text-gray-900 dark:text-white">
						Danger Zone
					</h1>
					<p class="text-red-600 dark:text-red-400 mt-1">
						These actions are permanent and cannot be undone
					</p>
				</div>
			</div>
		</div>
	</div>

	<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Warning Message -->
		<div class="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6 mb-8">
			<div class="flex items-start gap-3">
				<Shield class="h-6 w-6 text-yellow-600 dark:text-yellow-400 shrink-0" />
				<div>
					<h2 class="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
						Important Security Notice
					</h2>
					<p class="text-yellow-800 dark:text-yellow-200 mb-3">
						The actions on this page can significantly impact your account. Please ensure you:
					</p>
					<ul class="text-yellow-800 dark:text-yellow-200 space-y-1 list-disc list-inside">
						<li>Have exported any data you wish to keep</li>
						<li>Understand that some actions are irreversible</li>
						<li>Are certain about proceeding with these changes</li>
					</ul>
				</div>
			</div>
		</div>

		<!-- Actions -->
		<div class="space-y-6">
			{#each dangerousActions as action}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
					<div class="p-6">
						<div class="flex items-start gap-4">
							<div class="p-3 rounded-lg
								{action.variant === 'danger' 
									? 'bg-red-100 dark:bg-red-900/30' 
									: 'bg-orange-100 dark:bg-orange-900/30'}"
							>
								<svelte:component 
									this={action.icon} 
									class="h-6 w-6 {action.variant === 'danger' 
										? 'text-red-600 dark:text-red-400' 
										: 'text-orange-600 dark:text-orange-400'}" 
								/>
							</div>
							<div class="flex-1">
								<h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
									{action.title}
								</h3>
								<p class="text-gray-600 dark:text-gray-400 mb-4">
									{action.description}
								</p>
								<button
									on:click={action.action}
									disabled={loading}
									class="px-4 py-2 font-medium rounded-lg transition-colors
										{action.variant === 'danger'
											? 'bg-red-600 text-white hover:bg-red-700'
											: 'bg-orange-600 text-white hover:bg-orange-700'}
										disabled:opacity-50 disabled:cursor-not-allowed"
								>
									{action.title}
								</button>
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Additional Security Info -->
		<div class="mt-12 text-center text-sm text-gray-600 dark:text-gray-400">
			<p class="mb-2">Need help? Contact our support team before taking any irreversible actions.</p>
			<a href="/support" class="text-blue-600 dark:text-blue-400 hover:underline">
				Contact Support →
			</a>
		</div>
	</div>

	<!-- Deactivate Account Modal -->
	{#if showDeactivateModal}
		<div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
			<div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<div class="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
							<Archive class="h-6 w-6 text-orange-600 dark:text-orange-400" />
						</div>
						<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
							Archive Account
						</h2>
					</div>
					<button
						on:click={() => showDeactivateModal = false}
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
					>
						<X class="h-5 w-5" />
					</button>
				</div>

				<div class="space-y-4">
					<p class="text-gray-600 dark:text-gray-400">
						Archiving your account will:
					</p>
					<ul class="text-sm text-gray-600 dark:text-gray-400 space-y-2 list-disc list-inside">
						<li>Temporarily disable access to your account</li>
						<li>Preserve all your data and settings</li>
						<li>Allow you to reactivate anytime by logging in</li>
						<li>Stop any recurring subscriptions</li>
					</ul>
					<div class="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
						<p class="text-sm text-blue-800 dark:text-blue-200">
							<strong>Tip:</strong> This is reversible. You can reactivate your account 
							anytime by logging back in.
						</p>
					</div>
				</div>

				<div class="flex gap-3 mt-6">
					<button
						on:click={() => showDeactivateModal = false}
						class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
					>
						Cancel
					</button>
					<button
						on:click={deactivateAccount}
						disabled={loading}
						class="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50"
					>
						{#if loading}
							<LoadingSpinner size="sm" color="white" />
						{:else}
							Archive Account
						{/if}
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Delete Account Modal -->
	{#if showDeleteModal}
		<div class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
			<div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<div class="p-2 bg-red-100 dark:bg-red-900/30 rounded-lg">
							<AlertTriangle class="h-6 w-6 text-red-600 dark:text-red-400" />
						</div>
						<h2 class="text-xl font-semibold text-gray-900 dark:text-white">
							Delete Account
						</h2>
					</div>
					<button
						on:click={() => showDeleteModal = false}
						class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
					>
						<X class="h-5 w-5" />
					</button>
				</div>

				<div class="space-y-4">
					<div class="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
						<p class="text-red-800 dark:text-red-200 font-medium mb-2">
							This action is permanent and cannot be undone!
						</p>
						<p class="text-sm text-red-700 dark:text-red-300">
							All your data, including trades, analytics, and settings will be 
							permanently deleted.
						</p>
					</div>

					<p class="text-gray-600 dark:text-gray-400">
						Deleting your account will:
					</p>
					<ul class="text-sm text-gray-600 dark:text-gray-400 space-y-2 list-disc list-inside">
						<li>Permanently delete all your trading data</li>
						<li>Remove all analytics and insights</li>
						<li>Cancel any active subscriptions</li>
						<li>Delete your profile and settings</li>
					</ul>

					<div>
						<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
							Type "DELETE MY ACCOUNT" to confirm:
						</label>
						<input
							type="text"
							bind:value={deleteConfirmation}
							placeholder="DELETE MY ACCOUNT"
							class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
						/>
					</div>
				</div>

				<div class="flex gap-3 mt-6">
					<button
						on:click={() => showDeleteModal = false}
						class="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
					>
						Cancel
					</button>
					<button
						on:click={deleteAccount}
						disabled={loading || deleteConfirmation !== 'DELETE MY ACCOUNT'}
						class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{#if loading}
							<LoadingSpinner size="sm" color="white" />
						{:else}
							Delete Account
						{/if}
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>