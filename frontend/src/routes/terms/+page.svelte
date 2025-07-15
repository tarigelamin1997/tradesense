<script lang="ts">
	import { ChevronLeft } from 'lucide-svelte';
	
	const lastUpdated = new Date().toLocaleDateString('en-US', { 
		year: 'numeric', 
		month: 'long', 
		day: 'numeric' 
	});
</script>

<svelte:head>
	<title>Terms of Service - TradeSense</title>
	<meta name="description" content="TradeSense Terms of Service - Read our terms and conditions for using our trading journal and analytics platform.">
</svelte:head>

<div class="legal-page">
	<div class="legal-header">
		<a href="/" class="back-link">
			<ChevronLeft size={20} />
			Back to Home
		</a>
		<div class="header-content">
			<h1>Terms of Service</h1>
			<p class="last-updated">Last updated: {lastUpdated}</p>
		</div>
	</div>

	<div class="legal-content">
		<section>
			<h2>1. Acceptance of Terms</h2>
			<p>
				By accessing and using TradeSense ("Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
			</p>
		</section>

		<section>
			<h2>2. Description of Service</h2>
			<p>
				TradeSense provides a trading journal and analytics platform that allows users to:
			</p>
			<ul>
				<li>Track and analyze trading performance</li>
				<li>Import trade data from various sources</li>
				<li>Generate reports and insights</li>
				<li>Access educational content and tools</li>
			</ul>
			<p>
				The Service is provided "as is" and we reserve the right to modify or discontinue features at any time.
			</p>
		</section>

		<section>
			<h2>3. User Accounts</h2>
			<h3>3.1 Account Creation</h3>
			<p>
				To use certain features of the Service, you must register for an account. You agree to:
			</p>
			<ul>
				<li>Provide accurate, current, and complete information</li>
				<li>Maintain the security of your password</li>
				<li>Notify us immediately of any unauthorized use</li>
				<li>Accept responsibility for all activities under your account</li>
			</ul>

			<h3>3.2 Account Termination</h3>
			<p>
				We reserve the right to suspend or terminate accounts that violate these terms or for any other reason at our sole discretion.
			</p>
		</section>

		<section>
			<h2>4. Privacy and Data Protection</h2>
			<p>
				Your use of the Service is also governed by our <a href="/privacy">Privacy Policy</a>, which describes how we collect, use, and protect your information.
			</p>
		</section>

		<section>
			<h2>5. User Content and Data</h2>
			<h3>5.1 Ownership</h3>
			<p>
				You retain ownership of all trade data and content you upload to the Service. By uploading content, you grant us a license to use, store, and process this data to provide the Service.
			</p>

			<h3>5.2 Data Accuracy</h3>
			<p>
				You are responsible for the accuracy of your trade data. We are not responsible for any losses resulting from inaccurate data or analysis.
			</p>
		</section>

		<section>
			<h2>6. Acceptable Use Policy</h2>
			<p>You agree not to:</p>
			<ul>
				<li>Use the Service for any unlawful purpose</li>
				<li>Attempt to gain unauthorized access to any portion of the Service</li>
				<li>Interfere with or disrupt the Service</li>
				<li>Upload malicious code or content</li>
				<li>Impersonate another person or entity</li>
				<li>Scrape or copy content without permission</li>
			</ul>
		</section>

		<section>
			<h2>7. Payment Terms</h2>
			<h3>7.1 Subscription Plans</h3>
			<p>
				Certain features require a paid subscription. By subscribing, you agree to pay the fees associated with your chosen plan.
			</p>

			<h3>7.2 Billing</h3>
			<ul>
				<li>Subscriptions are billed in advance on a monthly or annual basis</li>
				<li>Prices are subject to change with 30 days notice</li>
				<li>All fees are non-refundable except as required by law</li>
			</ul>

			<h3>7.3 Cancellation</h3>
			<p>
				You may cancel your subscription at any time. Access continues until the end of the current billing period.
			</p>
		</section>

		<section>
			<h2>8. Intellectual Property</h2>
			<p>
				The Service and its original content (excluding user content) are and will remain the exclusive property of TradeSense and its licensors. The Service is protected by copyright, trademark, and other laws.
			</p>
		</section>

		<section>
			<h2>9. Disclaimers</h2>
			<h3>9.1 No Financial Advice</h3>
			<p class="disclaimer">
				<strong>Important:</strong> TradeSense does not provide financial advice. All analysis and insights are for informational purposes only. Always consult with qualified financial advisors before making investment decisions.
			</p>

			<h3>9.2 No Warranty</h3>
			<p>
				The Service is provided "as is" without warranties of any kind, either express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, or non-infringement.
			</p>
		</section>

		<section>
			<h2>10. Limitation of Liability</h2>
			<p>
				To the maximum extent permitted by law, TradeSense shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including but not limited to loss of profits, data, or use, arising from your use of the Service.
			</p>
		</section>

		<section>
			<h2>11. Indemnification</h2>
			<p>
				You agree to indemnify and hold harmless TradeSense and its officers, directors, employees, and agents from any claims, damages, or expenses arising from your use of the Service or violation of these Terms.
			</p>
		</section>

		<section>
			<h2>12. Changes to Terms</h2>
			<p>
				We reserve the right to modify these Terms at any time. We will notify users of any material changes via email or through the Service. Continued use after changes constitutes acceptance of the new Terms.
			</p>
		</section>

		<section>
			<h2>13. Governing Law</h2>
			<p>
				These Terms shall be governed by and construed in accordance with the laws of the United States and the State of Delaware, without regard to conflict of law principles.
			</p>
		</section>

		<section>
			<h2>14. Contact Information</h2>
			<p>
				If you have any questions about these Terms, please contact us at:
			</p>
			<ul>
				<li>Email: legal@tradesense.io</li>
				<li>Address: TradeSense Inc., 123 Market Street, Suite 100, San Francisco, CA 94105</li>
			</ul>
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

	a {
		color: #10b981;
		text-decoration: none;
	}

	a:hover {
		text-decoration: underline;
	}

	.disclaimer {
		background: #fef3c7;
		border: 1px solid #f59e0b;
		padding: 1rem;
		border-radius: 6px;
		margin: 1rem 0;
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
	}
</style>