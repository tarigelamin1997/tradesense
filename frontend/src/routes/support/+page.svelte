<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { api } from '$lib/api/client-safe';
    import { authStore } from '$lib/stores/auth';
    import Icon from '$lib/components/Icon.svelte';
    import analytics from '$lib/analytics';
    
    let user = null;
    let activeTab = 'tickets';
    let tickets = [];
    let kbArticles = [];
    let categories = [];
    let searchQuery = '';
    let loading = true;
    let error = null;
    
    // New ticket form
    let showNewTicket = false;
    let ticketForm = {
        subject: '',
        description: '',
        category: 'technical'
    };
    
    // KB search results
    let searchResults = [];
    let searching = false;
    
    authStore.subscribe(value => {
        user = value.user;
    });
    
    async function loadSupportData() {
        try {
            loading = true;
            error = null;
            
            if (activeTab === 'tickets' && user) {
                // Load user's tickets
                const response = await api.get('/support/tickets?limit=20');
                tickets = response.tickets;
            } else {
                // Load KB data
                const [categoriesData, popularData] = await Promise.all([
                    api.get('/support/kb/categories'),
                    api.get('/support/kb/articles/popular?limit=10')
                ]);
                
                categories = categoriesData.categories;
                kbArticles = popularData.articles;
            }
            
            analytics.trackPageView('/support');
            
        } catch (err) {
            error = err.message || 'Failed to load support data';
        } finally {
            loading = false;
        }
    }
    
    async function searchKnowledgeBase() {
        if (!searchQuery.trim() || searchQuery.length < 2) {
            searchResults = [];
            return;
        }
        
        try {
            searching = true;
            const response = await api.get(`/support/kb/search?q=${encodeURIComponent(searchQuery)}`);
            searchResults = response.results;
            
            analytics.trackAction('search_kb', 'support', { query: searchQuery });
            
        } catch (err) {
            console.error('Search failed:', err);
        } finally {
            searching = false;
        }
    }
    
    async function createTicket() {
        if (!ticketForm.subject || !ticketForm.description) {
            error = 'Please fill in all required fields';
            return;
        }
        
        try {
            const response = await api.post('/support/tickets', {
                subject: ticketForm.subject,
                description: ticketForm.description,
                category: ticketForm.category
            });
            
            analytics.trackAction('create_ticket', 'support', { category: ticketForm.category });
            
            // Show suggested articles if any
            if (response.suggested_articles && response.suggested_articles.length > 0) {
                // Could show a modal with suggestions
                console.log('Suggested articles:', response.suggested_articles);
            }
            
            // Redirect to ticket details
            goto(`/support/tickets/${response.ticket.ticket_id}`);
            
        } catch (err) {
            error = err.message || 'Failed to create ticket';
        }
    }
    
    function getStatusColor(status) {
        const colors = {
            open: 'bg-blue-100 text-blue-800',
            in_progress: 'bg-yellow-100 text-yellow-800',
            waiting_customer: 'bg-purple-100 text-purple-800',
            resolved: 'bg-green-100 text-green-800',
            closed: 'bg-gray-100 text-gray-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    }
    
    function getPriorityIcon(priority) {
        const icons = {
            urgent: { name: 'alert-circle', class: 'text-red-500' },
            high: { name: 'arrow-up', class: 'text-orange-500' },
            medium: { name: 'minus', class: 'text-yellow-500' },
            low: { name: 'arrow-down', class: 'text-gray-500' }
        };
        return icons[priority] || icons.medium;
    }
    
    function formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    let searchTimeout;
    function debounceSearch() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(searchKnowledgeBase, 300);
    }
    
    onMount(() => {
        loadSupportData();
    });
    
    $: if (activeTab) loadSupportData();
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Support Center</h1>
        <p class="mt-2 text-gray-600">Get help with TradeSense</p>
    </div>
    
    <!-- Tab Navigation -->
    <div class="border-b border-gray-200 mb-6">
        <nav class="-mb-px flex space-x-8">
            <button
                on:click={() => activeTab = 'tickets'}
                class="py-2 px-1 border-b-2 font-medium text-sm transition-colors
                       {activeTab === 'tickets' 
                        ? 'border-indigo-500 text-indigo-600' 
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
            >
                My Tickets
            </button>
            <button
                on:click={() => activeTab = 'knowledge'}
                class="py-2 px-1 border-b-2 font-medium text-sm transition-colors
                       {activeTab === 'knowledge' 
                        ? 'border-indigo-500 text-indigo-600' 
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
            >
                Knowledge Base
            </button>
        </nav>
    </div>
    
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="spinner"></div>
        </div>
    {:else if error}
        <div class="alert alert-error mb-6">{error}</div>
    {:else}
        {#if activeTab === 'tickets'}
            <!-- Tickets Tab -->
            {#if user}
                <div class="mb-6 flex justify-between items-center">
                    <h2 class="text-xl font-semibold text-gray-900">Support Tickets</h2>
                    <button
                        on:click={() => showNewTicket = true}
                        class="btn btn-primary"
                    >
                        <Icon name="plus" class="w-5 h-5 mr-2" />
                        New Ticket
                    </button>
                </div>
                
                {#if tickets.length === 0}
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
                        <Icon name="inbox" class="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <p class="text-gray-600">No support tickets yet</p>
                        <p class="text-sm text-gray-500 mt-2">
                            Need help? Create a ticket and we'll assist you.
                        </p>
                    </div>
                {:else}
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Subject
                                    </th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Priority
                                    </th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Created
                                    </th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Last Update
                                    </th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                {#each tickets as ticket}
                                    <tr class="hover:bg-gray-50 cursor-pointer"
                                        on:click={() => goto(`/support/tickets/${ticket.id}`)}>
                                        <td class="px-6 py-4">
                                            <div>
                                                <p class="text-sm font-medium text-gray-900">
                                                    {ticket.subject}
                                                </p>
                                                <p class="text-sm text-gray-500">
                                                    #{ticket.id.slice(0, 8)}
                                                </p>
                                            </div>
                                        </td>
                                        <td class="px-6 py-4">
                                            <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full
                                                       {getStatusColor(ticket.status)}">
                                                {ticket.status.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td class="px-6 py-4">
                                            <div class="flex items-center">
                                                <Icon 
                                                    name={getPriorityIcon(ticket.priority).name}
                                                    class="w-4 h-4 mr-1 {getPriorityIcon(ticket.priority).class}"
                                                />
                                                <span class="text-sm text-gray-900 capitalize">
                                                    {ticket.priority}
                                                </span>
                                            </div>
                                        </td>
                                        <td class="px-6 py-4 text-sm text-gray-500">
                                            {formatDate(ticket.created_at)}
                                        </td>
                                        <td class="px-6 py-4 text-sm text-gray-500">
                                            {formatDate(ticket.last_message_at || ticket.updated_at)}
                                        </td>
                                    </tr>
                                {/each}
                            </tbody>
                        </table>
                    </div>
                {/if}
            {:else}
                <div class="bg-blue-50 border border-blue-200 rounded-md p-4">
                    <p class="text-sm text-blue-800">
                        <a href="/login" class="font-medium underline">Sign in</a> to view and create support tickets.
                    </p>
                </div>
            {/if}
            
        {:else}
            <!-- Knowledge Base Tab -->
            <div class="mb-8">
                <!-- Search Box -->
                <div class="relative max-w-2xl mx-auto">
                    <input
                        type="text"
                        bind:value={searchQuery}
                        on:input={debounceSearch}
                        placeholder="Search for help articles..."
                        class="w-full px-4 py-3 pl-12 border border-gray-300 rounded-lg
                               focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                    />
                    <Icon name="search" class="absolute left-4 top-3.5 w-5 h-5 text-gray-400" />
                    {#if searching}
                        <div class="absolute right-4 top-3.5">
                            <div class="spinner-small"></div>
                        </div>
                    {/if}
                </div>
                
                <!-- Search Results -->
                {#if searchResults.length > 0}
                    <div class="mt-6 max-w-2xl mx-auto">
                        <h3 class="text-lg font-medium text-gray-900 mb-4">
                            Search Results ({searchResults.length})
                        </h3>
                        <div class="space-y-4">
                            {#each searchResults as result}
                                {#if result.type === 'quick_answer'}
                                    <div class="bg-indigo-50 rounded-lg p-4">
                                        <h4 class="font-medium text-indigo-900">{result.question}</h4>
                                        <p class="mt-2 text-sm text-indigo-800">{result.answer}</p>
                                        <a 
                                            href="/support/kb/{result.article_id}"
                                            class="inline-block mt-2 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                                        >
                                            Read full article →
                                        </a>
                                    </div>
                                {:else}
                                    <a 
                                        href="/support/kb/{result.slug || result.id}"
                                        class="block bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
                                    >
                                        <h4 class="font-medium text-gray-900">{result.title}</h4>
                                        <p class="mt-1 text-sm text-gray-600">{result.summary}</p>
                                        <div class="mt-2 flex items-center text-xs text-gray-500">
                                            <span class="capitalize">{result.category}</span>
                                            <span class="mx-2">•</span>
                                            <span>{result.view_count} views</span>
                                            {#if result.helpful_rate > 0}
                                                <span class="mx-2">•</span>
                                                <span>{Math.round(result.helpful_rate)}% helpful</span>
                                            {/if}
                                        </div>
                                    </a>
                                {/if}
                            {/each}
                        </div>
                    </div>
                {:else if searchQuery.length >= 2 && !searching}
                    <div class="mt-6 text-center text-gray-600">
                        No articles found for "{searchQuery}"
                    </div>
                {/if}
            </div>
            
            <!-- Categories Grid -->
            {#if !searchQuery}
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {#each categories as category}
                        <a 
                            href="/support/kb/category/{category.id}"
                            class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
                        >
                            <div class="flex items-center mb-4">
                                <div class="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                                    <Icon name={category.icon} class="w-6 h-6 text-indigo-600" />
                                </div>
                                <h3 class="ml-4 text-lg font-medium text-gray-900">{category.name}</h3>
                            </div>
                            <p class="text-sm text-gray-600 mb-4">{category.description}</p>
                            <div class="flex items-center text-sm text-gray-500">
                                <span>{category.article_count} articles</span>
                                <span class="mx-2">•</span>
                                <span>{category.total_views.toLocaleString()} views</span>
                            </div>
                        </a>
                    {/each}
                </div>
                
                <!-- Popular Articles -->
                <div class="mt-12">
                    <h3 class="text-xl font-semibold text-gray-900 mb-6">Popular Articles</h3>
                    <div class="bg-white rounded-lg shadow-sm border border-gray-200 divide-y divide-gray-200">
                        {#each kbArticles as article, index}
                            <a 
                                href="/support/kb/{article.slug || article.id}"
                                class="block px-6 py-4 hover:bg-gray-50 transition-colors"
                            >
                                <div class="flex items-start justify-between">
                                    <div class="flex-1">
                                        <h4 class="text-sm font-medium text-gray-900">
                                            {index + 1}. {article.title}
                                        </h4>
                                        <p class="mt-1 text-sm text-gray-600">{article.summary}</p>
                                    </div>
                                    <div class="ml-4 text-right">
                                        <p class="text-sm text-gray-500">{article.view_count} views</p>
                                        {#if article.helpful_rate > 0}
                                            <p class="text-xs text-green-600">
                                                {Math.round(article.helpful_rate)}% helpful
                                            </p>
                                        {/if}
                                    </div>
                                </div>
                            </a>
                        {/each}
                    </div>
                </div>
            {/if}
        {/if}
    {/if}
</div>

<!-- New Ticket Modal -->
{#if showNewTicket}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Create Support Ticket</h3>
            
            <form on:submit|preventDefault={createTicket} class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Subject *
                    </label>
                    <input
                        type="text"
                        bind:value={ticketForm.subject}
                        class="form-input"
                        placeholder="Brief description of your issue"
                        required
                    />
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Category
                    </label>
                    <select bind:value={ticketForm.category} class="form-select">
                        <option value="billing">Billing & Subscriptions</option>
                        <option value="technical">Technical Issue</option>
                        <option value="account">Account Management</option>
                        <option value="feature_request">Feature Request</option>
                        <option value="bug_report">Bug Report</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Description *
                    </label>
                    <textarea
                        bind:value={ticketForm.description}
                        rows="6"
                        class="form-textarea"
                        placeholder="Please provide detailed information about your issue..."
                        required
                    ></textarea>
                    <p class="mt-1 text-xs text-gray-500">
                        Include steps to reproduce, error messages, and what you expected to happen.
                    </p>
                </div>
                
                <div class="mt-6 flex justify-end space-x-3">
                    <button
                        type="button"
                        on:click={() => showNewTicket = false}
                        class="btn btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        class="btn btn-primary"
                    >
                        Create Ticket
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<style>
    .spinner {
        width: 2rem; height: 2rem; border-width: 4px; border-color: #c7d2fe; border-top-color: #4f46e5; border-radius: 9999px; animation: spin 1s linear infinite;
    }
    
    .spinner-small {
        width: 1.25rem;
        height: 1.25rem;
        border-width: 2px;
        border-style: solid;
        border-color: #c7d2fe;
        border-top-color: #4f46e5;
        border-radius: 9999px;
        animation: spin 1s linear infinite;
    }
    
    .form-input, .form-select, .form-textarea {
        width: 100%;
        border-radius: 0.375rem;
        border-color: #d1d5db;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    .form-input:focus, .form-select:focus, .form-textarea:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    .btn {
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: background-color 0.15s ease-in-out, color 0.15s ease-in-out;
    }
    
    .btn-primary {
        background-color: #4f46e5;
        color: white;
    }
    
    .btn-primary:hover {
        background-color: #4338ca;
    }
    
    .btn-secondary {
        background-color: #e5e7eb;
        color: #1f2937;
    }
    
    .btn-secondary:hover {
        background-color: #d1d5db;
    }
    
    .alert {
        padding: 1rem; border-radius: 0.375rem;
    }
    
    .alert-error {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }
</style>