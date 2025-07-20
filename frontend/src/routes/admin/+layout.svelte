<script>
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import { onMount } from 'svelte';
    import { authStore } from '$lib/stores/auth';
    import Icon from '$lib/components/Icon.svelte';
    
    let user = null;
    
    authStore.subscribe(value => {
        user = value.user;
        // Redirect if not admin
        if (user && user.role !== 'admin') {
            goto('/dashboard');
        }
    });
    
    onMount(() => {
        // Check if user is admin
        if (!user || user.role !== 'admin') {
            goto('/dashboard');
        }
    });
    
    const navigation = [
        { href: '/admin', label: 'Dashboard', icon: 'chart-bar' },
        { href: '/admin/users', label: 'Users', icon: 'users' },
        { href: '/admin/feedback', label: 'Feedback', icon: 'message-square' },
        { href: '/admin/analytics', label: 'Analytics', icon: 'chart-line' },
        { href: '/admin/support', label: 'Support', icon: 'headset' },
        { href: '/admin/settings', label: 'Settings', icon: 'cog' },
    ];
</script>

<div class="min-h-screen bg-gray-50">
    <!-- Admin Header -->
    <header class="bg-white shadow-sm border-b border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <div class="flex items-center">
                    <h1 class="text-2xl font-bold text-gray-900">TradeSense Admin</h1>
                    <span class="ml-3 px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                        Admin Panel
                    </span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/dashboard" class="text-sm text-gray-600 hover:text-gray-900">
                        Back to App
                    </a>
                    <div class="h-6 w-px bg-gray-300"></div>
                    <div class="text-sm text-gray-600">
                        {user?.email}
                    </div>
                </div>
            </div>
        </div>
    </header>
    
    <div class="flex">
        <!-- Sidebar Navigation -->
        <nav class="w-64 bg-white shadow-sm min-h-screen">
            <div class="p-4">
                <ul class="space-y-2">
                    {#each navigation as item}
                        <li>
                            <a
                                href={item.href}
                                class="flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors
                                       {$page.url.pathname === item.href
                                        ? 'bg-indigo-100 text-indigo-700'
                                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}"
                            >
                                <Icon name={item.icon} class="w-5 h-5 mr-3" />
                                {item.label}
                            </a>
                        </li>
                    {/each}
                </ul>
            </div>
            
            <!-- Admin Quick Stats -->
            <div class="p-4 mt-8 border-t border-gray-200">
                <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                    Quick Stats
                </h3>
                <div class="space-y-3">
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Total Users</span>
                        <span class="font-medium">--</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">Active Today</span>
                        <span class="font-medium">--</span>
                    </div>
                    <div class="flex justify-between text-sm">
                        <span class="text-gray-600">MRR</span>
                        <span class="font-medium">--</span>
                    </div>
                </div>
            </div>
        </nav>
        
        <!-- Main Content -->
        <main class="flex-1 p-6">
            <slot />
        </main>
    </div>
</div>

<style>
    /* Custom admin styles */
    :global(.admin-card) {
        background-color: white;
        border-radius: 0.5rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        border: 1px solid #e5e7eb;
        padding: 1.5rem;
    }
    
    :global(.admin-table) {
        min-width: 100%;
        border-collapse: collapse;
    }
    
    :global(.admin-table > * > tr) {
        border-bottom: 1px solid #e5e7eb;
    }
    
    :global(.admin-table thead) {
        background-color: #f9fafb;
    }
    
    :global(.admin-table th) {
        padding: 0.75rem 1.5rem;
        text-align: left;
        font-size: 0.75rem;
        font-weight: 500;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    :global(.admin-table td) {
        padding: 1rem 1.5rem;
        white-space: nowrap;
        font-size: 0.875rem;
        color: #111827;
    }
</style>