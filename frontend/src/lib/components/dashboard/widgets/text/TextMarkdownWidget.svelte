<script lang="ts">
  import { onMount } from 'svelte';
  import { marked } from 'marked';
  
  export let content: string = '# Welcome to TradeSense\n\nEdit this text to add notes, strategies, or insights to your dashboard.';
  export let isEditing: boolean = false;
  export let onSave: ((content: string) => void) | null = null;
  
  let editContent = content;
  let htmlContent = '';
  
  $: {
    // Convert markdown to HTML
    htmlContent = marked(content);
  }
  
  function startEdit() {
    isEditing = true;
    editContent = content;
  }
  
  function saveEdit() {
    content = editContent;
    isEditing = false;
    onSave?.(content);
  }
  
  function cancelEdit() {
    editContent = content;
    isEditing = false;
  }
  
  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      cancelEdit();
    } else if (e.key === 's' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      saveEdit();
    }
  }
</script>

<div class="text-widget">
  {#if isEditing}
    <div class="edit-mode">
      <textarea 
        bind:value={editContent}
        on:keydown={handleKeydown}
        placeholder="Enter markdown text..."
        autofocus
      />
      <div class="edit-actions">
        <button class="save-button" on:click={saveEdit}>
          Save
        </button>
        <button class="cancel-button" on:click={cancelEdit}>
          Cancel
        </button>
      </div>
    </div>
  {:else}
    <div 
      class="markdown-content"
      on:dblclick={startEdit}
      title="Double-click to edit"
    >
      {@html htmlContent}
    </div>
  {/if}
</div>

<style>
  .text-widget {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  .edit-mode {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  textarea {
    flex: 1;
    padding: 1rem;
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', monospace;
    font-size: 0.875rem;
    resize: none;
    outline: none;
  }
  
  textarea:focus {
    border-color: #10b981;
  }
  
  .edit-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 0.5rem;
  }
  
  .save-button,
  .cancel-button {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
  }
  
  .save-button {
    background: #10b981;
    color: white;
  }
  
  .save-button:hover {
    background: #059669;
  }
  
  .cancel-button {
    background: #f3f4f6;
    color: #374151;
  }
  
  .cancel-button:hover {
    background: #e5e7eb;
  }
  
  .markdown-content {
    padding: 1rem;
    overflow: auto;
    height: 100%;
    cursor: text;
  }
  
  /* Markdown styles */
  .markdown-content :global(h1) {
    font-size: 1.875rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
    color: #111827;
  }
  
  .markdown-content :global(h2) {
    font-size: 1.5rem;
    font-weight: 600;
    margin: 1.5rem 0 0.75rem 0;
    color: #1f2937;
  }
  
  .markdown-content :global(h3) {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 1.25rem 0 0.5rem 0;
    color: #374151;
  }
  
  .markdown-content :global(p) {
    margin: 0.5rem 0;
    line-height: 1.6;
    color: #4b5563;
  }
  
  .markdown-content :global(ul),
  .markdown-content :global(ol) {
    margin: 0.5rem 0;
    padding-left: 1.5rem;
    color: #4b5563;
  }
  
  .markdown-content :global(li) {
    margin: 0.25rem 0;
    line-height: 1.6;
  }
  
  .markdown-content :global(code) {
    background: #f3f4f6;
    padding: 0.125rem 0.375rem;
    border-radius: 4px;
    font-size: 0.875rem;
    color: #dc2626;
  }
  
  .markdown-content :global(pre) {
    background: #1f2937;
    color: #e5e7eb;
    padding: 1rem;
    border-radius: 6px;
    overflow-x: auto;
    margin: 1rem 0;
  }
  
  .markdown-content :global(pre code) {
    background: none;
    color: inherit;
    padding: 0;
  }
  
  .markdown-content :global(blockquote) {
    border-left: 4px solid #10b981;
    padding-left: 1rem;
    margin: 1rem 0;
    color: #6b7280;
    font-style: italic;
  }
  
  .markdown-content :global(a) {
    color: #10b981;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s;
  }
  
  .markdown-content :global(a:hover) {
    border-bottom-color: #10b981;
  }
  
  .markdown-content :global(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
  }
  
  .markdown-content :global(th),
  .markdown-content :global(td) {
    padding: 0.5rem;
    border: 1px solid #e5e7eb;
    text-align: left;
  }
  
  .markdown-content :global(th) {
    background: #f9fafb;
    font-weight: 600;
    color: #374151;
  }
  
  .markdown-content :global(hr) {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 2rem 0;
  }
</style>