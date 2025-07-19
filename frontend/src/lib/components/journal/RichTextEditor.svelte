<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import { TextStyle } from '@tiptap/extension-text-style';
	import { Underline } from '@tiptap/extension-underline';
	import { Highlight } from '@tiptap/extension-highlight';
	import { Placeholder } from '@tiptap/extension-placeholder';
	import { 
		Bold, Italic, Underline as UnderlineIcon, Strikethrough,
		List, ListOrdered, Quote, Code, Highlighter,
		Undo, Redo, Type
	} from 'lucide-svelte';
	
	export let content = '';
	export let placeholder = 'Start writing...';
	export let editable = true;
	export let minHeight = 300;
	
	let element: HTMLElement;
	let editor: Editor;
	
	const dispatch = createEventDispatcher();
	
	onMount(() => {
		editor = new Editor({
			element,
			extensions: [
				StarterKit.configure({
					heading: {
						levels: [1, 2, 3]
					}
				}),
				TextStyle,
				Underline,
				Highlight.configure({
					multicolor: true
				}),
				Placeholder.configure({
					placeholder,
					emptyEditorClass: 'editor-empty'
				})
			],
			content,
			editable,
			onTransaction: () => {
				// Force re-render to update button states
				editor = editor;
			},
			onUpdate: ({ editor }) => {
				const html = editor.getHTML();
				dispatch('update', { content: html });
			},
			onFocus: () => {
				dispatch('focus');
			},
			onBlur: () => {
				dispatch('blur');
			}
		});
	});
	
	onDestroy(() => {
		if (editor) {
			editor.destroy();
		}
	});
	
	$: if (editor && content !== editor.getHTML()) {
		editor.commands.setContent(content);
	}
	
	$: if (editor) {
		editor.setEditable(editable);
	}
	
	function toggleHeading(level: number) {
		editor.chain().focus().toggleHeading({ level }).run();
	}
	
	function addHighlight(color: string) {
		editor.chain().focus().toggleHighlight({ color }).run();
	}
	
	function insertDivider() {
		editor.chain().focus().setHorizontalRule().run();
	}
	
	function clearFormatting() {
		editor.chain().focus().clearNodes().unsetAllMarks().run();
	}
</script>

<div class="editor-wrapper">
	{#if editable}
		<div class="toolbar">
			<div class="toolbar-group">
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('heading', { level: 1 })}
					on:click={() => toggleHeading(1)}
					title="Heading 1"
				>
					H1
				</button>
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('heading', { level: 2 })}
					on:click={() => toggleHeading(2)}
					title="Heading 2"
				>
					H2
				</button>
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('heading', { level: 3 })}
					on:click={() => toggleHeading(3)}
					title="Heading 3"
				>
					H3
				</button>
			</div>
			
			<div class="toolbar-divider"></div>
			
			<div class="toolbar-group">
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('bold')}
					on:click={() => editor.chain().focus().toggleBold().run()}
					disabled={!editor?.can().chain().focus().toggleBold().run()}
					title="Bold"
				>
					<Bold size={16} />
				</button>
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('italic')}
					on:click={() => editor.chain().focus().toggleItalic().run()}
					disabled={!editor?.can().chain().focus().toggleItalic().run()}
					title="Italic"
				>
					<Italic size={16} />
				</button>
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('underline')}
					on:click={() => editor.chain().focus().toggleUnderline().run()}
					disabled={!editor?.can().chain().focus().toggleUnderline().run()}
					title="Underline"
				>
					<UnderlineIcon size={16} />
				</button>
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('strike')}
					on:click={() => editor.chain().focus().toggleStrike().run()}
					disabled={!editor?.can().chain().focus().toggleStrike().run()}
					title="Strikethrough"
				>
					<Strikethrough size={16} />
				</button>
			</div>
			
			<div class="toolbar-divider"></div>
			
			<div class="toolbar-group">
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('bulletList')}
					on:click={() => editor.chain().focus().toggleBulletList().run()}
					title="Bullet List"
				>
					<List size={16} />
				</button>
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('orderedList')}
					on:click={() => editor.chain().focus().toggleOrderedList().run()}
					title="Numbered List"
				>
					<ListOrdered size={16} />
				</button>
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('blockquote')}
					on:click={() => editor.chain().focus().toggleBlockquote().run()}
					title="Quote"
				>
					<Quote size={16} />
				</button>
				<button
					type="button"
					class="toolbar-button"
					class:active={editor?.isActive('code')}
					on:click={() => editor.chain().focus().toggleCode().run()}
					title="Code"
				>
					<Code size={16} />
				</button>
			</div>
			
			<div class="toolbar-divider"></div>
			
			<div class="toolbar-group">
				<button
					type="button"
					class="toolbar-button highlight-button"
					class:active={editor?.isActive('highlight')}
					title="Highlight"
				>
					<Highlighter size={16} />
					<div class="highlight-dropdown">
						<button
							type="button"
							class="highlight-option"
							style="background-color: #fef3c7"
							on:click={() => addHighlight('#fef3c7')}
							title="Yellow"
						></button>
						<button
							type="button"
							class="highlight-option"
							style="background-color: #d1fae5"
							on:click={() => addHighlight('#d1fae5')}
							title="Green"
						></button>
						<button
							type="button"
							class="highlight-option"
							style="background-color: #dbeafe"
							on:click={() => addHighlight('#dbeafe')}
							title="Blue"
						></button>
						<button
							type="button"
							class="highlight-option"
							style="background-color: #fce7f3"
							on:click={() => addHighlight('#fce7f3')}
							title="Pink"
						></button>
						<button
							type="button"
							class="highlight-option clear"
							on:click={() => editor.chain().focus().unsetHighlight().run()}
							title="Clear highlight"
						>
							×
						</button>
					</div>
				</button>
			</div>
			
			<div class="toolbar-divider"></div>
			
			<div class="toolbar-group">
				<button
					type="button"
					class="toolbar-button"
					on:click={() => editor.chain().focus().undo().run()}
					disabled={!editor?.can().chain().focus().undo().run()}
					title="Undo"
				>
					<Undo size={16} />
				</button>
				<button
					type="button"
					class="toolbar-button"
					on:click={() => editor.chain().focus().redo().run()}
					disabled={!editor?.can().chain().focus().redo().run()}
					title="Redo"
				>
					<Redo size={16} />
				</button>
			</div>
			
			<div class="toolbar-group ml-auto">
				<button
					type="button"
					class="toolbar-button"
					on:click={clearFormatting}
					title="Clear formatting"
				>
					<Type size={16} />
				</button>
			</div>
		</div>
	{/if}
	
	<div 
		class="editor-content" 
		style="min-height: {minHeight}px"
		bind:this={element}
	></div>
