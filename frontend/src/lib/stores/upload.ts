import { writable } from 'svelte/store';
import type { FileUploadResponse, ValidationResult, ColumnMapping } from '$lib/api/uploads';

export interface UploadState {
	stage: 'idle' | 'uploading' | 'validating' | 'mapping' | 'importing' | 'complete' | 'error';
	progress: number;
	message: string;
	file: File | null;
	uploadResponse: FileUploadResponse | null;
	validationResult: ValidationResult | null;
	columnMapping: ColumnMapping;
	importResult: any | null;
	error: string | null;
}

function createUploadStore() {
	const { subscribe, set, update } = writable<UploadState>({
		stage: 'idle',
		progress: 0,
		message: '',
		file: null,
		uploadResponse: null,
		validationResult: null,
		columnMapping: {},
		importResult: null,
		error: null
	});

	return {
		subscribe,
		reset: () => set({
			stage: 'idle',
			progress: 0,
			message: '',
			file: null,
			uploadResponse: null,
			validationResult: null,
			columnMapping: {},
			importResult: null,
			error: null
		}),
		setStage: (stage: UploadState['stage']) => update(s => ({ ...s, stage })),
		setProgress: (progress: number) => update(s => ({ ...s, progress })),
		setMessage: (message: string) => update(s => ({ ...s, message })),
		setFile: (file: File) => update(s => ({ ...s, file })),
		setUploadResponse: (response: FileUploadResponse) => update(s => ({ 
			...s, 
			uploadResponse: response 
		})),
		setValidationResult: (result: ValidationResult) => update(s => ({ 
			...s, 
			validationResult: result 
		})),
		setColumnMapping: (mapping: ColumnMapping) => update(s => ({ 
			...s, 
			columnMapping: mapping 
		})),
		setImportResult: (result: any) => update(s => ({ 
			...s, 
			importResult: result 
		})),
		setError: (error: string) => update(s => ({ 
			...s, 
			error,
			stage: 'error' 
		}))
	};
}

export const uploadStore = createUploadStore();