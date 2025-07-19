<script lang="ts">
  import { MessageSquare, X } from 'lucide-svelte';
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';
  import FeedbackModal from './FeedbackModal.svelte';

  let showModal = false;
  let isExpanded = false;
  let pulseAnimation = true;

  // Disable pulse after first interaction
  function handleInteraction() {
    pulseAnimation = false;
    localStorage.setItem('feedback-button-seen', 'true');
  }

  onMount(() => {
    // Check if user has seen the button before
    if (localStorage.getItem('feedback-button-seen')) {
      pulseAnimation = false;
    }

    // Add keyboard shortcut
    function handleKeyPress(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'F') {
        e.preventDefault();
        showModal = true;
        handleInteraction();
      }
    }

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  });
</script>

<!-- Floating Action Button -->
<button
  class="feedback-fab"
  class:expanded={isExpanded}
  class:pulse={pulseAnimation}
  on:click={() => {
    showModal = true;
    handleInteraction();
  }}
  on:mouseenter={() => isExpanded = true}
  on:mouseleave={() => isExpanded = false}
  aria-label="Send feedback"
>
  <MessageSquare size={20} />
  {#if isExpanded}
    <span class="feedback-text">Report Issue</span>
  {/if}
</button>

<!-- Feedback Modal -->
{#if showModal}
  <FeedbackModal on:close={() => showModal = false} />
{/if}

<!-- Keyboard shortcut hint -->
{#if pulseAnimation}
  <div class="shortcut-hint">
    Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>F</kbd> to report an issue
  </div>
{/if}

<style>
  .feedback-fab {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 9999px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    cursor: pointer;
    transition: all 0.2s ease;
    font-weight: 600;
    font-size: 0.875rem;
  }

  .feedback-fab:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  }

  .feedback-fab.pulse {
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4);
    }
    70% {
      box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
    }
  }

  .feedback-text {
    overflow: hidden;
    white-space: nowrap;
    animation: slideIn 0.2s ease;
  }

  @keyframes slideIn {
    from {
      width: 0;
      opacity: 0;
    }
    to {
      width: auto;
      opacity: 1;
    }
  }

  .shortcut-hint {
    position: fixed;
    bottom: 6rem;
    right: 2rem;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    animation: fadeInOut 5s ease;
    animation-delay: 2s;
    opacity: 0;
    pointer-events: none;
  }

  @keyframes fadeInOut {
    0%, 100% { opacity: 0; }
    20%, 80% { opacity: 1; }
  }

  kbd {
    background: rgba(255, 255, 255, 0.2);
    padding: 0.125rem 0.25rem;
    border-radius: 0.25rem;
    font-family: monospace;
    font-size: 0.75rem;
  }

  /* Mobile responsiveness */
  @media (max-width: 640px) {
    .feedback-fab {
      bottom: 1rem;
      right: 1rem;
      padding: 0.625rem 0.875rem;
    }

    .shortcut-hint {
      display: none;
    }
  }
</style>