<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/api/auth';
	import { get } from 'svelte/store';
	import { journalApi, type JournalEntry } from '$lib/api/journal';
	import RichTextEditor from '$lib/components/journal/RichTextEditor.svelte';
	import MoodTracker from '$lib/components/journal/MoodTracker.svelte';
	import JournalTemplates from '$lib/components/journal/JournalTemplates.svelte';
	import JournalInsights from '$lib/components/journal/JournalInsights.svelte';
	import { Search, Calendar, Tag, Filter, X, Edit, Trash2 } from 'lucide-svelte';
	import { billingApi } from '$lib/api/billing';
	import { logger } from '$lib/utils/logger';
	import LoadingSkeleton from '$lib/components/LoadingSkeleton.svelte';
	import DataExport from '$lib/components/DataExport.svelte';
	
	let loading = true;
	let error = '';
	let entries: JournalEntry[] = [];
	let filteredEntries: JournalEntry[] = [];
	let selectedEntry: JournalEntry | null = null;
	let showEntryForm = false;
	let showTemplates = false;
	let editingEntry: JournalEntry | null = null;
	let userPlan: 'free' | 'pro' | 'enterprise' = 'free';
	
	// Search and filters
	let searchQuery = '';
	let selectedMoodFilter = '';
	let selectedDateRange = '30d';
	
	// New entry form data
	let newEntry = {
		title: '',
		content: '',
		mood: '',
		confidence: 5,
		tags: [] as string[],
		tradeIds: [] as number[]
	};
	
	let tagInput = '';
	
	async function fetchEntries() {
		try {
			loading = true;
			error = '';
			
			// Check if authenticated
			if (!get(isAuthenticated)) {
				goto('/login');
				return;
			}
			
			// Try to fetch from API and subscription
			try {
				const [journalEntries, subscription] = await Promise.all([
					journalApi.getEntries(),
					billingApi.getSubscription()
				]);
				
				entries = journalEntries;
				
				// Determine user plan
				if (subscription) {
					if (subscription.plan_id.includes('enterprise')) userPlan = 'enterprise';
					else if (subscription.plan_id.includes('pro')) userPlan = 'pro';
					else userPlan = 'free';
				}
			} catch (err) {
				// Use sample data as fallback
				entries = generateSampleEntries();
			}
			
			applyFilters();
			
		} catch (err: any) {
			logger.error('Failed to fetch journal entries:', err);
			error = 'Failed to load journal entries.';
			// Use sample data
			entries = generateSampleEntries();
			applyFilters();
		} finally {
			loading = false;
		}
	}
	
	function generateSampleEntries(): JournalEntry[] {
		return [
			{
				id: 1,
				title: 'Exceptional Trading Day - Discipline Pays Off',
				content: `<h3>Market Overview</h3>
<p>The market opened with strong bullish momentum after positive economic data. I remained patient and waited for my setups.</p>

<h3>Trades Executed</h3>
<ul>
<li><strong>AAPL Long:</strong> Entered at the breakout of the morning range. Perfect execution with 2:1 risk/reward achieved.</li>
<li><strong>TSLA Short:</strong> Identified weakness at resistance. Covered at first target for a quick profit.</li>
</ul>

<h3>Key Takeaways</h3>
<p>Patience and discipline were the keys today. By waiting for high-probability setups and managing risk properly, I achieved consistent profits.</p>`,
				mood: 'confident',
				confidence: 9,
				tags: ['disciplined', 'profitable', 'patient'],
				created_at: new Date().toISOString(),
				updated_at: new Date().toISOString()
			},
			{
				id: 2,
				title: 'Learning from Overtrading',
				content: `<h3>What Happened</h3>
<p>Started the day well but gave back profits by overtrading in the afternoon. FOMO kicked in after missing a move in NVDA.</p>

<h3>Mistakes Made</h3>
<ul>
<li>Took 3 trades without proper setups</li>
<li>Increased position size out of frustration</li>
<li>Ignored my stop loss rules on one trade</li>
</ul>

<h3>Lessons Learned</h3>
<p>Need to implement a daily trade limit. When I hit my target or max trades, I should stop for the day. Also, never trade out of FOMO.</p>`,
				mood: 'frustrated',
				confidence: 4,
				tags: ['overtrading', 'lessons', 'FOMO'],
				created_at: new Date(Date.now() - 86400000).toISOString(),
				updated_at: new Date(Date.now() - 86400000).toISOString()
			},
			{
				id: 3,
				title: 'Market Analysis - Trend Reversal Signals',
				content: `<h3>Technical Analysis</h3>
<p>Seeing potential trend reversal signals in major indices. SPY testing 50-day MA with decreasing volume.</p>

<h3>Sector Rotation</h3>
<p>Money flowing out of tech and into defensive sectors. This could signal risk-off sentiment.</p>

<h3>Trading Plan</h3>
<p>Will reduce position sizes and focus on quick scalps until trend becomes clearer. May consider some hedge positions.</p>`,
				mood: 'neutral',
				confidence: 6,
				tags: ['analysis', 'market-conditions', 'planning'],
				created_at: new Date(Date.now() - 172800000).toISOString(),
				updated_at: new Date(Date.now() - 172800000).toISOString()
			}
		];
	}
	
	function applyFilters() {
		filteredEntries = entries.filter(entry => {
			// Search filter
			if (searchQuery) {
				const query = searchQuery.toLowerCase();
				const matchesSearch = 
					entry.title.toLowerCase().includes(query) ||
					entry.content.toLowerCase().includes(query) ||
					entry.tags.some(tag => tag.toLowerCase().includes(query));
				if (!matchesSearch) return false;
			}
			
			// Mood filter
			if (selectedMoodFilter && entry.mood !== selectedMoodFilter) {
				return false;
			}
			
			// Date range filter
			if (selectedDateRange !== 'all') {
				const entryDate = new Date(entry.created_at);
				const now = new Date();
				const daysDiff = (now.getTime() - entryDate.getTime()) / (1000 * 60 * 60 * 24);
				
				switch (selectedDateRange) {
					case '7d':
						if (daysDiff > 7) return false;
						break;
					case '30d':
						if (daysDiff > 30) return false;
						break;
					case '90d':
						if (daysDiff > 90) return false;
						break;
				}
			}
			
			return true;
		});
		
		// Sort by date (newest first)
		filteredEntries.sort((a, b) => 
			new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
		);
	}
	
	function handleNewEntry() {
		showEntryForm = true;
		showTemplates = true;
		editingEntry = null;
		newEntry = {
			title: '',
			content: '',
			mood: '',
			confidence: 5,
			tags: [],
			tradeIds: []
		};
	}
	
	function handleEditEntry(entry: JournalEntry) {
		editingEntry = entry;
		newEntry = {
			title: entry.title,
			content: entry.content,
			mood: entry.mood,
			confidence: entry.confidence,
			tags: [...entry.tags],
			tradeIds: entry.trade_ids || []
		};
		showEntryForm = true;
		showTemplates = false;
	}
	
	async function handleSaveEntry() {
		try {
			if (editingEntry) {
				// Update existing entry
				await journalApi.updateEntry(editingEntry.id, {
					title: newEntry.title,
					content: newEntry.content,
					mood: newEntry.mood,
					confidence: newEntry.confidence,
					tags: newEntry.tags,
					trade_ids: newEntry.tradeIds
				});
			} else {
				// Create new entry
				await journalApi.createEntry({
					title: newEntry.title,
					content: newEntry.content,
					mood: newEntry.mood,
					confidence: newEntry.confidence,
					tags: newEntry.tags,
					trade_ids: newEntry.tradeIds
				});
			}
			
			await fetchEntries();
			handleCancelEntry();
		} catch (err) {
			logger.error('Failed to save entry:', err);
			// For demo, just add to local entries
			if (!editingEntry) {
				const newJournalEntry: JournalEntry = {
					id: Date.now(),
					...newEntry,
					created_at: new Date().toISOString(),
					updated_at: new Date().toISOString()
				};
				entries = [newJournalEntry, ...entries];
				applyFilters();
			}
			handleCancelEntry();
		}
	}
	
	async function handleDeleteEntry(id: number) {
		if (!confirm('Are you sure you want to delete this journal entry?')) return;
		
		try {
			await journalApi.deleteEntry(id);
			await fetchEntries();
		} catch (err) {
			// For demo, remove from local entries
			entries = entries.filter(e => e.id !== id);
			applyFilters();
		}
		
		if (selectedEntry?.id === id) {
			selectedEntry = null;
		}
	}
	
	function handleCancelEntry() {
		showEntryForm = false;
		showTemplates = false;
		editingEntry = null;
		newEntry = {
			title: '',
			content: '',
			mood: '',
			confidence: 5,
			tags: [],
			tradeIds: []
		};
		tagInput = '';
	}
	
	function handleTemplateSelect(event: CustomEvent<{ template: any }>) {
		const { template } = event.detail;
		newEntry.title = template.name;
		newEntry.content = template.content;
		showTemplates = false;
	}
	
	function handleMoodChange(event: CustomEvent<{ mood: string }>) {
		newEntry.mood = event.detail.mood;
	}
	
	function handleConfidenceChange(event: CustomEvent<{ confidence: number }>) {
		newEntry.confidence = event.detail.confidence;
	}
	
	function handleContentUpdate(event: CustomEvent<{ content: string }>) {
		newEntry.content = event.detail.content;
	}
	
	function addTag() {
		if (tagInput.trim() && !newEntry.tags.includes(tagInput.trim())) {
			newEntry.tags = [...newEntry.tags, tagInput.trim()];
			tagInput = '';
		}
	}
	
	function removeTag(tag: string) {
		newEntry.tags = newEntry.tags.filter(t => t !== tag);
	}
	
	function selectEntry(entry: JournalEntry) {
		selectedEntry = entry;
	}
	
	function formatDate(dateString: string) {
		const date = new Date(dateString);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
	
	function getMoodDetails(mood: string) {
		const moods: Record<string, { emoji: string; color: string }> = {
			confident: { emoji: '😎', color: '#10b981' },
			focused: { emoji: '🎯', color: '#3b82f6' },
			anxious: { emoji: '😰', color: '#f59e0b' },
			frustrated: { emoji: '😤', color: '#ef4444' },
			neutral: { emoji: '😐', color: '#6b7280' },
			excited: { emoji: '🚀', color: '#8b5cf6' }
		};
		return moods[mood] || { emoji: '😐', color: '#6b7280' };
	}
	
	// Update filters when search or filter values change
	$: if (searchQuery !== undefined || selectedMoodFilter !== undefined || selectedDateRange) {
		applyFilters();
	}
	
	onMount(() => {
		fetchEntries();
	});
</script>

<svelte:head>
	<title>Journal - TradeSense</title>
</svelte:head>

<div class="journal-page">
	<header class="page-header">
		<div>
			<h1>Trading Journal</h1>
			<p>Document your trading journey and insights</p>
		</div>
		<div class="header-actions">
			<DataExport 
				data={entries}
				filename="journal_entries"
				buttonText="Export"
			/>
			<button on:click={handleNewEntry} class="new-entry-button">
				New Entry
			</button>
		</div>
	</header>
	
	{#if loading}
		<div class="journal-skeleton">
			<!-- Filters Skeleton -->
			<div class="filters-skeleton">
				<LoadingSkeleton type="text" lines={1} width="200px" />
			</div>
			
			<!-- Entries Skeleton -->
			<div class="entries-container">
				<div class="entries-list">
					{#each Array(4) as _}
						<LoadingSkeleton type="card" height="120px" />
					{/each}
				</div>
				<div class="entry-preview">
					<LoadingSkeleton type="card" height="400px" />
				</div>
			</div>
		</div>
	{:else if error}
		<div class="error">{error}</div>
	{:else}
		{#if showEntryForm}
			<div class="entry-form-container">
				<div class="entry-form card">
					<div class="form-header">
						<h2>{editingEntry ? 'Edit' : 'New'} Journal Entry</h2>
						<button type="button" class="close-button" on:click={handleCancelEntry} aria-label="Close entry form">
							<X size={20} />
						</button>
					</div>
					
					{#if showTemplates && !editingEntry}
						<JournalTemplates on:select={handleTemplateSelect} />
					{/if}
					
					<form on:submit|preventDefault={handleSaveEntry}>
						<div class="form-group">
							<label for="title">Title</label>
							<input
								id="title"
								type="text"
								bind:value={newEntry.title}
								placeholder="Give your entry a title..."
								required
							/>
						</div>
						
						<div class="form-row">
							<div class="form-group flex-1">
								<MoodTracker 
									selectedMood={newEntry.mood}
									confidence={newEntry.confidence}
									on:moodChange={handleMoodChange}
									on:confidenceChange={handleConfidenceChange}
								/>
							</div>
						</div>
						
						<div class="form-group">
							<label for="content">Content</label>
							<RichTextEditor 
								id="content" 
								content={newEntry.content}
								placeholder="What's on your mind? Document your trades, thoughts, and lessons learned..."
								on:update={handleContentUpdate}
							/>
						</div>
						
						<div class="form-group">
							<label for="tags">Tags</label>
							<div class="tag-input-container">
								<input
									id="tags"
									type="text"
									bind:value={tagInput}
									on:keypress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
									placeholder="Add tags..."
								/>
								<button type="button" on:click={addTag} class="add-tag-button">
									Add
								</button>
							</div>
							{#if newEntry.tags.length > 0}
								<div class="tags">
									{#each newEntry.tags as tag}
										<span class="tag removable">
											{tag}
											<button type="button" on:click={() => removeTag(tag)}>×</button>
										</span>
									{/each}
								</div>
							{/if}
						</div>
						
						<div class="form-actions">
							<button type="button" on:click={handleCancelEntry} class="cancel-button">
								Cancel
							</button>
							<button type="submit" class="save-button">
								{editingEntry ? 'Update' : 'Save'} Entry
							</button>
						</div>
					</form>
				</div>
			</div>
		{:else}
			<!-- Search and Filters -->
			<div class="filters-section">
				<div class="search-container">
					<Search size={20} class="search-icon" />
					<input
						type="text"
						placeholder="Search entries..."
						bind:value={searchQuery}
						class="search-input"
					/>
				</div>
				
				<div class="filter-buttons">
					<select bind:value={selectedDateRange} class="filter-select">
						<option value="7d">Last 7 days</option>
						<option value="30d">Last 30 days</option>
						<option value="90d">Last 90 days</option>
						<option value="all">All time</option>
					</select>
					
					<select bind:value={selectedMoodFilter} class="filter-select">
						<option value="">All moods</option>
						<option value="confident">Confident</option>
						<option value="focused">Focused</option>
						<option value="anxious">Anxious</option>
						<option value="frustrated">Frustrated</option>
						<option value="neutral">Neutral</option>
						<option value="excited">Excited</option>
					</select>
				</div>
			</div>
			
			<!-- AI Insights -->
			<JournalInsights entries={filteredEntries} {userPlan} />
			
			{#if filteredEntries.length === 0}
				<div class="empty-state">
					<h2>No journal entries found</h2>
					<p>
						{searchQuery || selectedMoodFilter ? 'Try adjusting your filters' : 'Start documenting your trading journey'}
					</p>
					{#if !searchQuery && !selectedMoodFilter}
						<button on:click={handleNewEntry} class="primary-button">
							Write Your First Entry
						</button>
					{/if}
				</div>
			{:else}
				<div class="entries-layout">
					<div class="entries-list">
						{#each filteredEntries as entry}
							<button 
								class="entry-card card"
								class:selected={selectedEntry?.id === entry.id}
								on:click={() => selectEntry(entry)}
								type="button"
							>
								<div class="entry-header">
									<div class="entry-meta">
										<span class="entry-date">{formatDate(entry.created_at)}</span>
										{#if entry.confidence}
											<span class="confidence-badge">Confidence: {entry.confidence}/10</span>
										{/if}
									</div>
									<div class="entry-mood" style="color: {getMoodDetails(entry.mood).color}">
										{getMoodDetails(entry.mood).emoji}
									</div>
								</div>
								<h3>{entry.title}</h3>
								<div class="entry-preview">
									{@html entry.content.replace(/<[^>]*>/g, '').substring(0, 150)}...
								</div>
								{#if entry.tags.length > 0}
									<div class="tags">
										{#each entry.tags as tag}
											<span class="tag">{tag}</span>
										{/each}
									</div>
								{/if}
							</button>
						{/each}
					</div>
					
					{#if selectedEntry}
						<div class="entry-detail card">
							<div class="detail-header">
								<div>
									<h2>{selectedEntry.title}</h2>
									<div class="detail-meta">
										<span>{formatDate(selectedEntry.created_at)}</span>
										<span class="mood-indicator" style="color: {getMoodDetails(selectedEntry.mood).color}">
											{getMoodDetails(selectedEntry.mood).emoji} 
											{selectedEntry.mood.charAt(0).toUpperCase() + selectedEntry.mood.slice(1)}
										</span>
										{#if selectedEntry.confidence}
											<span>Confidence: {selectedEntry.confidence}/10</span>
										{/if}
									</div>
								</div>
								<div class="detail-actions">
									<button 
										type="button" 
										class="icon-button"
										on:click={() => handleEditEntry(selectedEntry)}
										title="Edit entry"
									>
										<Edit size={18} />
									</button>
									<button 
										type="button" 
										class="icon-button danger"
										on:click={() => handleDeleteEntry(selectedEntry.id)}
										title="Delete entry"
									>
										<Trash2 size={18} />
									</button>
								</div>
							</div>
							
							<div class="detail-content">
								{@html selectedEntry.content}
							</div>
							
							{#if selectedEntry.tags.length > 0}
								<div class="tags">
									{#each selectedEntry.tags as tag}
										<span class="tag">{tag}</span>
									{/each}
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/if}
		{/if}
	{/if}
</div>

<style>
	.journal-page {
		max-width: 1400px;
		margin: 0 auto;
		padding-bottom: 4rem;
	}
	
	.journal-skeleton {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	.filters-skeleton {
		margin-bottom: 1rem;
	}
	
	.journal-skeleton .entries-container {
		display: grid;
		grid-template-columns: 1fr 2fr;
		gap: 2rem;
		height: 600px;
	}
	
	.journal-skeleton .entries-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow: hidden;
	}
	
	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		flex-wrap: wrap;
		gap: 1rem;
	}
	
	.page-header h1 {
		font-size: 2rem;
		margin-bottom: 0.5rem;
	}
	
	.page-header p {
		color: #666;
	}
	
	.header-actions {
		display: flex;
		gap: 1rem;
		align-items: center;
	}
	
	.new-entry-button {
		background: #10b981;
		color: white;
		padding: 0.75rem 1.5rem;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	.new-entry-button:hover {
		background: #059669;
	}
	
	.loading {
		text-align: center;
		padding: 4rem;
		color: #666;
	}
	
	.error {
		background: #fee;
		color: #c00;
		padding: 1rem;
		border-radius: 6px;
		margin-bottom: 1rem;
	}
	
	/* Entry Form */
	.entry-form-container {
		margin-bottom: 2rem;
	}
	
	.entry-form {
		max-width: 900px;
		margin: 0 auto;
	}
	
	.form-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.form-header h2 {
		font-size: 1.5rem;
		margin: 0;
	}
	
	.close-button {
		background: none;
		border: none;
		color: #666;
		cursor: pointer;
		padding: 0.5rem;
		border-radius: 4px;
		transition: all 0.2s;
	}
	
	.close-button:hover {
		background: #f3f4f6;
		color: #333;
	}
	
	.form-group {
		margin-bottom: 1.5rem;
	}
	
	.form-group label {
		display: block;
		margin-bottom: 0.5rem;
		font-weight: 500;
		color: #333;
	}
	
	.form-group input {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 1rem;
		font-family: inherit;
	}
	
	.form-group input:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.form-row {
		display: flex;
		gap: 2rem;
		margin-bottom: 1.5rem;
	}
	
	.flex-1 {
		flex: 1;
	}
	
	.tag-input-container {
		display: flex;
		gap: 0.5rem;
	}
	
	.add-tag-button {
		padding: 0.75rem 1rem;
		background: #f3f4f6;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.add-tag-button:hover {
		background: #e5e7eb;
		border-color: #d1d5db;
	}
	
	.tags {
		display: flex;
		gap: 0.5rem;
		flex-wrap: wrap;
		margin-top: 0.75rem;
	}
	
	.tag {
		background: #e0f2fe;
		color: #0369a1;
		padding: 0.25rem 0.75rem;
		border-radius: 20px;
		font-size: 0.875rem;
	}
	
	.tag.removable {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding-right: 0.5rem;
	}
	
	.tag.removable button {
		background: none;
		border: none;
		color: #0369a1;
		cursor: pointer;
		font-size: 1.25rem;
		line-height: 1;
		padding: 0;
		opacity: 0.7;
	}
	
	.tag.removable button:hover {
		opacity: 1;
	}
	
	.form-actions {
		display: flex;
		gap: 1rem;
		justify-content: flex-end;
		margin-top: 2rem;
		padding-top: 2rem;
		border-top: 1px solid #e0e0e0;
	}
	
	.cancel-button {
		padding: 0.75rem 1.5rem;
		background: #f3f4f6;
		color: #333;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	.cancel-button:hover {
		background: #e5e7eb;
	}
	
	.save-button {
		padding: 0.75rem 1.5rem;
		background: #10b981;
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		transition: background 0.2s;
	}
	
	.save-button:hover {
		background: #059669;
	}
	
	/* Filters */
	.filters-section {
		display: flex;
		gap: 1rem;
		margin-bottom: 2rem;
		flex-wrap: wrap;
	}
	
	.search-container {
		flex: 1;
		position: relative;
		min-width: 300px;
	}
	
	:global(.search-icon) {
		position: absolute;
		left: 1rem;
		top: 50%;
		transform: translateY(-50%);
		color: #666;
		pointer-events: none;
	}
	
	.search-input {
		width: 100%;
		padding: 0.75rem 1rem 0.75rem 3rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		font-size: 1rem;
	}
	
	.search-input:focus {
		outline: none;
		border-color: #10b981;
	}
	
	.filter-buttons {
		display: flex;
		gap: 0.5rem;
	}
	
	.filter-select {
		padding: 0.75rem 1rem;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		background: white;
		font-size: 0.875rem;
		cursor: pointer;
	}
	
	.filter-select:focus {
		outline: none;
		border-color: #10b981;
	}
	
	/* Entries Layout */
	.entries-layout {
		display: grid;
		grid-template-columns: 400px 1fr;
		gap: 2rem;
		align-items: start;
	}
	
	.entries-list {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		max-height: calc(100vh - 300px);
		overflow-y: auto;
		padding-right: 0.5rem;
	}
	
	.entry-card {
		padding: 1.5rem;
		cursor: pointer;
		transition: all 0.2s;
		border: 2px solid transparent;
		width: 100%;
		text-align: left;
		background: transparent;
		font-family: inherit;
	}
	
	.entry-card:hover {
		transform: translateX(4px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}
	
	.entry-card.selected {
		border-color: #10b981;
		background: #f0fdf4;
	}
	
	.entry-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 0.75rem;
	}
	
	.entry-meta {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	
	.entry-date {
		font-size: 0.875rem;
		color: #666;
	}
	
	.confidence-badge {
		font-size: 0.75rem;
		color: #10b981;
		font-weight: 500;
	}
	
	.entry-mood {
		font-size: 1.5rem;
		line-height: 1;
	}
	
	.entry-card h3 {
		font-size: 1.125rem;
		margin-bottom: 0.5rem;
		color: #333;
		line-height: 1.4;
	}
	
	.entry-preview {
		font-size: 0.875rem;
		color: #666;
		line-height: 1.5;
		margin-bottom: 0.75rem;
	}
	
	/* Entry Detail */
	.entry-detail {
		padding: 2rem;
		position: sticky;
		top: 1rem;
		max-height: calc(100vh - 200px);
		overflow-y: auto;
	}
	
	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: 1.5rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid #e0e0e0;
	}
	
	.detail-header h2 {
		font-size: 1.75rem;
		margin-bottom: 0.5rem;
		line-height: 1.3;
	}
	
	.detail-meta {
		display: flex;
		gap: 1rem;
		font-size: 0.875rem;
		color: #666;
		align-items: center;
	}
	
	.mood-indicator {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}
	
	.detail-actions {
		display: flex;
		gap: 0.5rem;
	}
	
	.icon-button {
		padding: 0.5rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.icon-button:hover {
		background: #f3f4f6;
		border-color: #d1d5db;
		color: #333;
	}
	
	.icon-button.danger:hover {
		background: #fef2f2;
		border-color: #fecaca;
		color: #ef4444;
	}
	
	.detail-content {
		font-size: 1rem;
		line-height: 1.8;
		color: #333;
		margin-bottom: 2rem;
	}
	
	/* Rich content styles */
	.detail-content :global(h1),
	.detail-content :global(h2),
	.detail-content :global(h3) {
		margin-top: 1.5rem;
		margin-bottom: 0.75rem;
	}
	
	.detail-content :global(ul),
	.detail-content :global(ol) {
		margin: 1rem 0;
	}
	
	.detail-content :global(blockquote) {
		margin: 1rem 0;
		padding-left: 1rem;
		border-left: 3px solid #e0e0e0;
		color: #666;
		font-style: italic;
	}
	
	/* Empty State */
	.empty-state {
		text-align: center;
		padding: 4rem 2rem;
	}
	
	.empty-state h2 {
		font-size: 1.5rem;
		margin-bottom: 1rem;
		color: #666;
	}
	
	.empty-state p {
		color: #999;
		margin-bottom: 2rem;
	}
	
	.primary-button {
		background: #10b981;
		color: white;
		padding: 1rem 2rem;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1.125rem;
		transition: all 0.2s;
		text-decoration: none;
		display: inline-block;
	}
	
	.primary-button:hover {
		background: #059669;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
	}
	
	@media (max-width: 1024px) {
		.entries-layout {
			grid-template-columns: 1fr;
		}
		
		.entries-list {
			max-height: none;
		}
		
		.entry-detail {
			position: static;
		}
	}
	
	@media (max-width: 640px) {
		.journal-page {
			padding: 0 1rem 4rem;
		}
		
		.page-header {
			flex-direction: column;
			align-items: stretch;
			text-align: center;
		}
		
		.page-header h1 {
			font-size: 1.5rem;
		}
		
		.new-entry-button {
			width: 100%;
		}
		
		.form-row {
			flex-direction: column;
		}
		
		.filters-section {
			flex-direction: column;
		}
		
		.search-container {
			min-width: auto;
		}
		
		.filter-buttons {
			flex-direction: column;
			width: 100%;
		}
		
		.filter-select {
			width: 100%;
		}
		
		.entries-list {
			padding-right: 0;
		}
		
		.entry-card {
			padding: 1rem;
		}
		
		.entry-card h3 {
			font-size: 1rem;
		}
		
		.entry-detail {
			padding: 1rem;
		}
		
		.detail-header {
			flex-direction: column;
			gap: 1rem;
		}
		
		.detail-header h2 {
			font-size: 1.25rem;
		}
		
		.detail-meta {
			flex-wrap: wrap;
			font-size: 0.75rem;
		}
		
		.detail-actions {
			align-self: flex-end;
		}
		
		/* Entry form mobile styles */
		.entry-form {
			padding: 1rem;
		}
		
		.form-header h2 {
			font-size: 1.25rem;
		}
		
		.form-actions {
			flex-direction: column-reverse;
			gap: 0.5rem;
		}
		
		.form-actions button {
			width: 100%;
		}
	}
</style>