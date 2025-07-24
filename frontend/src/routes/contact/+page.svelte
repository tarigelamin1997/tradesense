<script lang="ts">
	import { Mail, MessageSquare, Phone, MapPin, Send, AlertCircle } from 'lucide-svelte';
	import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

	let formData = {
		name: '',
		email: '',
		subject: '',
		message: ''
	};

	let loading = false;
	let success = false;
	let error = '';

	const contactInfo = [
		{
			icon: Mail,
			title: 'Email',
			content: 'support@tradesense.com',
			link: 'mailto:support@tradesense.com'
		},
		{
			icon: MessageSquare,
			title: 'Live Chat',
			content: 'Available Mon-Fri, 9AM-6PM EST',
			action: () => {
				// Open chat widget
			}
		},
		{
			icon: Phone,
			title: 'Phone',
			content: '+1 (555) 123-4567',
			link: 'tel:+15551234567'
		},
		{
			icon: MapPin,
			title: 'Office',
			content: '123 Trading Street, New York, NY 10001',
			link: 'https://maps.google.com'
		}
	];

	async function handleSubmit(e: Event) {
		e.preventDefault();
		loading = true;
		error = '';

		try {
			const response = await fetch('/api/contact', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(formData)
			});

			if (!response.ok) {
				throw new Error('Failed to send message');
			}

			success = true;
			formData = {
				name: '',
				email: '',
				subject: '',
				message: ''
			};
		} catch (err) {
			error = 'Failed to send message. Please try again.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Contact Us - TradeSense</title>
	<meta name="description" content="Get in touch with the TradeSense team. We're here to help with any questions about our trading analytics platform." />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
	<!-- Hero Section -->
	<section class="pt-20 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-gray-50 dark:from-gray-800 dark:to-gray-900">
		<div class="max-w-7xl mx-auto text-center">
			<h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
				Get in Touch
			</h1>
			<p class="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
				Have questions about TradeSense? We're here to help. Reach out to our team and we'll get back to you as soon as possible.
			</p>
		</div>
	</section>

	<!-- Contact Form and Info -->
	<section class="py-16 px-4 sm:px-6 lg:px-8">
		<div class="max-w-7xl mx-auto">
			<div class="grid lg:grid-cols-3 gap-12">
				<!-- Contact Form -->
				<div class="lg:col-span-2">
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8">
						<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
							Send us a Message
						</h2>

						{#if success}
							<div class="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
								<p class="text-green-700 dark:text-green-400">
									Thank you for your message! We'll get back to you soon.
								</p>
							</div>
						{/if}

						{#if error}
							<div class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
								<AlertCircle class="h-5 w-5 text-red-600 dark:text-red-400 shrink-0" />
								<p class="text-red-700 dark:text-red-400">
									{error}
								</p>
							</div>
						{/if}

						<form on:submit={handleSubmit} class="space-y-6">
							<div class="grid md:grid-cols-2 gap-6">
								<div>
									<label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
										Your Name
									</label>
									<input
										id="name"
										type="text"
										bind:value={formData.name}
										required
										class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
									/>
								</div>

								<div>
									<label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
										Email Address
									</label>
									<input
										id="email"
										type="email"
										bind:value={formData.email}
										required
										class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
									/>
								</div>
							</div>

							<div>
								<label for="subject" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Subject
								</label>
								<input
									id="subject"
									type="text"
									bind:value={formData.subject}
									required
									class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
								/>
							</div>

							<div>
								<label for="message" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
									Message
								</label>
								<textarea
									id="message"
									bind:value={formData.message}
									required
									rows="6"
									class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
								/>
							</div>

							<button
								type="submit"
								disabled={loading}
								class="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
							>
								{#if loading}
									<LoadingSpinner size="sm" color="white" />
									Sending...
								{:else}
									<Send class="h-5 w-5" />
									Send Message
								{/if}
							</button>
						</form>
					</div>
				</div>

				<!-- Contact Information -->
				<div class="space-y-6">
					<div>
						<h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">
							Other Ways to Reach Us
						</h2>
						
						<div class="space-y-4">
							{#each contactInfo as info}
								<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm">
									<div class="flex items-start gap-4">
										<div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
											<svelte:component this={info.icon} class="h-6 w-6 text-blue-600 dark:text-blue-400" />
										</div>
										<div>
											<h3 class="font-semibold text-gray-900 dark:text-white mb-1">
												{info.title}
											</h3>
											{#if info.link}
												<a
													href={info.link}
													class="text-blue-600 dark:text-blue-400 hover:underline"
													target={info.link.startsWith('http') ? '_blank' : undefined}
													rel={info.link.startsWith('http') ? 'noopener noreferrer' : undefined}
												>
													{info.content}
												</a>
											{:else if info.action}
												<button
													on:click={info.action}
													class="text-blue-600 dark:text-blue-400 hover:underline text-left"
												>
													{info.content}
												</button>
											{:else}
												<p class="text-gray-600 dark:text-gray-400">
													{info.content}
												</p>
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					</div>

					<!-- FAQ Link -->
					<div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6">
						<h3 class="font-semibold text-gray-900 dark:text-white mb-2">
							Looking for quick answers?
						</h3>
						<p class="text-gray-600 dark:text-gray-400 mb-4">
							Check out our frequently asked questions for instant help.
						</p>
						<a
							href="/support/kb"
							class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline font-medium"
						>
							Visit Knowledge Base →
						</a>
					</div>
				</div>
			</div>
		</div>
	</section>
</div>