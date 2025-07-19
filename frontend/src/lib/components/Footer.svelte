<script lang="ts">
	import { Shield, Lock, FileText, Mail } from 'lucide-svelte';
</script>

<footer class="app-footer">
	<div class="footer-content">
		<div class="footer-section">
			<h4>Product</h4>
			<ul>
				<li><a href="/features">Features</a></li>
				<li><a href="/pricing">Pricing</a></li>
				<li><a href="/roadmap">Roadmap</a></li>
				<li><a href="/changelog">Changelog</a></li>
			</ul>
		</div>
		
		<div class="footer-section">
			<h4>Company</h4>
			<ul>
				<li><a href="/about">About</a></li>
				<li><a href="/blog">Blog</a></li>
				<li><a href="/careers">Careers</a></li>
				<li><a href="/contact">Contact</a></li>
			</ul>
		</div>
		
		<div class="footer-section">
			<h4>Resources</h4>
			<ul>
				<li><a href="/docs">Documentation</a></li>
				<li><a href="/api">API Reference</a></li>
				<li><a href="/status">System Status</a></li>
				<li><a href="/support">Support</a></li>
			</ul>
		</div>
		
		<div class="footer-section">
			<h4>Legal</h4>
			<ul>
				<li><a href="/terms" class="legal-link">
					<FileText size={14} />
					Terms of Service
				</a></li>
				<li><a href="/privacy" class="legal-link">
					<Lock size={14} />
					Privacy Policy
				</a></li>
				<li><a href="/security" class="legal-link">
					<Shield size={14} />
					Security
				</a></li>
			</ul>
		</div>
	</div>
	
	<div class="footer-bottom">
		<p>&copy; {new Date().getFullYear()} TradeSense Inc. All rights reserved.</p>
		<div class="footer-badges">
			<span class="badge">SOC2 Compliant</span>
			<span class="badge">GDPR Ready</span>
			<span class="badge">256-bit SSL</span>
		</div>
	</div>
</footer>

<style>
	.app-footer {
		background: #1a1a1a;
		color: #ccc;
		padding: 3rem 0 2rem;
		margin-top: 4rem;
	}

	.footer-content {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 2rem;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 2rem;
		margin-bottom: 3rem;
	}

	.footer-section h4 {
		color: white;
		font-size: 1rem;
		margin-bottom: 1rem;
		font-weight: 600;
	}

	.footer-section ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}

	.footer-section li {
		margin-bottom: 0.5rem;
	}

	.footer-section a {
		color: #ccc;
		text-decoration: none;
		font-size: 0.875rem;
		transition: color 0.2s;
	}

	.footer-section a:hover {
		color: #10b981;
	}

	.legal-link {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
	}

	.footer-bottom {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem 2rem 0;
		border-top: 1px solid #333;
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.footer-bottom p {
		margin: 0;
		font-size: 0.875rem;
		color: #999;
	}

	.footer-badges {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
	}

	.badge {
		background: #333;
		padding: 0.25rem 0.75rem;
		border-radius: 4px;
		font-size: 0.75rem;
		color: #10b981;
		border: 1px solid #10b981;
	}

	@media (max-width: 768px) {
		.footer-content {
			grid-template-columns: repeat(2, 1fr);
			padding: 0 1rem;
		}

		.footer-bottom {
			flex-direction: column;
			text-align: center;
			padding: 2rem 1rem 0;
		}
	}

	@media (max-width: 480px) {
		.footer-content {
			grid-template-columns: 1fr;
		}
	}
</style>