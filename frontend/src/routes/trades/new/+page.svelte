<script lang="ts">
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/api/auth';
	import { get } from 'svelte/store';
	import { onMount } from 'svelte';
	import TradeForm from '$lib/components/TradeForm.svelte';

	let showForm = true;

	onMount(() => {
		if (!get(isAuthenticated)) {
			goto('/login');
		}
	});

	function handleSave(event: CustomEvent) {
		// Trade saved, redirect back to trade log
		goto('/tradelog');
	}

	function handleClose() {
		goto('/tradelog');
	}
</script>

<svelte:head>
	<title>Add New Trade - TradeSense</title>
</svelte:head>

<div class="trade-entry-page">
	<header class="page-header">
		<h1>Add New Trade</h1>
		<p>Record your trading activity</p>
	</header>

	<TradeForm 
		show={showForm}
		on:save={handleSave}
		on:close={handleClose}
	/>
</div>

<style>
	.trade-entry-page {
		max-width: 800px;
		margin: 0 auto;
		padding-bottom: 4rem;
	}

	.page-header {
		margin-bottom: 2rem;
		text-align: center;
	}

	.page-header h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}

	.page-header p {
		color: #666;
	}
</style>