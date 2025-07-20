<script>
    import { onMount } from 'svelte';
    import { browser } from '$app/environment';
    import { api } from '$lib/api/client';
    import Icon from '$lib/components/Icon.svelte';
    import analytics from '$lib/analytics';
    
    let users = [];
    let loading = true;
    let error = null;
    let selectedUsers = new Set();
    
    // Pagination
    let currentPage = 1;
    let pageSize = 50;
    let totalUsers = 0;
    
    // Filters
    let searchQuery = '';
    let filterTier = '';
    let filterStatus = '';
    let sortBy = 'created_at';
    let sortOrder = 'desc';
    
    // User details modal
    let selectedUser = null;
    let showUserModal = false;
    
    // Edit user
    let editingUser = null;
    let showEditModal = false;
    
    async function loadUsers() {
        try {
            loading = true;
            error = null;
            
            const skip = (currentPage - 1) * pageSize;
            const params = new URLSearchParams({
                skip,
                limit: pageSize,
                sort_by: sortBy,
                sort_order: sortOrder
            });
            
            if (searchQuery) params.append('search', searchQuery);
            if (filterTier) params.append('subscription_tier', filterTier);
            if (filterStatus) params.append('status', filterStatus);
            
            const response = await api.get(`/admin/users?${params}`);
            users = response.users;
            totalUsers = response.total;
            
        } catch (err) {
            error = err.message || 'Failed to load users';
        } finally {
            loading = false;
        }
    }
    
    async function viewUserDetails(userId) {
        try {
            const response = await api.get(`/admin/users/${userId}`);
            selectedUser = response;
            showUserModal = true;
            
            analytics.trackAction('view_user_details', 'admin', { user_id: userId });
        } catch (err) {
            error = err.message || 'Failed to load user details';
        }
    }
    
    async function updateUser(userId, updates) {
        try {
            await api.put(`/admin/users/${userId}`, updates);
            await loadUsers();
            showEditModal = false;
            editingUser = null;
            
            analytics.trackAction('update_user', 'admin', { user_id: userId });
        } catch (err) {
            error = err.message || 'Failed to update user';
        }
    }
    
    async function deleteUser(userId) {
        if (!confirm('Are you sure you want to delete this user?')) return;
        
        try {
            await api.delete(`/admin/users/${userId}`);
            await loadUsers();
            
            analytics.trackAction('delete_user', 'admin', { user_id: userId });
        } catch (err) {
            error = err.message || 'Failed to delete user';
        }
    }
    
    async function performBulkAction(action) {
        if (selectedUsers.size === 0) {
            alert('Please select users first');
            return;
        }
        
        try {
            await api.post('/admin/users/bulk-action', {
                user_ids: Array.from(selectedUsers),
                action
            });
            
            selectedUsers.clear();
            await loadUsers();
            
            analytics.trackAction('bulk_action', 'admin', { 
                action, 
                user_count: selectedUsers.size 
            });
        } catch (err) {
            error = err.message || 'Failed to perform bulk action';
        }
    }
    
    async function impersonateUser(userId) {
        if (!confirm('Are you sure you want to impersonate this user?')) return;
        
        try {
            const response = await api.post(`/admin/users/${userId}/impersonate`);
            
            // Store the impersonation token
            if (browser) {
                localStorage.setItem('impersonation_token', response.token);
                localStorage.setItem('impersonated_user', JSON.stringify(response.user));
                
                // Redirect to dashboard as the user
                window.location.href = '/dashboard';
            }
            
        } catch (err) {
            error = err.message || 'Failed to impersonate user';
        }
    }
    
    function toggleUserSelection(userId) {
        if (selectedUsers.has(userId)) {
            selectedUsers.delete(userId);
        } else {
            selectedUsers.add(userId);
        }
        selectedUsers = selectedUsers; // Trigger reactivity
    }
    
    function selectAllUsers() {
        if (selectedUsers.size === users.length) {
            selectedUsers.clear();
        } else {
            users.forEach(user => selectedUsers.add(user.id));
        }
        selectedUsers = selectedUsers; // Trigger reactivity
    }
    
    function formatDate(dateString) {
        if (!dateString) return 'Never';
        return new Date(dateString).toLocaleDateString();
    }
    
    function getTierColor(tier) {
        switch (tier) {
            case 'premium': return 'bg-purple-100 text-purple-800';
            case 'pro': return 'bg-indigo-100 text-indigo-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }
    
    $: totalPages = Math.ceil(totalUsers / pageSize);
    
    // Reload when filters change
    $: if (searchQuery !== undefined || filterTier !== undefined || filterStatus !== undefined || sortBy || sortOrder) {
        currentPage = 1;
        loadUsers();
    }
    
    onMount(() => {
        loadUsers();
    });
</script>

<div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center">
        <div>
            <h2 class="text-2xl font-bold text-gray-900">User Management</h2>
            <p class="text-gray-600 mt-1">Manage users, subscriptions, and access</p>
        </div>
        <button class="btn btn-primary">
            <Icon name="user-plus" class="w-4 h-4 mr-2" />
            Add User
        </button>
    </div>
    
    <!-- Filters -->
    <div class="admin-card">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Search</label>
                <input
                    type="text"
                    bind:value={searchQuery}
                    placeholder="Email or name..."
                    class="form-input"
                />
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Subscription</label>
                <select bind:value={filterTier} class="form-select">
                    <option value="">All Tiers</option>
                    <option value="free">Free</option>
                    <option value="pro">Pro</option>
                    <option value="premium">Premium</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
                <select bind:value={filterStatus} class="form-select">
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                    <option value="paid">Paid Only</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
                <select bind:value={sortBy} class="form-select">
                    <option value="created_at">Join Date</option>
                    <option value="last_login">Last Login</option>
                    <option value="email">Email</option>
                </select>
            </div>
        </div>
    </div>
    
    <!-- Bulk Actions -->
    {#if selectedUsers.size > 0}
        <div class="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
            <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-indigo-900">
                    {selectedUsers.size} user{selectedUsers.size === 1 ? '' : 's'} selected
                </span>
                <div class="space-x-2">
                    <button
                        on:click={() => performBulkAction('activate')}
                        class="btn btn-sm btn-secondary"
                    >
                        Activate
                    </button>
                    <button
                        on:click={() => performBulkAction('deactivate')}
                        class="btn btn-sm btn-secondary"
                    >
                        Deactivate
                    </button>
                    <button
                        on:click={() => selectedUsers.clear()}
                        class="btn btn-sm btn-ghost"
                    >
                        Clear
                    </button>
                </div>
            </div>
        </div>
    {/if}
    
    <!-- Users Table -->
    <div class="admin-card">
        {#if loading}
            <div class="flex justify-center py-8">
                <div class="spinner"></div>
            </div>
        {:else if error}
            <div class="alert alert-error">{error}</div>
        {:else}
            <div class="overflow-x-auto">
                <table class="admin-table">
                    <thead>
                        <tr>
                            <th>
                                <input
                                    type="checkbox"
                                    checked={selectedUsers.size === users.length && users.length > 0}
                                    on:change={selectAllUsers}
                                    class="form-checkbox"
                                />
                            </th>
                            <th>User</th>
                            <th>Subscription</th>
                            <th>Status</th>
                            <th>Trades</th>
                            <th>Joined</th>
                            <th>Last Login</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
                        {#each users as user}
                            <tr class="hover:bg-gray-50">
                                <td>
                                    <input
                                        type="checkbox"
                                        checked={selectedUsers.has(user.id)}
                                        on:change={() => toggleUserSelection(user.id)}
                                        class="form-checkbox"
                                    />
                                </td>
                                <td>
                                    <div>
                                        <div class="text-sm font-medium text-gray-900">
                                            {user.full_name}
                                        </div>
                                        <div class="text-sm text-gray-500">
                                            {user.email}
                                        </div>
                                    </div>
                                </td>
                                <td>
                                    <span class="px-2 py-1 text-xs font-medium rounded-full {getTierColor(user.subscription_tier)}">
                                        {user.subscription_tier}
                                    </span>
                                </td>
                                <td>
                                    <span class="flex items-center text-sm">
                                        <span class="w-2 h-2 rounded-full mr-2 {user.is_active ? 'bg-green-400' : 'bg-gray-400'}"></span>
                                        {user.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td class="text-center">
                                    {user.trade_count || 0}
                                </td>
                                <td>
                                    {formatDate(user.created_at)}
                                </td>
                                <td>
                                    {formatDate(user.last_login)}
                                </td>
                                <td>
                                    <div class="flex items-center space-x-2">
                                        <button
                                            on:click={() => viewUserDetails(user.id)}
                                            class="text-indigo-600 hover:text-indigo-900"
                                            title="View Details"
                                        >
                                            <Icon name="eye" class="w-4 h-4" />
                                        </button>
                                        <button
                                            on:click={() => {editingUser = user; showEditModal = true;}}
                                            class="text-gray-600 hover:text-gray-900"
                                            title="Edit"
                                        >
                                            <Icon name="pencil" class="w-4 h-4" />
                                        </button>
                                        <button
                                            on:click={() => impersonateUser(user.id)}
                                            class="text-purple-600 hover:text-purple-900"
                                            title="Impersonate"
                                        >
                                            <Icon name="user-switch" class="w-4 h-4" />
                                        </button>
                                        <button
                                            on:click={() => deleteUser(user.id)}
                                            class="text-red-600 hover:text-red-900"
                                            title="Delete"
                                        >
                                            <Icon name="trash" class="w-4 h-4" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        {/each}
                    </tbody>
                </table>
            </div>
            
            <!-- Pagination -->
            <div class="mt-4 flex items-center justify-between">
                <div class="text-sm text-gray-700">
                    Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, totalUsers)} of {totalUsers} users
                </div>
                <div class="flex space-x-2">
                    <button
                        on:click={() => currentPage--}
                        disabled={currentPage === 1}
                        class="btn btn-sm btn-secondary"
                    >
                        Previous
                    </button>
                    <button
                        on:click={() => currentPage++}
                        disabled={currentPage === totalPages}
                        class="btn btn-sm btn-secondary"
                    >
                        Next
                    </button>
                </div>
            </div>
        {/if}
    </div>
</div>

<!-- User Details Modal -->
{#if showUserModal && selectedUser}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div class="p-6">
                <div class="flex justify-between items-start mb-6">
                    <h3 class="text-xl font-semibold text-gray-900">User Details</h3>
                    <button
                        on:click={() => {showUserModal = false; selectedUser = null;}}
                        class="text-gray-400 hover:text-gray-600"
                    >
                        <Icon name="x" class="w-6 h-6" />
                    </button>
                </div>
                
                <!-- User info -->
                <div class="grid grid-cols-2 gap-6 mb-6">
                    <div>
                        <h4 class="font-medium text-gray-900 mb-2">Basic Information</h4>
                        <dl class="space-y-2">
                            <div>
                                <dt class="text-sm text-gray-500">Name</dt>
                                <dd class="text-sm font-medium">{selectedUser.user.full_name}</dd>
                            </div>
                            <div>
                                <dt class="text-sm text-gray-500">Email</dt>
                                <dd class="text-sm font-medium">{selectedUser.user.email}</dd>
                            </div>
                            <div>
                                <dt class="text-sm text-gray-500">Role</dt>
                                <dd class="text-sm font-medium capitalize">{selectedUser.user.role}</dd>
                            </div>
                        </dl>
                    </div>
                    <div>
                        <h4 class="font-medium text-gray-900 mb-2">Subscription</h4>
                        <dl class="space-y-2">
                            <div>
                                <dt class="text-sm text-gray-500">Tier</dt>
                                <dd class="text-sm font-medium capitalize">{selectedUser.user.subscription_tier}</dd>
                            </div>
                            <div>
                                <dt class="text-sm text-gray-500">Status</dt>
                                <dd class="text-sm font-medium">{selectedUser.user.subscription_status}</dd>
                            </div>
                            <div>
                                <dt class="text-sm text-gray-500">Started</dt>
                                <dd class="text-sm font-medium">{formatDate(selectedUser.user.subscription_started_at)}</dd>
                            </div>
                        </dl>
                    </div>
                </div>
                
                <!-- Statistics -->
                <div class="mb-6">
                    <h4 class="font-medium text-gray-900 mb-2">Activity Statistics</h4>
                    <div class="grid grid-cols-4 gap-4">
                        <div class="bg-gray-50 p-3 rounded">
                            <p class="text-xs text-gray-500">Total Events</p>
                            <p class="text-lg font-semibold">{selectedUser.statistics.total_events}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded">
                            <p class="text-xs text-gray-500">Active Days</p>
                            <p class="text-lg font-semibold">{selectedUser.statistics.active_days}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded">
                            <p class="text-xs text-gray-500">Total Sessions</p>
                            <p class="text-lg font-semibold">{selectedUser.statistics.total_sessions}</p>
                        </div>
                        <div class="bg-gray-50 p-3 rounded">
                            <p class="text-xs text-gray-500">Last Activity</p>
                            <p class="text-lg font-semibold">{formatDate(selectedUser.statistics.last_activity)}</p>
                        </div>
                    </div>
                </div>
                
                <!-- Recent Activity -->
                <div>
                    <h4 class="font-medium text-gray-900 mb-2">Recent Activity</h4>
                    <div class="space-y-2 max-h-48 overflow-y-auto">
                        {#each selectedUser.recent_activity as activity}
                            <div class="text-sm border-l-2 border-gray-200 pl-3 py-1">
                                <span class="font-medium">{activity.event_type}</span>
                                <span class="text-gray-500 ml-2">
                                    {new Date(activity.timestamp).toLocaleString()}
                                </span>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>
        </div>
    </div>
{/if}

<!-- Edit User Modal -->
{#if showEditModal && editingUser}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div class="p-6">
                <h3 class="text-xl font-semibold text-gray-900 mb-4">Edit User</h3>
                
                <form on:submit|preventDefault={() => updateUser(editingUser.id, editingUser)}>
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                            <input
                                type="text"
                                bind:value={editingUser.full_name}
                                class="form-input"
                            />
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
                            <input
                                type="email"
                                bind:value={editingUser.email}
                                class="form-input"
                            />
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Subscription Tier</label>
                            <select bind:value={editingUser.subscription_tier} class="form-select">
                                <option value="free">Free</option>
                                <option value="pro">Pro</option>
                                <option value="premium">Premium</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
                            <select bind:value={editingUser.is_active} class="form-select">
                                <option value={true}>Active</option>
                                <option value={false}>Inactive</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="mt-6 flex justify-end space-x-2">
                        <button
                            type="button"
                            on:click={() => {showEditModal = false; editingUser = null;}}
                            class="btn btn-secondary"
                        >
                            Cancel
                        </button>
                        <button type="submit" class="btn btn-primary">
                            Save Changes
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
{/if}

<style>
    .spinner {
        width: 2rem; height: 2rem; border-width: 4px; border-color: #c7d2fe; border-top-color: #4f46e5; border-radius: 9999px; animation: spin 1s linear infinite;
    }
</style>