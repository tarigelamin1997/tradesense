import type { Trade } from '$lib/stores/trades';

export interface ExportOptions {
	filename?: string;
	columns?: string[];
	format?: 'csv' | 'excel' | 'json';
	dateFormat?: string;
}

export class TradeExporter {
	/**
	 * Export trades to CSV format
	 */
	static toCSV(trades: Trade[], options: ExportOptions = {}): Blob {
		const {
			columns = [
				'symbol', 'side', 'entryPrice', 'exitPrice', 'quantity',
				'pnl', 'entryDate', 'exitDate', 'strategy', 'notes'
			]
		} = options;

		// Create header row
		const headers = columns.map(col => this.formatColumnHeader(col));
		const rows = [headers.join(',')];

		// Add data rows
		for (const trade of trades) {
			const row = columns.map(col => {
				const value = this.getTradeValue(trade, col);
				// Escape values that contain commas or quotes
				if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
					return `"${value.replace(/"/g, '""')}"`;
				}
				return value;
			});
			rows.push(row.join(','));
		}

		const csv = rows.join('\n');
		return new Blob([csv], { type: 'text/csv;charset=utf-8;' });
	}

	/**
	 * Export trades to Excel format (simplified - creates CSV that Excel can open)
	 */
	static toExcel(trades: Trade[], options: ExportOptions = {}): Blob {
		// For now, we'll create a CSV that Excel can open
		// In a production app, you'd use a library like SheetJS
		const csv = this.toCSV(trades, options);
		return new Blob([csv], { type: 'application/vnd.ms-excel' });
	}

	/**
	 * Export trades to JSON format
	 */
	static toJSON(trades: Trade[], options: ExportOptions = {}): Blob {
		const data = trades.map(trade => this.formatTradeForExport(trade));
		const json = JSON.stringify(data, null, 2);
		return new Blob([json], { type: 'application/json' });
	}

	/**
	 * Download the exported file
	 */
	static download(blob: Blob, filename: string) {
		const url = URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = filename;
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		URL.revokeObjectURL(url);
	}

	/**
	 * Export trades with the specified format
	 */
	static export(trades: Trade[], format: 'csv' | 'excel' | 'json' = 'csv', options: ExportOptions = {}) {
		const date = new Date().toISOString().split('T')[0];
		const defaultFilename = `trades_${date}.${format === 'excel' ? 'xlsx' : format}`;
		const filename = options.filename || defaultFilename;

		let blob: Blob;
		switch (format) {
			case 'csv':
				blob = this.toCSV(trades, options);
				break;
			case 'excel':
				blob = this.toExcel(trades, options);
				break;
			case 'json':
				blob = this.toJSON(trades, options);
				break;
			default:
				throw new Error(`Unsupported format: ${format}`);
		}

		this.download(blob, filename);
	}

	/**
	 * Format column header for display
	 */
	private static formatColumnHeader(column: string): string {
		const headerMap: Record<string, string> = {
			symbol: 'Symbol',
			side: 'Side',
			entryPrice: 'Entry Price',
			exitPrice: 'Exit Price',
			quantity: 'Quantity',
			pnl: 'P&L',
			entryDate: 'Entry Date',
			exitDate: 'Exit Date',
			strategy: 'Strategy',
			notes: 'Notes'
		};
		return headerMap[column] || column;
	}

	/**
	 * Get value from trade object
	 */
	private static getTradeValue(trade: Trade, column: string): any {
		switch (column) {
			case 'symbol':
				return trade.symbol;
			case 'side':
				return trade.side;
			case 'entryPrice':
				return trade.entryPrice;
			case 'exitPrice':
				return trade.exitPrice;
			case 'quantity':
				return trade.quantity;
			case 'pnl':
				return trade.pnl.toFixed(2);
			case 'entryDate':
				return this.formatDate(trade.entryDate);
			case 'exitDate':
				return this.formatDate(trade.exitDate);
			case 'strategy':
				return trade.strategy || '';
			case 'notes':
				return trade.notes || '';
			default:
				return '';
		}
	}

	/**
	 * Format trade object for export
	 */
	private static formatTradeForExport(trade: Trade): Record<string, any> {
		return {
			symbol: trade.symbol,
			side: trade.side,
			entry_price: trade.entryPrice,
			exit_price: trade.exitPrice,
			quantity: trade.quantity,
			pnl: parseFloat(trade.pnl.toFixed(2)),
			pnl_percentage: trade.pnl / (trade.entryPrice * trade.quantity) * 100,
			entry_date: trade.entryDate,
			exit_date: trade.exitDate,
			duration_hours: this.calculateDuration(trade.entryDate, trade.exitDate),
			strategy: trade.strategy || null,
			notes: trade.notes || null
		};
	}

	/**
	 * Format date for display
	 */
	private static formatDate(dateString: string): string {
		const date = new Date(dateString);
		return date.toLocaleString('en-US', {
			year: 'numeric',
			month: '2-digit',
			day: '2-digit',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	/**
	 * Calculate trade duration in hours
	 */
	private static calculateDuration(entryDate: string, exitDate: string): number {
		const entry = new Date(entryDate);
		const exit = new Date(exitDate);
		const durationMs = exit.getTime() - entry.getTime();
		return Math.round(durationMs / (1000 * 60 * 60) * 100) / 100;
	}
}