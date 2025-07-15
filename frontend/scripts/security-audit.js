#!/usr/bin/env node

/**
 * Security Audit Script
 * Runs npm audit and generates a report
 */

import { exec } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const AUDIT_REPORT_PATH = path.join(__dirname, '..', 'security-audit-report.json');
const AUDIT_SUMMARY_PATH = path.join(__dirname, '..', 'security-audit-summary.md');

function runAudit() {
  console.log('🔒 Running security audit...');
  
  exec('npm audit --json', (error, stdout, stderr) => {
    let auditData;
    
    try {
      auditData = JSON.parse(stdout);
    } catch (e) {
      console.error('Failed to parse audit results:', e);
      process.exit(1);
    }
    
    // Save full report
    fs.writeFileSync(AUDIT_REPORT_PATH, JSON.stringify(auditData, null, 2));
    console.log(`📄 Full report saved to: ${AUDIT_REPORT_PATH}`);
    
    // Generate summary
    const summary = generateSummary(auditData);
    fs.writeFileSync(AUDIT_SUMMARY_PATH, summary);
    console.log(`📊 Summary saved to: ${AUDIT_SUMMARY_PATH}`);
    
    // Exit with error if high or critical vulnerabilities found
    const metadata = auditData.metadata || {};
    const vulnerabilities = metadata.vulnerabilities || {};
    
    if (vulnerabilities.high > 0 || vulnerabilities.critical > 0) {
      console.error('❌ High or critical vulnerabilities found!');
      process.exit(1);
    } else {
      console.log('✅ No high or critical vulnerabilities found.');
      process.exit(0);
    }
  });
}

function generateSummary(auditData) {
  const metadata = auditData.metadata || {};
  const vulnerabilities = metadata.vulnerabilities || {};
  const date = new Date().toISOString().split('T')[0];
  
  let summary = `# Security Audit Summary\n\n`;
  summary += `**Date:** ${date}\n\n`;
  summary += `## Vulnerability Summary\n\n`;
  summary += `| Severity | Count |\n`;
  summary += `|----------|-------|\n`;
  summary += `| Critical | ${vulnerabilities.critical || 0} |\n`;
  summary += `| High | ${vulnerabilities.high || 0} |\n`;
  summary += `| Moderate | ${vulnerabilities.moderate || 0} |\n`;
  summary += `| Low | ${vulnerabilities.low || 0} |\n`;
  summary += `| **Total** | **${vulnerabilities.total || 0}** |\n\n`;
  
  // Add details about vulnerabilities
  const vulns = auditData.vulnerabilities || {};
  const vulnList = Object.entries(vulns);
  
  if (vulnList.length > 0) {
    summary += `## Vulnerability Details\n\n`;
    
    // Group by severity
    const bySeverity = {
      critical: [],
      high: [],
      moderate: [],
      low: []
    };
    
    vulnList.forEach(([name, details]) => {
      const severity = details.severity || 'unknown';
      if (bySeverity[severity]) {
        bySeverity[severity].push({ name, ...details });
      }
    });
    
    // Output by severity
    ['critical', 'high', 'moderate', 'low'].forEach(severity => {
      const items = bySeverity[severity];
      if (items.length > 0) {
        summary += `### ${severity.charAt(0).toUpperCase() + severity.slice(1)} Severity\n\n`;
        items.forEach(item => {
          summary += `- **${item.name}** (${item.range})\n`;
          summary += `  - ${item.title}\n`;
          if (item.fixAvailable) {
            summary += `  - Fix available: ${typeof item.fixAvailable === 'object' ? item.fixAvailable.name : 'Yes'}\n`;
          }
          summary += `\n`;
        });
      }
    });
  }
  
  summary += `## Recommendations\n\n`;
  
  if (vulnerabilities.critical > 0 || vulnerabilities.high > 0) {
    summary += `⚠️ **Immediate Action Required:**\n`;
    summary += `- Run \`npm audit fix\` to automatically fix available patches\n`;
    summary += `- Review and manually update packages that require breaking changes\n\n`;
  }
  
  if (vulnerabilities.moderate > 0) {
    summary += `📋 **Recommended Actions:**\n`;
    summary += `- Review moderate severity vulnerabilities\n`;
    summary += `- Plan updates in next maintenance window\n\n`;
  }
  
  summary += `## Next Steps\n\n`;
  summary += `1. Run \`npm audit fix\` to apply automatic fixes\n`;
  summary += `2. Review packages requiring manual updates\n`;
  summary += `3. Test application after updates\n`;
  summary += `4. Run audit again to verify fixes\n`;
  
  return summary;
}

// Run the audit
runAudit();