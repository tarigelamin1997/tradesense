import { api } from './client';

export interface FileUploadResponse {
	success: boolean;
	filename: string;
	rows: number;
	columns: string[];
	data_preview: any[];
	message: string;
	upload_id: string;
}

export interface ValidationResult {
	valid: boolean;
	errors: ValidationError[];
	warnings: ValidationWarning[];
	total_rows: number;
	valid_rows: number;
	invalid_rows: number;
}

export interface ValidationError {
	row: number;
	field: string;
	message: string;
	value?: any;
}

export interface ValidationWarning {
	row: number;
	field: string;
	message: string;
}

export interface ColumnMapping {
	[fileColumn: string]: string; // maps file column to system field
}

export interface ImportResult {
	success: boolean;
	imported: number;
	failed: number;
	errors: ImportError[];
	message: string;
}

export interface ImportError {
	row: number;
	message: string;
	data?: any;
}

export const uploadsApi = {
	// Upload a file
	async uploadFile(file: File): Promise<FileUploadResponse> {
		const formData = new FormData();
		formData.append('file', file);
		
		return api.post('/api/v1/uploads', formData, {
			headers: {
				'Content-Type': 'multipart/form-data'
			}
		});
	},

	// Validate uploaded data
	async validateData(uploadId: string, columnMapping?: ColumnMapping): Promise<ValidationResult> {
		return api.post(`/api/v1/uploads/${uploadId}/validate`, {
			column_mapping: columnMapping
		});
	},

	// Import validated data
	async importTrades(uploadId: string, columnMapping?: ColumnMapping): Promise<ImportResult> {
		return api.post(`/api/v1/uploads/${uploadId}/import`, {
			column_mapping: columnMapping
		});
	},

	// Get upload status
	async getUploadStatus(uploadId: string): Promise<any> {
		return api.get(`/api/v1/uploads/${uploadId}/status`);
	},

	// Get suggested column mappings
	async getSuggestedMappings(columns: string[]): Promise<ColumnMapping> {
		// Client-side mapping suggestions
		const mappings: ColumnMapping = {};
		const fieldMappings = {
			symbol: ['symbol', 'ticker', 'stock', 'instrument'],
			side: ['side', 'direction', 'type', 'position'],
			entry_price: ['entry_price', 'entry', 'buy_price', 'open_price', 'price_in'],
			exit_price: ['exit_price', 'exit', 'sell_price', 'close_price', 'price_out'],
			quantity: ['quantity', 'qty', 'shares', 'size', 'volume'],
			entry_date: ['entry_date', 'entry_time', 'open_date', 'buy_date', 'date_in'],
			exit_date: ['exit_date', 'exit_time', 'close_date', 'sell_date', 'date_out'],
			pnl: ['pnl', 'profit', 'profit_loss', 'gain_loss', 'p&l'],
			strategy: ['strategy', 'setup', 'system', 'method'],
			notes: ['notes', 'comments', 'remarks', 'description']
		};

		for (const column of columns) {
			const lowerColumn = column.toLowerCase().replace(/[^a-z0-9]/g, '_');
			
			for (const [field, variations] of Object.entries(fieldMappings)) {
				if (variations.some(v => lowerColumn.includes(v))) {
					mappings[column] = field;
					break;
				}
			}
		}

		return mappings;
	}
};