</div>

<style>
	.editor-wrapper {
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		background: white;
		overflow: hidden;
	}
	
	.toolbar {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem;
		border-bottom: 1px solid #e0e0e0;
		background: #f9fafb;
		flex-wrap: wrap;
	}
	
	.toolbar-group {
		display: flex;
		align-items: center;
		gap: 0.25rem;
	}
	
	.toolbar-divider {
		width: 1px;
		height: 24px;
		background: #e0e0e0;
	}
	
	.toolbar-button {
		padding: 0.5rem;
		background: white;
		border: 1px solid transparent;
		border-radius: 4px;
		color: #666;
		cursor: pointer;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 0.875rem;
		font-weight: 600;
		position: relative;
	}
	
	.toolbar-button:hover {
		background: #f3f4f6;
		border-color: #e5e7eb;
		color: #333;
	}
	
	.toolbar-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.toolbar-button:disabled:hover {
		background: white;
		border-color: transparent;
		color: #666;
	}
	
	.toolbar-button.active {
		background: #10b981;
		border-color: #10b981;
		color: white;
	}
	
	.highlight-button:hover .highlight-dropdown,
	.highlight-button:focus-within .highlight-dropdown {
		display: flex;
	}
	
	.highlight-dropdown {
		display: none;
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		margin-top: 0.5rem;
		padding: 0.5rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 6px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		gap: 0.25rem;
		z-index: 10;
	}
	
	.highlight-option {
		width: 24px;
		height: 24px;
		border: 1px solid #e0e0e0;
		border-radius: 4px;
		cursor: pointer;
		transition: transform 0.2s;
	}
	
	.highlight-option:hover {
		transform: scale(1.1);
	}
	
	.highlight-option.clear {
		background: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 1.25rem;
		color: #666;
	}
	
	.ml-auto {
		margin-left: auto;
	}
	
	.editor-content {
		padding: 1.5rem;
		overflow-y: auto;
	}
	
	/* TipTap Editor Styles */
	:global(.ProseMirror) {
		outline: none;
		min-height: inherit;
	}
	
	:global(.ProseMirror p) {
		margin: 0 0 1rem 0;
	}
	
	:global(.ProseMirror p:last-child) {
		margin-bottom: 0;
	}
	
	:global(.ProseMirror h1) {
		font-size: 2rem;
		font-weight: 700;
		margin: 0 0 1rem 0;
		line-height: 1.2;
	}
	
	:global(.ProseMirror h2) {
		font-size: 1.5rem;
		font-weight: 600;
		margin: 0 0 1rem 0;
		line-height: 1.3;
	}
	
	:global(.ProseMirror h3) {
		font-size: 1.25rem;
		font-weight: 600;
		margin: 0 0 1rem 0;
		line-height: 1.4;
	}
	
	:global(.ProseMirror ul),
	:global(.ProseMirror ol) {
		padding-left: 1.5rem;
		margin: 0 0 1rem 0;
	}
	
	:global(.ProseMirror li) {
		margin: 0.25rem 0;
	}
	
	:global(.ProseMirror blockquote) {
		padding-left: 1rem;
		border-left: 3px solid #e0e0e0;
		margin: 0 0 1rem 0;
		font-style: italic;
		color: #666;
	}
	
	:global(.ProseMirror code) {
		background-color: #f3f4f6;
		border-radius: 4px;
		color: #374151;
		font-family: 'Courier New', monospace;
		font-size: 0.875rem;
		padding: 0.125rem 0.25rem;
	}
	
	:global(.ProseMirror pre) {
		background: #1f2937;
		border-radius: 0.5rem;
		color: #f9fafb;
		font-family: 'Courier New', monospace;
		margin: 0 0 1rem 0;
		padding: 1rem;
		overflow-x: auto;
	}
	
	:global(.ProseMirror pre code) {
		background: none;
		color: inherit;
		font-size: 0.875rem;
		padding: 0;
	}
	
	:global(.ProseMirror hr) {
		border: none;
		border-top: 2px solid #e5e7eb;
		margin: 2rem 0;
	}
	
	:global(.ProseMirror mark) {
		background-color: inherit;
		padding: 0.125rem 0;
		border-radius: 2px;
	}
	
	:global(.ProseMirror.editor-empty::before) {
		color: #9ca3af;
		content: attr(data-placeholder);
		float: left;
		height: 0;
		pointer-events: none;
	}
	
	:global(.ProseMirror:focus) {
		outline: none;
	}
	
	@media (max-width: 640px) {
		.toolbar {
			padding: 0.5rem;
			gap: 0.25rem;
		}
		
		.toolbar-button {
			padding: 0.375rem;
		}
	}
</style>