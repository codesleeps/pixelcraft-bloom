/**
 * Export Utilities for Dashboard Components
 * Provides functionality to export dashboard data in various formats (PDF, Excel, CSV)
 */

// PDF Export using jsPDF
function exportToPDF(elementId, filename) {
  const element = document.getElementById(elementId);
  if (!element) {
    console.error(`Element with ID ${elementId} not found`);
    return;
  }

  // Load jsPDF dynamically if not already loaded
  if (typeof jspdf === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
    script.onload = () => {
      const html2canvasScript = document.createElement('script');
      html2canvasScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
      html2canvasScript.onload = () => {
        generatePDF(element, filename);
      };
      document.head.appendChild(html2canvasScript);
    };
    document.head.appendChild(script);
  } else {
    generatePDF(element, filename);
  }
}

function generatePDF(element, filename) {
  const { jsPDF } = window.jspdf;
  
  html2canvas(element).then(canvas => {
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('l', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    const imgWidth = canvas.width;
    const imgHeight = canvas.height;
    const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
    const imgX = (pdfWidth - imgWidth * ratio) / 2;
    const imgY = 30;
    
    pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);
    pdf.save(`${filename || 'dashboard-export'}.pdf`);
  });
}

// Excel Export using SheetJS
function exportToExcel(data, filename) {
  // Load SheetJS dynamically if not already loaded
  if (typeof XLSX === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
    script.onload = () => {
      generateExcel(data, filename);
    };
    document.head.appendChild(script);
  } else {
    generateExcel(data, filename);
  }
}

function generateExcel(data, filename) {
  const ws = XLSX.utils.json_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Dashboard Data');
  XLSX.writeFile(wb, `${filename || 'dashboard-export'}.xlsx`);
}

// CSV Export
function exportToCSV(data, filename) {
  if (!data || !data.length) {
    console.error('No data provided for CSV export');
    return;
  }

  // Get headers from the first object
  const headers = Object.keys(data[0]);
  
  // Create CSV content
  let csvContent = headers.join(',') + '\n';
  
  // Add data rows
  data.forEach(item => {
    const row = headers.map(header => {
      // Handle values that need quotes (contain commas, quotes, or newlines)
      let cell = item[header] === null || item[header] === undefined ? '' : item[header].toString();
      if (cell.includes(',') || cell.includes('"') || cell.includes('\n')) {
        cell = '"' + cell.replace(/"/g, '""') + '"';
      }
      return cell;
    });
    csvContent += row.join(',') + '\n';
  });
  
  // Create and download the file
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', `${filename || 'dashboard-export'}.csv`);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// Extract table data for export
function extractTableData(tableId) {
  const table = document.getElementById(tableId);
  if (!table) {
    console.error(`Table with ID ${tableId} not found`);
    return [];
  }
  
  const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
  const rows = Array.from(table.querySelectorAll('tbody tr'));
  
  return rows.map(row => {
    const cells = Array.from(row.querySelectorAll('td'));
    const rowData = {};
    
    headers.forEach((header, index) => {
      rowData[header] = cells[index] ? cells[index].textContent.trim() : '';
    });
    
    return rowData;
  });
}

// Extract chart data for export
function extractChartData(chartInstance) {
  if (!chartInstance || !chartInstance.data) {
    console.error('Invalid chart instance provided');
    return [];
  }
  
  const datasets = chartInstance.data.datasets;
  const labels = chartInstance.data.labels;
  const result = [];
  
  labels.forEach((label, i) => {
    const item = { Label: label };
    
    datasets.forEach(dataset => {
      item[dataset.label] = dataset.data[i];
    });
    
    result.push(item);
  });
  
  return result;
}