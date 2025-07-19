<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	
	export let selectedMood: string = '';
	export let confidence: number = 5;
	
	const dispatch = createEventDispatcher();
	
	const moods = [
		{ value: 'confident', label: 'Confident', emoji: '😎', color: '#10b981' },
		{ value: 'focused', label: 'Focused', emoji: '🎯', color: '#3b82f6' },
		{ value: 'anxious', label: 'Anxious', emoji: '😰', color: '#f59e0b' },
		{ value: 'frustrated', label: 'Frustrated', emoji: '😤', color: '#ef4444' },
		{ value: 'neutral', label: 'Neutral', emoji: '😐', color: '#6b7280' },
		{ value: 'excited', label: 'Excited', emoji: '🚀', color: '#8b5cf6' }
	];
	
	function selectMood(mood: string) {
		selectedMood = mood;
		dispatch('moodChange', { mood });
	}
	
	function updateConfidence(value: number) {
		confidence = value;
		dispatch('confidenceChange', { confidence });
	}
</script>

<div class="mood-tracker">
	<div class="section">
		<h3>How are you feeling?</h3>
		<div class="mood-grid">
			{#each moods as mood}
				<button
					type="button"
					class="mood-button"
					class:selected={selectedMood === mood.value}
					style="--mood-color: {mood.color}"
					on:click={() => selectMood(mood.value)}
				>
					<span class="emoji">{mood.emoji}</span>
					<span class="label">{mood.label}</span>
				</button>
			{/each}
		</div>
	</div>
	
	<div class="section">
		<h3>Confidence Level</h3>
		<div class="confidence-slider">
			<input
				type="range"
				min="1"
				max="10"
				bind:value={confidence}
				on:input={() => updateConfidence(confidence)}
				class="slider"
			/>
			<div class="confidence-labels">
				<span>1</span>
				<span class="confidence-value">{confidence}</span>
				<span>10</span>
			</div>
		</div>
		<div class="confidence-description">
			{#if confidence <= 3}
				<p>Low confidence - Consider paper trading or smaller positions</p>
			{:else if confidence <= 6}
				<p>Moderate confidence - Proceed with normal risk management</p>
			{:else if confidence <= 8}
				<p>High confidence - Good mental state for trading</p>
			{:else}
				<p>Very high confidence - Be cautious of overconfidence bias</p>
			{/if}
		</div>
	</div>
</div>

<style>
	.mood-tracker {
		display: flex;
		flex-direction: column;
		gap: 2rem;
	}
	
	.section h3 {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 1rem;
		color: #333;
	}
	
	.mood-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
		gap: 0.75rem;
	}
	
	.mood-button {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		padding: 1rem;
		background: white;
		border: 2px solid #e0e0e0;
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.2s;
	}
	
	.mood-button:hover {
		border-color: var(--mood-color);
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}
	
	.mood-button.selected {
		border-color: var(--mood-color);
		background: var(--mood-color);
		color: white;
	}
	
	.mood-button.selected .label {
		color: white;
	}
	
	.emoji {
		font-size: 2rem;
		line-height: 1;
	}
	
	.label {
		font-size: 0.875rem;
		font-weight: 500;
		color: #666;
		transition: color 0.2s;
	}
	
	.confidence-slider {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.slider {
		width: 100%;
		height: 8px;
		border-radius: 4px;
		background: #e0e0e0;
		outline: none;
		-webkit-appearance: none;
		appearance: none;
	}
	
	.slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #10b981;
		cursor: pointer;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
		transition: all 0.2s;
	}
	
	.slider::-webkit-slider-thumb:hover {
		transform: scale(1.1);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
	}
	
	.slider::-moz-range-thumb {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: #10b981;
		cursor: pointer;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
		transition: all 0.2s;
		border: none;
	}
	
	.slider::-moz-range-thumb:hover {
		transform: scale(1.1);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
	}
	
	.confidence-labels {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.875rem;
		color: #666;
	}
	
	.confidence-value {
		font-size: 1.5rem;
		font-weight: 600;
		color: #10b981;
	}
	
	.confidence-description {
		margin-top: 1rem;
		padding: 0.75rem;
		background: #f3f4f6;
		border-radius: 6px;
		font-size: 0.875rem;
		color: #666;
	}
	
	@media (max-width: 640px) {
		.mood-grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}
</style>