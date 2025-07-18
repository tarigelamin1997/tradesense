<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import { authStore } from '$lib/stores/auth';
    import Icon from '$lib/components/Icon.svelte';
    
    let user = null;
    let flags = [];
    let loading = true;
    let error = null;
    let showCreateModal = false;
    let showEditModal = false;
    let selectedFlag = null;
    
    // Form data
    let flagForm = {
        key: '',
        name: '',
        description: '',
        type: 'boolean',
        default_value: false,
        targeting_rules: [],
        variants: {}
    };
    
    // New targeting rule form
    let newRule = {
        user_tiers: [],
        user_percentage: 100,
        min_trades: 0
    };
    
    authStore.subscribe(value => {
        user = value.user;
        if (!user?.is_admin) {
            window.location.href = '/';
        }
    });
    
    async function loadFlags() {
        try {
            loading = true;
            error = null;
            
            const response = await api.get('/feature-flags/?include_inactive=true');
            flags = response.flags;
            
        } catch (err) {
            error = err.message || 'Failed to load feature flags';
        } finally {
            loading = false;
        }
    }
    
    async function createFlag() {
        try {
            // Prepare data
            const data = {
                ...flagForm,
                default_value: flagForm.type === 'boolean' ? 
                    flagForm.default_value === true : 
                    flagForm.default_value
            };
            
            await api.post('/feature-flags/', data);
            
            showCreateModal = false;
            resetForm();
            await loadFlags();
            
        } catch (err) {
            error = err.message || 'Failed to create feature flag';
        }
    }
    
    async function updateFlag() {
        if (!selectedFlag) return;
        
        try {
            const updates = {
                name: flagForm.name,
                description: flagForm.description,
                status: flagForm.status,
                default_value: flagForm.default_value,
                targeting_rules: flagForm.targeting_rules
            };
            
            await api.put(`/feature-flags/${selectedFlag.id}`, updates);
            
            showEditModal = false;
            selectedFlag = null;
            resetForm();
            await loadFlags();
            
        } catch (err) {
            error = err.message || 'Failed to update feature flag';
        }
    }
    
    async function toggleFlag(flag) {
        try {
            const newStatus = flag.status === 'active' ? 'inactive' : 'active';
            await api.put(`/feature-flags/${flag.id}`, { status: newStatus });
            await loadFlags();
            
        } catch (err) {
            error = err.message || 'Failed to toggle feature flag';
        }
    }
    
    async function deleteFlag(flagId) {
        if (!confirm('Are you sure you want to delete this feature flag?')) {
            return;
        }
        
        try {
            await api.delete(`/feature-flags/${flagId}`);
            await loadFlags();
            
        } catch (err) {
            error = err.message || 'Failed to delete feature flag';
        }
    }
    
    async function testFlag(flag) {
        const testUserId = prompt('Enter user ID to test with:');
        if (!testUserId) return;
        
        try {
            const response = await api.post(`/feature-flags/test/${flag.key}`, {
                test_user_id: testUserId
            });
            
            alert(`Flag value for user ${testUserId}: ${JSON.stringify(response.value)}`);
            
        } catch (err) {
            alert(`Test failed: ${err.message}`);
        }
    }
    
    function editFlag(flag) {
        selectedFlag = flag;
        flagForm = {
            key: flag.key,
            name: flag.name,
            description: flag.description,
            type: flag.type,
            status: flag.status,
            default_value: flag.default_value,
            targeting_rules: flag.targeting_rules || [],
            variants: flag.variants || {}
        };
        showEditModal = true;
    }
    
    function addTargetingRule() {
        flagForm.targeting_rules = [
            ...flagForm.targeting_rules,
            { ...newRule }
        ];
        
        // Reset rule form
        newRule = {
            user_tiers: [],
            user_percentage: 100,
            min_trades: 0
        };
    }
    
    function removeTargetingRule(index) {
        flagForm.targeting_rules = flagForm.targeting_rules.filter((_, i) => i !== index);
    }
    
    function resetForm() {
        flagForm = {
            key: '',
            name: '',
            description: '',
            type: 'boolean',
            default_value: false,
            targeting_rules: [],
            variants: {}
        };
        
        newRule = {
            user_tiers: [],
            user_percentage: 100,
            min_trades: 0
        };
    }
    
    function getFlagTypeIcon(type) {
        const icons = {
            boolean: 'toggle-left',
            percentage: 'percent',
            user_list: 'users',
            variant: 'shuffle'
        };
        return icons[type] || 'flag';
    }
    
    function getStatusColor(status) {
        const colors = {
            active: 'text-green-600 bg-green-100',
            inactive: 'text-gray-600 bg-gray-100',
            scheduled: 'text-blue-600 bg-blue-100',
            expired: 'text-red-600 bg-red-100'
        };
        return colors[status] || 'text-gray-600 bg-gray-100';
    }
    
    onMount(() => {
        loadFlags();
    });
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-8 flex justify-between items-center">
        <div>
            <h1 class="text-3xl font-bold text-gray-900">Feature Flags</h1>
            <p class="mt-2 text-gray-600">Manage feature rollouts and A/B tests</p>
        </div>
        <button
            on:click={() => showCreateModal = true}
            class="btn btn-primary"
        >
            <Icon name="plus" class="w-5 h-5 mr-2" />
            Create Flag
        </button>
    </div>
    
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="spinner"></div>
        </div>
    {:else if error}
        <div class="alert alert-error mb-6">{error}</div>
    {:else}
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Flag
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Type
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Default Value
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Targeting
                        </th>
                        <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Actions
                        </th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    {#each flags as flag}
                        <tr>
                            <td class="px-6 py-4">
                                <div>
                                    <p class="text-sm font-medium text-gray-900">{flag.name}</p>
                                    <p class="text-xs text-gray-500 font-mono">{flag.key}</p>
                                    {#if flag.description}
                                        <p class="text-xs text-gray-600 mt-1">{flag.description}</p>
                                    {/if}
                                </div>
                            </td>
                            <td class="px-6 py-4">
                                <div class="flex items-center">
                                    <Icon 
                                        name={getFlagTypeIcon(flag.type)}
                                        class="w-4 h-4 text-gray-400 mr-2"
                                    />
                                    <span class="text-sm text-gray-900 capitalize">
                                        {flag.type.replace('_', ' ')}
                                    </span>
                                </div>
                            </td>
                            <td class="px-6 py-4">
                                <span class="inline-flex px-2 py-1 text-xs font-medium rounded-full
                                           {getStatusColor(flag.status)}">
                                    {flag.status}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-900">
                                {#if flag.type === 'boolean'}
                                    {flag.default_value ? 'Enabled' : 'Disabled'}
                                {:else}
                                    {flag.default_value}
                                {/if}
                            </td>
                            <td class="px-6 py-4">
                                {#if flag.targeting_rules && flag.targeting_rules.length > 0}
                                    <div class="text-xs text-gray-600">
                                        {flag.targeting_rules.length} rule{flag.targeting_rules.length > 1 ? 's' : ''}
                                    </div>
                                {:else}
                                    <span class="text-xs text-gray-400">No targeting</span>
                                {/if}
                            </td>
                            <td class="px-6 py-4 text-right text-sm font-medium">
                                <div class="flex items-center justify-end space-x-2">
                                    <button
                                        on:click={() => toggleFlag(flag)}
                                        class="text-gray-400 hover:text-gray-600"
                                        title="Toggle status"
                                    >
                                        <Icon name={flag.status === 'active' ? 'toggle-right' : 'toggle-left'} 
                                              class="w-5 h-5" />
                                    </button>
                                    <button
                                        on:click={() => editFlag(flag)}
                                        class="text-indigo-600 hover:text-indigo-900"
                                        title="Edit flag"
                                    >
                                        <Icon name="edit" class="w-5 h-5" />
                                    </button>
                                    <button
                                        on:click={() => testFlag(flag)}
                                        class="text-green-600 hover:text-green-900"
                                        title="Test flag"
                                    >
                                        <Icon name="play" class="w-5 h-5" />
                                    </button>
                                    <a
                                        href="/admin/feature-flags/{flag.key}/analytics"
                                        class="text-blue-600 hover:text-blue-900"
                                        title="View analytics"
                                    >
                                        <Icon name="bar-chart-2" class="w-5 h-5" />
                                    </a>
                                    {#if !flag.id.startsWith('default_')}
                                        <button
                                            on:click={() => deleteFlag(flag.id)}
                                            class="text-red-600 hover:text-red-900"
                                            title="Delete flag"
                                        >
                                            <Icon name="trash" class="w-5 h-5" />
                                        </button>
                                    {/if}
                                </div>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    {/if}
</div>

<!-- Create Flag Modal -->
{#if showCreateModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Create Feature Flag</h3>
            
            <form on:submit|preventDefault={createFlag} class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Key *
                        </label>
                        <input
                            type="text"
                            bind:value={flagForm.key}
                            pattern="[a-z0-9_]+"
                            class="form-input"
                            placeholder="feature_key"
                            required
                        />
                        <p class="mt-1 text-xs text-gray-500">
                            Lowercase letters, numbers, and underscores only
                        </p>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Name *
                        </label>
                        <input
                            type="text"
                            bind:value={flagForm.name}
                            class="form-input"
                            placeholder="Feature Name"
                            required
                        />
                    </div>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Description
                    </label>
                    <textarea
                        bind:value={flagForm.description}
                        rows="2"
                        class="form-textarea"
                        placeholder="What does this feature do?"
                    ></textarea>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Type
                        </label>
                        <select bind:value={flagForm.type} class="form-select">
                            <option value="boolean">Boolean (On/Off)</option>
                            <option value="percentage">Percentage Rollout</option>
                            <option value="user_list">User List</option>
                            <option value="variant">A/B Test Variant</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Default Value
                        </label>
                        {#if flagForm.type === 'boolean'}
                            <select bind:value={flagForm.default_value} class="form-select">
                                <option value={false}>Disabled</option>
                                <option value={true}>Enabled</option>
                            </select>
                        {:else}
                            <input
                                type="text"
                                bind:value={flagForm.default_value}
                                class="form-input"
                                placeholder="Default value"
                            />
                        {/if}
                    </div>
                </div>
                
                <!-- Targeting Rules -->
                <div>
                    <h4 class="text-sm font-medium text-gray-700 mb-2">Targeting Rules</h4>
                    
                    {#if flagForm.targeting_rules.length > 0}
                        <div class="space-y-2 mb-4">
                            {#each flagForm.targeting_rules as rule, index}
                                <div class="bg-gray-50 rounded-md p-3 relative">
                                    <button
                                        type="button"
                                        on:click={() => removeTargetingRule(index)}
                                        class="absolute top-2 right-2 text-red-600 hover:text-red-800"
                                    >
                                        <Icon name="x" class="w-4 h-4" />
                                    </button>
                                    
                                    <div class="text-sm">
                                        {#if rule.user_tiers?.length > 0}
                                            <p>Tiers: {rule.user_tiers.join(', ')}</p>
                                        {/if}
                                        {#if rule.user_percentage < 100}
                                            <p>Rollout: {rule.user_percentage}%</p>
                                        {/if}
                                        {#if rule.min_trades > 0}
                                            <p>Min trades: {rule.min_trades}</p>
                                        {/if}
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {/if}
                    
                    <div class="border border-gray-300 rounded-md p-3">
                        <p class="text-sm font-medium text-gray-700 mb-2">Add Rule</p>
                        <div class="grid grid-cols-3 gap-2">
                            <div>
                                <label class="block text-xs text-gray-600">User Tiers</label>
                                <select 
                                    multiple
                                    bind:value={newRule.user_tiers}
                                    class="form-select text-sm"
                                    size="3"
                                >
                                    <option value="free">Free</option>
                                    <option value="pro">Pro</option>
                                    <option value="premium">Premium</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs text-gray-600">Percentage</label>
                                <input
                                    type="number"
                                    bind:value={newRule.user_percentage}
                                    min="0"
                                    max="100"
                                    class="form-input text-sm"
                                />
                            </div>
                            <div>
                                <label class="block text-xs text-gray-600">Min Trades</label>
                                <input
                                    type="number"
                                    bind:value={newRule.min_trades}
                                    min="0"
                                    class="form-input text-sm"
                                />
                            </div>
                        </div>
                        <button
                            type="button"
                            on:click={addTargetingRule}
                            class="mt-2 text-sm text-indigo-600 hover:text-indigo-700"
                        >
                            + Add Rule
                        </button>
                    </div>
                </div>
                
                <div class="mt-6 flex justify-end space-x-3">
                    <button
                        type="button"
                        on:click={() => {showCreateModal = false; resetForm();}}
                        class="btn btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        class="btn btn-primary"
                    >
                        Create Flag
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<!-- Edit Flag Modal -->
{#if showEditModal && selectedFlag}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Edit Feature Flag</h3>
            
            <form on:submit|preventDefault={updateFlag} class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Key
                    </label>
                    <input
                        type="text"
                        value={flagForm.key}
                        class="form-input bg-gray-100"
                        disabled
                    />
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Name
                    </label>
                    <input
                        type="text"
                        bind:value={flagForm.name}
                        class="form-input"
                        required
                    />
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Description
                    </label>
                    <textarea
                        bind:value={flagForm.description}
                        rows="2"
                        class="form-textarea"
                    ></textarea>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Status
                        </label>
                        <select bind:value={flagForm.status} class="form-select">
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Default Value
                        </label>
                        {#if flagForm.type === 'boolean'}
                            <select bind:value={flagForm.default_value} class="form-select">
                                <option value={false}>Disabled</option>
                                <option value={true}>Enabled</option>
                            </select>
                        {:else}
                            <input
                                type="text"
                                bind:value={flagForm.default_value}
                                class="form-input"
                            />
                        {/if}
                    </div>
                </div>
                
                <div class="mt-6 flex justify-end space-x-3">
                    <button
                        type="button"
                        on:click={() => {showEditModal = false; selectedFlag = null; resetForm();}}
                        class="btn btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        class="btn btn-primary"
                    >
                        Update Flag
                    </button>
                </div>
            </form>
        </div>
    </div>
{/if}

<style>
    .spinner {
        @apply w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin;
    }
    
    .form-input, .form-select, .form-textarea {
        @apply w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500;
    }
    
    .btn {
        @apply px-4 py-2 rounded-md font-medium transition-colors;
    }
    
    .btn-primary {
        @apply bg-indigo-600 text-white hover:bg-indigo-700;
    }
    
    .btn-secondary {
        @apply bg-gray-200 text-gray-800 hover:bg-gray-300;
    }
    
    .alert {
        @apply p-4 rounded-md;
    }
    
    .alert-error {
        @apply bg-red-50 text-red-800 border border-red-200;
    }
</style>