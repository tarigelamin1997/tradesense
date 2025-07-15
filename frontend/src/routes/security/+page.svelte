<script lang="ts">
	import { ChevronLeft, Shield, Lock, Key, Server, Eye, AlertTriangle, CheckCircle2, FileCheck } from 'lucide-svelte';
</script>

<svelte:head>
	<title>Security - TradeSense</title>
	<meta name="description" content="Learn about TradeSense's security measures, including encryption, compliance, and best practices to protect your trading data.">
</svelte:head>

<div class="security-page">
	<div class="security-header">
		<a href="/" class="back-link">
			<ChevronLeft size={20} />
			Back to Home
		</a>
		<div class="header-content">
			<h1>Security at TradeSense</h1>
			<p class="subtitle">Your trading data deserves bank-level protection</p>
		</div>
	</div>

	<div class="security-overview">
		<div class="overview-card">
			<Shield size={32} />
			<h2>Enterprise-Grade Security</h2>
			<p>We use the same security standards as major financial institutions to protect your data.</p>
		</div>
	</div>

	<div class="security-content">
		<section>
			<h2>🔒 Data Encryption</h2>
			<div class="security-feature">
				<h3>In Transit</h3>
				<p>All data transmitted between your device and our servers is encrypted using TLS 1.3, the latest and most secure protocol.</p>
				<ul>
					<li>256-bit SSL encryption</li>
					<li>Perfect forward secrecy</li>
					<li>Certificate pinning for mobile apps</li>
				</ul>
			</div>
			
			<div class="security-feature">
				<h3>At Rest</h3>
				<p>Your data is encrypted when stored on our servers using industry-standard AES-256 encryption.</p>
				<ul>
					<li>Encrypted database storage</li>
					<li>Encrypted file storage</li>
					<li>Encrypted backups</li>
				</ul>
			</div>
		</section>

		<section>
			<h2>🛡️ Infrastructure Security</h2>
			<div class="infrastructure-grid">
				<div class="infra-card">
					<Server size={24} />
					<h3>Secure Hosting</h3>
					<p>Hosted on AWS with SOC 2 Type II compliance</p>
				</div>
				<div class="infra-card">
					<AlertTriangle size={24} />
					<h3>DDoS Protection</h3>
					<p>CloudFlare protection against attacks</p>
				</div>
				<div class="infra-card">
					<Eye size={24} />
					<h3>24/7 Monitoring</h3>
					<p>Continuous security monitoring and alerts</p>
				</div>
				<div class="infra-card">
					<Key size={24} />
					<h3>Access Control</h3>
					<p>Role-based access with principle of least privilege</p>
				</div>
			</div>
		</section>

		<section>
			<h2>🔐 Account Security</h2>
			<div class="account-features">
				<div class="feature-item">
					<CheckCircle2 size={20} color="#10b981" />
					<div>
						<h3>Two-Factor Authentication (2FA)</h3>
						<p>Optional TOTP-based 2FA for enhanced account protection</p>
					</div>
				</div>
				<div class="feature-item">
					<CheckCircle2 size={20} color="#10b981" />
					<div>
						<h3>Strong Password Requirements</h3>
						<p>Enforced password complexity and regular rotation reminders</p>
					</div>
				</div>
				<div class="feature-item">
					<CheckCircle2 size={20} color="#10b981" />
					<div>
						<h3>Session Management</h3>
						<p>Automatic timeout and ability to revoke active sessions</p>
					</div>
				</div>
				<div class="feature-item">
					<CheckCircle2 size={20} color="#10b981" />
					<div>
						<h3>Login Notifications</h3>
						<p>Email alerts for new device logins and suspicious activity</p>
					</div>
				</div>
			</div>
		</section>

		<section>
			<h2>📋 Compliance & Certifications</h2>
			<div class="compliance-grid">
				<div class="compliance-card">
					<h3>SOC 2 Type II</h3>
					<p>Annual audits for security, availability, and confidentiality</p>
				</div>
				<div class="compliance-card">
					<h3>GDPR Compliant</h3>
					<p>Full compliance with EU data protection regulations</p>
				</div>
				<div class="compliance-card">
					<h3>CCPA Compliant</h3>
					<p>California Consumer Privacy Act compliance</p>
				</div>
				<div class="compliance-card">
					<h3>PCI DSS</h3>
					<p>Payment Card Industry Data Security Standard</p>
				</div>
			</div>
		</section>

		<section>
			<h2>🛠️ Security Practices</h2>
			<div class="practices-list">
				<h3>Development Security</h3>
				<ul>
					<li>Regular security code reviews</li>
					<li>Automated vulnerability scanning</li>
					<li>Dependency security updates</li>
					<li>Secure development lifecycle (SDLC)</li>
				</ul>

				<h3>Operational Security</h3>
				<ul>
					<li>Regular penetration testing</li>
					<li>Security incident response plan</li>
					<li>Employee security training</li>
					<li>Vendor security assessments</li>
				</ul>

				<h3>Data Protection</h3>
				<ul>
					<li>Data minimization principles</li>
					<li>Regular data backups</li>
					<li>Secure data deletion</li>
					<li>Data isolation between accounts</li>
				</ul>
			</div>
		</section>

		<section>
			<h2>🚨 Reporting Security Issues</h2>
			<div class="security-contact">
				<p>
					We take security seriously and appreciate responsible disclosure of vulnerabilities. 
					If you discover a security issue, please report it to our security team.
				</p>
				<div class="contact-box">
					<h3>Security Contact</h3>
					<p>Email: <a href="mailto:security@tradesense.io">security@tradesense.io</a></p>
					<p>PGP Key: Available on request</p>
				</div>
				<div class="bug-bounty">
					<h3>Bug Bounty Program</h3>
					<p>We offer rewards for responsibly disclosed vulnerabilities. Please email us for details.</p>
				</div>
			</div>
		</section>

		<section>
			<h2>💡 Security Best Practices for Users</h2>
			<div class="best-practices">
				<div class="practice-card">
					<h3>Use Strong Passwords</h3>
					<p>Create unique, complex passwords and consider using a password manager</p>
				</div>
				<div class="practice-card">
					<h3>Enable 2FA</h3>
					<p>Add an extra layer of security with two-factor authentication</p>
				</div>
				<div class="practice-card">
					<h3>Keep Software Updated</h3>
					<p>Use the latest version of your browser and operating system</p>
				</div>
				<div class="practice-card">
					<h3>Verify URLs</h3>
					<p>Always check you're on tradesense.io before entering credentials</p>
				</div>
			</div>
		</section>

		<section class="security-footer">
			<h2>Questions About Security?</h2>
			<p>
				Our team is here to help. Contact us at <a href="mailto:support@tradesense.io">support@tradesense.io</a> 
				for any security-related questions or concerns.
			</p>
		</section>
	</div>
