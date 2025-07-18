<script lang="ts">
	import { ChevronLeft, Shield, Lock, Eye, Database, Mail, Globe } from 'lucide-svelte';
	
	const lastUpdated = new Date().toLocaleDateString('en-US', { 
		year: 'numeric', 
		month: 'long', 
		day: 'numeric' 
	});
</script>

<svelte:head>
	<title>Privacy Policy - TradeSense</title>
	<meta name="description" content="TradeSense Privacy Policy - Learn how we collect, use, and protect your personal information and trading data.">
</svelte:head>

<div class="legal-page">
	<div class="legal-header">
		<a href="/" class="back-link">
			<ChevronLeft size={20} />
			Back to Home
		</a>
		<div class="header-content">
			<h1>Privacy Policy</h1>
			<p class="last-updated">Last updated: {lastUpdated}</p>
		</div>
	</div>

	<div class="privacy-highlights">
		<h2>Your Privacy at a Glance</h2>
		<div class="highlights-grid">
			<div class="highlight-card">
				<Shield size={24} />
				<h3>Data Security</h3>
				<p>Bank-level encryption for all your data</p>
			</div>
			<div class="highlight-card">
				<Lock size={24} />
				<h3>Your Control</h3>
				<p>Export or delete your data anytime</p>
			</div>
			<div class="highlight-card">
				<Eye size={24} />
				<h3>No Selling</h3>
				<p>We never sell your personal information</p>
			</div>
		</div>
	</div>

	<div class="legal-content">
		<section>
			<h2>1. Introduction</h2>
			<p>
				TradeSense ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our trading journal and analytics platform.
			</p>
			<p>
				By using TradeSense, you agree to the collection and use of information in accordance with this policy.
			</p>
		</section>

		<section>
			<h2>2. Information We Collect</h2>
			
			<h3>2.1 Personal Information</h3>
			<p>Information you provide directly to us:</p>
			<ul>
				<li><strong>Account Information:</strong> Name, email address, username, password</li>
				<li><strong>Profile Information:</strong> Trading experience, preferences, timezone</li>
				<li><strong>Payment Information:</strong> Processed securely through Stripe (we don't store card details)</li>
				<li><strong>Communication:</strong> Support tickets, emails, feedback</li>
			</ul>

			<h3>2.2 Trading Data</h3>
			<ul>
				<li>Trade history and transaction details</li>
				<li>Performance metrics and analytics</li>
				<li>Journal entries and notes</li>
				<li>Uploaded CSV files and imported data</li>
			</ul>

			<h3>2.3 Automatically Collected Information</h3>
			<ul>
				<li><strong>Usage Data:</strong> Features used, pages visited, time spent</li>
				<li><strong>Device Information:</strong> Browser type, operating system, IP address</li>
				<li><strong>Cookies:</strong> Session management and preferences</li>
			</ul>
		</section>

		<section>
			<h2>3. How We Use Your Information</h2>
			<p>We use your information to:</p>
			<ul>
				<li>Provide and maintain the Service</li>
				<li>Process your trades and generate analytics</li>
				<li>Send important notifications about your account</li>
				<li>Respond to support requests</li>
				<li>Improve our Service and develop new features</li>
				<li>Detect and prevent fraud or abuse</li>
				<li>Comply with legal obligations</li>
			</ul>

			<div class="info-box">
				<p><strong>We do NOT use your trading data for:</strong></p>
				<ul>
					<li>Making our own trades or investments</li>
					<li>Sharing with third parties for their trading</li>
					<li>Selling to data brokers or advertisers</li>
				</ul>
			</div>
		</section>

		<section>
			<h2>4. Data Storage and Security</h2>
			
			<h3>4.1 Security Measures</h3>
			<ul>
				<li><strong>Encryption:</strong> All data is encrypted in transit (TLS) and at rest (AES-256)</li>
				<li><strong>Access Control:</strong> Role-based access with multi-factor authentication</li>
				<li><strong>Regular Audits:</strong> Security assessments and penetration testing</li>
				<li><strong>Secure Infrastructure:</strong> Hosted on SOC 2 compliant servers</li>
			</ul>

			<h3>4.2 Data Location</h3>
			<p>
				Your data is stored on secure servers in the United States. We use industry-standard safeguards to protect your information.
			</p>
		</section>

		<section>
			<h2>5. Information Sharing</h2>
			
			<h3>5.1 We Share Information Only:</h3>
			<ul>
				<li><strong>With Your Consent:</strong> When you explicitly agree</li>
				<li><strong>For Legal Reasons:</strong> To comply with laws or valid legal requests</li>
				<li><strong>With Service Providers:</strong> Trusted partners who help operate our Service (under strict confidentiality)</li>
				<li><strong>Business Transfers:</strong> In case of merger or acquisition (with notice)</li>
			</ul>

			<h3>5.2 Third-Party Services</h3>
			<p>We work with:</p>
			<ul>
				<li><strong>Stripe:</strong> Payment processing</li>
				<li><strong>AWS:</strong> Cloud infrastructure</li>
				<li><strong>SendGrid:</strong> Email notifications</li>
			</ul>
			<p>These providers have their own privacy policies and are prohibited from using your data for other purposes.</p>
		</section>

		<section>
			<h2>6. Your Rights and Choices</h2>
			
			<h3>6.1 You Can Always:</h3>
			<ul>
				<li><strong>Access Your Data:</strong> View all information we have about you</li>
				<li><strong>Export Your Data:</strong> Download your trades and analytics in standard formats</li>
				<li><strong>Update Information:</strong> Correct any inaccurate data</li>
				<li><strong>Delete Your Account:</strong> Remove all your data from our systems</li>
				<li><strong>Opt-Out:</strong> Unsubscribe from marketing communications</li>
			</ul>

			<h3>6.2 Data Portability</h3>
			<p>
				You can export your data at any time in CSV or JSON format through your account settings.
			</p>
		</section>

		<section>
			<h2>7. Cookies and Tracking</h2>
			<p>We use cookies for:</p>
			<ul>
				<li><strong>Essential Functions:</strong> Login sessions, security</li>
				<li><strong>Preferences:</strong> Language, timezone, display settings</li>
				<li><strong>Analytics:</strong> Understanding usage patterns (anonymized)</li>
			</ul>
			<p>
				You can control cookies through your browser settings, but some features may not work properly without them.
			</p>
		</section>

		<section>
			<h2>8. Children's Privacy</h2>
			<p>
				TradeSense is not intended for users under 18 years of age. We do not knowingly collect information from children. If you believe we have collected information from a minor, please contact us immediately.
			</p>
		</section>

		<section>
			<h2>9. International Users</h2>
			<p>
				If you access TradeSense from outside the United States, please be aware that your information may be transferred to and processed in the United States. We comply with applicable data protection laws including GDPR for EU users.
			</p>

			<h3>9.1 GDPR Rights (EU Users)</h3>
			<p>EU users have additional rights including:</p>
			<ul>
				<li>Right to erasure ("right to be forgotten")</li>
				<li>Right to restrict processing</li>
				<li>Right to data portability</li>
				<li>Right to object to processing</li>
			</ul>
		</section>

		<section>
			<h2>10. Data Retention</h2>
			<p>
				We retain your information for as long as your account is active or as needed to provide services. After account deletion:
			</p>
			<ul>
				<li>Personal data is deleted within 30 days</li>
				<li>Backups are purged within 90 days</li>
				<li>Some data may be retained longer if required by law</li>
			</ul>
		</section>

		<section>
			<h2>11. Changes to This Policy</h2>
			<p>
				We may update this Privacy Policy from time to time. We will notify you of any material changes via email or through the Service. Your continued use after changes means you accept the updated policy.
			</p>
		</section>

		<section>
			<h2>12. Contact Us</h2>
			<p>
				If you have questions about this Privacy Policy or your data:
			</p>
			<div class="contact-info">
				<div class="contact-item">
					<Mail size={20} />
					<span>privacy@tradesense.io</span>
				</div>
				<div class="contact-item">
					<Globe size={20} />
					<span>TradeSense Inc., 123 Market Street, Suite 100, San Francisco, CA 94105</span>
				</div>
			</div>

			<p>
				<strong>Data Protection Officer:</strong> dpo@tradesense.io
			</p>
		</section>
	</div>
</div>

<style>
	.legal-page {
		max-width: 800px;
		margin: 0 auto;
		padding: 2rem;
		min-height: 100vh;
		background: white;
	}

	.legal-header {
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

	.last-updated {
		color: #666;
		font-size: 0.875rem;
	}

	.privacy-highlights {
		background: #f0fdf4;
		padding: 2rem;
		border-radius: 12px;
		margin-bottom: 3rem;
	}

	.privacy-highlights h2 {
		font-size: 1.5rem;
		margin-bottom: 1.5rem;
		text-align: center;
		color: #059669;
	}

	.highlights-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
	}

	.highlight-card {
		text-align: center;
		padding: 1.5rem;
		background: white;
		border-radius: 8px;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	}

	.highlight-card h3 {
		font-size: 1.125rem;
		margin: 0.75rem 0 0.5rem;
		color: #1a1a1a;
	}

	.highlight-card p {
		font-size: 0.875rem;
		color: #666;
		margin: 0;
	}

	.legal-content {
		line-height: 1.8;
		color: #333;
	}

	section {
		margin-bottom: 3rem;
	}

	h2 {
		font-size: 1.75rem;
		margin-bottom: 1rem;
		color: #1a1a1a;
	}

	h3 {
		font-size: 1.25rem;
		margin-top: 1.5rem;
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

	strong {
		font-weight: 600;
		color: #1a1a1a;
	}

	a {
		color: #10b981;
		text-decoration: none;
	}

	a:hover {
		text-decoration: underline;
	}

	.info-box {
		background: #e0f2fe;
		border: 1px solid #0284c7;
		padding: 1rem;
		border-radius: 6px;
		margin: 1.5rem 0;
	}

	.info-box p {
		margin-bottom: 0.5rem;
	}

	.contact-info {
		margin: 1rem 0;
	}

	.contact-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
		color: #666;
	}

	@media (max-width: 768px) {
		.legal-page {
			padding: 1rem;
		}

		.header-content h1 {
			font-size: 2rem;
		}

		h2 {
			font-size: 1.5rem;
		}

		.highlights-grid {
			grid-template-columns: 1fr;
		}

		.privacy-highlights {
			padding: 1.5rem;
		}
	}
</style>