import React, { useRef } from 'react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { saveAs } from 'file-saver';
import { Download, FileImage, FileText, FileSpreadsheet } from 'lucide-react';

interface ChartExporterProps {
  chartRef: React.RefObject<HTMLDivElement>;
  chartTitle: string;
  data?: any[];
  className?: string;
}

export const ChartExporter: React.FC<ChartExporterProps> = ({ 
  chartRef, 
  chartTitle, 
  data,
  className = ''
}) => {
  const [isExporting, setIsExporting] = React.useState(false);
  const [showMenu, setShowMenu] = React.useState(false);
  
  // Export as PNG
  const exportAsPNG = async () => {
    if (!chartRef.current) return;
    
    setIsExporting(true);
    try {
      const canvas = await html2canvas(chartRef.current, {
        scale: 2,
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true
      });
      
      canvas.toBlob((blob) => {
        if (blob) {
          saveAs(blob, `${chartTitle.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}.png`);
        }
      }, 'image/png');
    } catch (error) {
      console.error('Error exporting PNG:', error);
    } finally {
      setIsExporting(false);
      setShowMenu(false);
    }
  };
  
  // Export as PDF
  const exportAsPDF = async () => {
    if (!chartRef.current) return;
    
    setIsExporting(true);
    try {
      const canvas = await html2canvas(chartRef.current, {
        scale: 2,
        backgroundColor: '#ffffff',
        logging: false
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'px',
        format: [canvas.width, canvas.height]
      });
      
      // Add metadata
      pdf.setProperties({
        title: chartTitle,
        subject: 'Trading Analytics Report',
        author: 'TradeSense',
        keywords: 'trading, analytics, report',
        creator: 'TradeSense Analytics'
      });
      
      // Add title and date
      pdf.setFontSize(20);
      pdf.text(chartTitle, 40, 40);
      pdf.setFontSize(12);
      pdf.text(`Generated: ${new Date().toLocaleString()}`, 40, 60);
      
      // Add chart image
      pdf.addImage(imgData, 'PNG', 0, 80, canvas.width, canvas.height);
      
      pdf.save(`${chartTitle.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}.pdf`);
    } catch (error) {
      console.error('Error exporting PDF:', error);
    } finally {
      setIsExporting(false);
      setShowMenu(false);
    }
  };
  
  // Export data as CSV
  const exportAsCSV = () => {
    if (!data || data.length === 0) {
      console.warn('No data available for CSV export');
      return;
    }
    
    try {
      // Get headers from first object
      const headers = Object.keys(data[0]);
      
      // Create CSV content
      let csvContent = headers.join(',') + '\n';
      
      data.forEach(row => {
        const values = headers.map(header => {
          const value = row[header];
          // Handle special characters and commas in values
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value ?? '';
        });
        csvContent += values.join(',') + '\n';
      });
      
      // Create blob and download
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      saveAs(blob, `${chartTitle.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}.csv`);
    } catch (error) {
      console.error('Error exporting CSV:', error);
    } finally {
      setShowMenu(false);
    }
  };
  
  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setShowMenu(!showMenu)}
        disabled={isExporting}
        className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
        title="Export chart"
      >
        {isExporting ? (
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600" />
        ) : (
          <Download className="h-4 w-4 text-gray-600" />
        )}
      </button>
      
      {showMenu && !isExporting && (
        <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          <button
            onClick={exportAsPNG}
            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <FileImage className="h-4 w-4 mr-2" />
            Export as PNG
          </button>
          
          <button
            onClick={exportAsPDF}
            className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <FileText className="h-4 w-4 mr-2" />
            Export as PDF
          </button>
          
          {data && (
            <button
              onClick={exportAsCSV}
              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Export Data (CSV)
            </button>
          )}
        </div>
      )}
    </div>
  );
};

// Hook for easy chart export
export const useChartExport = () => {
  const chartRef = useRef<HTMLDivElement>(null);
  
  const exportChart = async (format: 'png' | 'pdf', title: string = 'Chart') => {
    if (!chartRef.current) return;
    
    try {
      const canvas = await html2canvas(chartRef.current, {
        scale: 2,
        backgroundColor: '#ffffff',
        logging: false
      });
      
      if (format === 'png') {
        canvas.toBlob((blob) => {
          if (blob) {
            saveAs(blob, `${title.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}.png`);
          }
        }, 'image/png');
      } else if (format === 'pdf') {
        const imgData = canvas.toDataURL('image/png');
        const pdf = new jsPDF({
          orientation: 'landscape',
          unit: 'px',
          format: [canvas.width, canvas.height]
        });
        
        pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height);
        pdf.save(`${title.replace(/\s+/g, '-').toLowerCase()}-${Date.now()}.pdf`);
      }
    } catch (error) {
      console.error('Error exporting chart:', error);
    }
  };
  
  return { chartRef, exportChart };
};

export default ChartExporter;