</div>

<style>
	.security-page {
		max-width: 900px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: white;
	}

	.security-header {
		margin-bottom: 3rem;
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: #666;
		text-decoration: none;
		font-size: 0.875rem;
		margin-bottom: 1rem;
		transition: color 0.2s;
	}

	.back-link:hover {
		color: #10b981;
	}

	.header-content h1 {
		font-size: 2.5rem;
		margin-bottom: 0.5rem;
		color: #1a1a1a;
	}

	.subtitle {
		color: #666;
		font-size: 1.25rem;
	}

	.security-overview {
		margin-bottom: 3rem;
	}

	.overview-card {
		background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
		padding: 2rem;
		border-radius: 12px;
		text-align: center;
		border: 1px solid #10b981;
	}

	.overview-card h2 {
		font-size: 1.5rem;
		margin: 1rem 0 0.5rem;
		color: #059669;
	}

	.security-content {
		line-height: 1.8;
		color: #333;
	}

	section {
		margin-bottom: 3rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid #e0e0e0;
	}

	section:last-child {
		border-bottom: none;
	}

	h2 {
		font-size: 1.75rem;
		margin-bottom: 1.5rem;
		color: #1a1a1a;
	}

	h3 {
		font-size: 1.25rem;
		margin-bottom: 0.75rem;
		color: #333;
	}

	p {
		margin-bottom: 1rem;
	}

	ul {
		margin: 1rem 0;
		padding-left: 2rem;
	}

	li {
		margin-bottom: 0.5rem;
	}

	.security-feature {
		background: #f9fafb;
		padding: 1.5rem;
		border-radius: 8px;
		margin-bottom: 1.5rem;
	}

	.infrastructure-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
	}

	.infra-card {
		background: white;
		padding: 1.5rem;
		border-radius: 8px;
		border: 1px solid #e0e0e0;
		text-align: center;
		transition: all 0.3s;
	}

	.infra-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.infra-card h3 {
		margin: 0.75rem 0 0.5rem;
		font-size: 1.125rem;
	}

	.infra-card p {
		font-size: 0.875rem;
		color: #666;
		margin: 0;
	}

	.account-features {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.feature-item {
		display: flex;
		gap: 1rem;
		align-items: flex-start;
	}

	.feature-item h3 {
		margin: 0 0 0.25rem 0;
		font-size: 1.125rem;
	}

	.feature-item p {
		margin: 0;
		color: #666;
		font-size: 0.875rem;
	}

	.compliance-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
	}

	.compliance-card {
		background: #f0fdf4;
		padding: 1.5rem;
		border-radius: 8px;
		border: 1px solid #10b981;
	}

	.compliance-card h3 {
		color: #059669;
		margin-bottom: 0.5rem;
	}

	.compliance-card p {
		font-size: 0.875rem;
		color: #666;
		margin: 0;
	}

	.practices-list {
		background: #f9fafb;
		padding: 2rem;
		border-radius: 8px;
	}

	.practices-list h3 {
		margin-top: 1.5rem;
	}

	.practices-list h3:first-child {
		margin-top: 0;
	}

	.security-contact {
		background: #fef3c7;
		padding: 2rem;
		border-radius: 8px;
		border: 1px solid #f59e0b;
	}

	.contact-box, .bug-bounty {
		background: white;
		padding: 1.5rem;
		border-radius: 6px;
		margin-top: 1rem;
	}

	.best-practices {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: 1.5rem;
	}

	.practice-card {
		background: #e0f2fe;
		padding: 1.5rem;
		border-radius: 8px;
		border: 1px solid #0284c7;
	}

	.practice-card h3 {
		color: #0369a1;
		margin-bottom: 0.5rem;
	}

	.practice-card p {
		font-size: 0.875rem;
		color: #666;
		margin: 0;
	}

	.security-footer {
		text-align: center;
		padding: 2rem;
		background: #f9fafb;
		border-radius: 8px;
		margin-top: 3rem;
	}

	.security-footer h2 {
		margin-bottom: 1rem;
	}

	.security-footer p {
		margin: 0;
	}

	a {
		color: #10b981;
		text-decoration: none;
	}

	a:hover {
		text-decoration: underline;
	}

	@media (max-width: 768px) {
		.security-page {
			padding: 1rem;
		}

		.header-content h1 {
			font-size: 2rem;
		}

		.infrastructure-grid,
		.compliance-grid,
		.best-practices {
			grid-template-columns: 1fr;
		}

		.practices-list {
			padding: 1.5rem;
		}
	}
</style>