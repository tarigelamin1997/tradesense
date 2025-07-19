<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { Upload, X, FileText, FileSpreadsheet, FileJson, AlertCircle } from 'lucide-svelte';
	
	const dispatch = createEventDispatcher();
	
	export let accept = '.csv,.xlsx,.xls,.json';
	export let maxSize = 10 * 1024 * 1024; // 10MB
	export let multiple = false;
	
	let dragActive = false;
	let files: File[] = [];
	let errors: string[] = [];
	
	const acceptedFormats = {
		'.csv': { icon: FileText, color: 'text-green-600' },
		'.xlsx': { icon: FileSpreadsheet, color: 'text-blue-600' },
		'.xls': { icon: FileSpreadsheet, color: 'text-blue-600' },
		'.json': { icon: FileJson, color: 'text-orange-600' }
	};
	
	function handleDragEnter(e: DragEvent) {
		e.preventDefault();
		e.stopPropagation();
		dragActive = true;
	}
	
	function handleDragLeave(e: DragEvent) {
		e.preventDefault();
		e.stopPropagation();
		dragActive = false;
	}
	
	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		e.stopPropagation();
	}
	
	function handleDrop(e: DragEvent) {
		e.preventDefault();
		e.stopPropagation();
		dragActive = false;
		
		const droppedFiles = Array.from(e.dataTransfer?.files || []);
		handleFiles(droppedFiles);
	}
	
	function handleFileInput(e: Event) {
		const input = e.target as HTMLInputElement;
		const selectedFiles = Array.from(input.files || []);
		handleFiles(selectedFiles);
	}
	
	function handleFiles(newFiles: File[]) {
		errors = [];
		const validFiles: File[] = [];
		
		for (const file of newFiles) {
			// Check file extension
			const ext = '.' + file.name.split('.').pop()?.toLowerCase();
			if (!accept.includes(ext)) {
				errors.push(`${file.name}: Invalid file type. Accepted formats: ${accept}`);
				continue;
			}
			
			// Check file size
			if (file.size > maxSize) {
				errors.push(`${file.name}: File too large. Maximum size: ${formatFileSize(maxSize)}`);
				continue;
			}
			
			validFiles.push(file);
		}
		
		if (multiple) {
			files = [...files, ...validFiles];
		} else {
			files = validFiles.slice(0, 1);
		}
		
		if (validFiles.length > 0) {
			dispatch('upload', { files: validFiles });
		}
	}
	
	function removeFile(index: number) {
		files = files.filter((_, i) => i !== index);
		dispatch('remove', { index });
	}
	
	function formatFileSize(bytes: number): string {
		if (bytes === 0) return '0 Bytes';
		const k = 1024;
		const sizes = ['Bytes', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
	}
	
	function getFileIcon(fileName: string) {
		const ext = '.' + fileName.split('.').pop()?.toLowerCase();
		return acceptedFormats[ext] || { icon: FileText, color: 'text-gray-600' };
	}
</script>

<div class="file-upload">
	<div
		class="drop-zone {dragActive ? 'active' : ''}"
		on:dragenter={handleDragEnter}
		on:dragleave={handleDragLeave}
		on:dragover={handleDragOver}
		on:drop={handleDrop}
		role="region"
		aria-label="File upload drop zone"
	>
		<input
			type="file"
			id="file-input"
			{accept}
			{multiple}
			on:change={handleFileInput}
			class="hidden"
		/>
		
		<label for="file-input" class="upload-label">
			<Upload size={48} class="upload-icon" />
			<h3>Drag & drop files here</h3>
			<p>or click to browse</p>
			<div class="formats">
				<span>Accepted formats: CSV, Excel, JSON</span>
				<span>Maximum size: {formatFileSize(maxSize)}</span>
			</div>
		</label>
	</div>
	
	{#if errors.length > 0}
		<div class="errors">
			{#each errors as error}
				<div class="error">
					<AlertCircle size={16} />
					<span>{error}</span>
				</div>
			{/each}
		</div>
	{/if}
	
	{#if files.length > 0}
		<div class="file-list">
			<h4>Selected Files</h4>
			{#each files as file, index}
				{@const fileInfo = getFileIcon(file.name)}
				<div class="file-item">
					<div class="file-info">
						<svelte:component this={fileInfo.icon} size={20} class={fileInfo.color} />
						<span class="file-name">{file.name}</span>
						<span class="file-size">{formatFileSize(file.size)}</span>
					</div>
					<button
						type="button"
						class="remove-btn"
						on:click={() => removeFile(index)}
						aria-label="Remove file"
					>
						<X size={16} />
					</button>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.file-upload {
		width: 100%;
	}
	
	.drop-zone {
		border: 2px dashed #e0e0e0;
		border-radius: 12px;
		padding: 3rem;
		text-align: center;
		transition: all 0.3s ease;
		background: #fafafa;
		cursor: pointer;
	}
	
	.drop-zone:hover {
		border-color: #10b981;
		background: #f0fdf4;
	}
	
	.drop-zone.active {
		border-color: #10b981;
		background: #f0fdf4;
		transform: scale(1.02);
	}
	
	.upload-label {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		cursor: pointer;
	}
	
	.upload-icon {
		color: #10b981;
		transition: transform 0.3s ease;
	}
	
	.drop-zone:hover .upload-icon {
		transform: translateY(-4px);
	}
	
	.upload-label h3 {
		font-size: 1.25rem;
		font-weight: 600;
		color: #333;
		margin: 0;
	}
	
	.upload-label p {
		color: #666;
		margin: 0;
	}
	
	.formats {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		margin-top: 1rem;
	}
	
	.formats span {
		font-size: 0.875rem;
		color: #999;
	}
	
	.hidden {
		display: none;
	}
	
	.errors {
		margin-top: 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.error {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		background: #fee;
		border: 1px solid #fcc;
		border-radius: 6px;
		color: #c00;
		font-size: 0.875rem;
	}
	
	.file-list {
		margin-top: 2rem;
		padding: 1.5rem;
		background: white;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
	}
	
	.file-list h4 {
		margin: 0 0 1rem 0;
		font-size: 1rem;
		font-weight: 600;
		color: #333;
	}
	
	.file-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem;
		background: #f9f9f9;
		border-radius: 6px;
		margin-bottom: 0.5rem;
	}
	
	.file-item:last-child {
		margin-bottom: 0;
	}
	
	.file-info {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		flex: 1;
	}
	
	.file-name {
		flex: 1;
		font-weight: 500;
		color: #333;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.file-size {
		font-size: 0.875rem;
		color: #666;
	}
	
	.remove-btn {
		padding: 0.25rem;
		background: none;
		border: none;
		color: #999;
		cursor: pointer;
		border-radius: 4px;
		transition: all 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	
	.remove-btn:hover {
		background: #fee;
		color: #c00;
	}
	
	:global(.upload-icon) {
		stroke-width: 1.5;
	}
	
	@media (max-width: 640px) {
		.drop-zone {
			padding: 2rem 1rem;
		}
		
		.upload-label h3 {
			font-size: 1.125rem;
		}
		
		.formats {
			font-size: 0.75rem;
		}
		
		.file-info {
			gap: 0.5rem;
		}
		
		.file-name {
			font-size: 0.875rem;
		}
	}
</style>