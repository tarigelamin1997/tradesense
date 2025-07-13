// Icon size diagnostics utility
export const runIconDiagnostics = () => {
  console.log('🔍 Running Icon Size Diagnostics...');
  
  // Check all SVG elements
  const svgs = document.querySelectorAll('svg');
  console.log(`Found ${svgs.length} SVG elements`);
  
  svgs.forEach((svg, index) => {
    const rect = svg.getBoundingClientRect();
    const computed = window.getComputedStyle(svg);
    
    // Flag if SVG is larger than expected
    if (rect.width > 48 || rect.height > 48) {
      console.warn(`⚠️ Large SVG #${index}:`, {
        dimensions: `${rect.width}x${rect.height}px`,
        className: svg.className.baseVal || svg.className,
        computedWidth: computed.width,
        computedHeight: computed.height,
        viewBox: svg.getAttribute('viewBox'),
        parent: svg.parentElement?.className,
        svg
      });
    }
  });
  
  // Check for global CSS rules affecting SVGs
  const sheets = Array.from(document.styleSheets);
  const svgRules: any[] = [];
  
  sheets.forEach(sheet => {
    try {
      const rules = Array.from(sheet.cssRules || []);
      rules.forEach(rule => {
        if (rule instanceof CSSStyleRule && rule.selectorText?.includes('svg')) {
          svgRules.push({
            selector: rule.selectorText,
            styles: rule.style.cssText
          });
        }
      });
    } catch (e) {
      // Cross-origin stylesheets will throw
    }
  });
  
  if (svgRules.length > 0) {
    console.log('📋 SVG-related CSS rules:', svgRules);
  }
  
  // Check lucide-react default size
  const lucideIcons = document.querySelectorAll('[data-lucide]');
  if (lucideIcons.length > 0) {
    console.log(`Found ${lucideIcons.length} Lucide icons`);
  }
  
  // Check for any elements with unexpected sizes
  const allElements = document.querySelectorAll('*');
  const largeElements: any[] = [];
  
  allElements.forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.width > 200 && rect.height > 200 && el.tagName !== 'BODY' && el.tagName !== 'HTML' && el.tagName !== 'DIV') {
      largeElements.push({
        tag: el.tagName,
        className: el.className,
        dimensions: `${rect.width}x${rect.height}px`,
        element: el
      });
    }
  });
  
  if (largeElements.length > 0) {
    console.warn('🔍 Unexpectedly large elements:', largeElements);
  }
  
  console.log('✅ Diagnostics complete. Check console warnings for issues.');
};