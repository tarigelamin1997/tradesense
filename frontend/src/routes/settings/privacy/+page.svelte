<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import { authStore } from '$lib/stores/auth';
    import Icon from '$lib/components/Icon.svelte';
    import analytics from '$lib/analytics';
    
    let user = null;
    let loading = true;
    let saving = false;
    let error = null;
    let successMessage = null;
    
    // Privacy settings
    let privacySettings = {
        analytics_enabled: true,
        marketing_emails: true,
        data_sharing: false,
        cookie_preferences: {
            necessary: true,
            analytics: true,
            marketing: false
        }
    };
    
    // Export/deletion modals
    let showExportModal = false;
    let showDeletionModal = false;
    let deletionPassword = '';
    let deletionReason = '';
    let deletionFeedback = '';
    
    // Active requests
    let activeRequests = [];
    
    authStore.subscribe(value => {
        user = value.user;
    });
    
    async function loadPrivacySettings() {
        try {
            loading = true;
            error = null;
            
            // Load privacy settings
            const settings = await api.get('/gdpr/privacy-settings');
            privacySettings = settings;
            
            // Check for active GDPR requests
            await checkActiveRequests();
            
            analytics.trackPageView('/settings/privacy');
            
        } catch (err) {
            error = err.message || 'Failed to load privacy settings';
        } finally {
            loading = false;
        }
    }
    
    async function savePrivacySettings() {
        try {
            saving = true;
            error = null;
            successMessage = null;
            
            await api.put('/gdpr/privacy-settings', privacySettings);
            
            successMessage = 'Privacy settings updated successfully';
            
            analytics.trackAction('update_privacy_settings', 'privacy', privacySettings);
            
            // If analytics disabled, stop tracking
            if (!privacySettings.analytics_enabled) {
                analytics.disable();
            }
            
        } catch (err) {
            error = err.message || 'Failed to save privacy settings';
        } finally {
            saving = false;
        }
    }
    
    async function requestDataExport() {
        if (!confirm('This will create a complete export of all your TradeSense data. Continue?')) {
            return;
        }
        
        try {
            error = null;
            const response = await api.post('/gdpr/export', {
                confirmation: true
            });
            
            if (response.request_id) {
                activeRequests = [...activeRequests, {
                    id: response.request_id,
                    type: 'export',
                    status: response.status,
                    requested_at: new Date()
                }];
                
                successMessage = 'Data export requested. You\'ll receive an email when it\'s ready.';
                showExportModal = false;
            }
            
            analytics.trackAction('request_data_export', 'privacy');
            
        } catch (err) {
            error = err.message || 'Failed to request data export';
        }
    }
    
    async function requestAccountDeletion() {
        if (!deletionPassword) {
            error = 'Please enter your password';
            return;
        }
        
        if (!confirm('Are you absolutely sure? This action cannot be undone. All your data will be permanently deleted.')) {
            return;
        }
        
        try {
            error = null;
            const response = await api.delete('/gdpr/account', {
                confirmation: true,
                password: deletionPassword,
                reason: deletionReason,
                feedback: deletionFeedback
            });
            
            if (response.error === 'active_subscription') {
                error = response.message;
                return;
            }
            
            if (response.request_id) {
                // Log out user
                await authStore.logout();
                
                // Redirect to goodbye page
                window.location.href = '/goodbye';
            }
            
        } catch (err) {
            error = err.message || 'Failed to delete account';
        }
    }
    
    async function checkActiveRequests() {
        // In a real implementation, you'd fetch active requests from an endpoint
        // For now, check localStorage for recent requests
        const stored = localStorage.getItem('gdpr_requests');
        if (stored) {
            activeRequests = JSON.parse(stored);
        }
    }
    
    async function checkRequestStatus(requestId) {
        try {
            const status = await api.get(`/gdpr/request/${requestId}`);
            
            // Update request in list
            activeRequests = activeRequests.map(req => 
                req.id === requestId ? { ...req, ...status } : req
            );
            
            // Save to localStorage
            localStorage.setItem('gdpr_requests', JSON.stringify(activeRequests));
            
            if (status.status === 'completed' && status.download_url) {
                // Download file
                window.location.href = `/api/v1${status.download_url}`;
            }
            
        } catch (err) {
            console.error('Failed to check request status:', err);
        }
    }
    
    function toggleCookiePreference(type) {
        if (type === 'necessary') {
            // Necessary cookies cannot be disabled
            return;
        }
        
        privacySettings.cookie_preferences[type] = !privacySettings.cookie_preferences[type];
        
        // If disabling analytics cookies, also disable analytics
        if (type === 'analytics' && !privacySettings.cookie_preferences.analytics) {
            privacySettings.analytics_enabled = false;
        }
    }
    
    onMount(() => {
        loadPrivacySettings();
    });
</script>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Privacy Settings</h1>
        <p class="mt-2 text-gray-600">Control how your data is collected and used</p>
    </div>
    
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="spinner"></div>
        </div>
    {:else}
        {#if error}
            <div class="alert alert-error mb-6">{error}</div>
        {/if}
        
        {#if successMessage}
            <div class="alert alert-success mb-6">{successMessage}</div>
        {/if}
        
        <!-- Privacy Settings -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Data Collection & Usage</h2>
            
            <div class="space-y-6">
                <!-- Analytics -->
                <div class="flex items-start">
                    <div class="flex items-center h-5">
                        <input
                            type="checkbox"
                            bind:checked={privacySettings.analytics_enabled}
                            class="form-checkbox"
                        />
                    </div>
                    <div class="ml-3">
                        <label class="font-medium text-gray-900">Usage Analytics</label>
                        <p class="text-sm text-gray-600 mt-1">
                            Help us improve TradeSense by sharing anonymous usage data. This includes feature usage, 
                            performance metrics, and error reports.
                        </p>
                    </div>
                </div>
                
                <!-- Marketing Emails -->
                <div class="flex items-start">
                    <div class="flex items-center h-5">
                        <input
                            type="checkbox"
                            bind:checked={privacySettings.marketing_emails}
                            class="form-checkbox"
                        />
                    </div>
                    <div class="ml-3">
                        <label class="font-medium text-gray-900">Marketing Communications</label>
                        <p class="text-sm text-gray-600 mt-1">
                            Receive updates about new features, trading tips, and special offers. 
                            You can unsubscribe at any time.
                        </p>
                    </div>
                </div>
                
                <!-- Data Sharing -->
                <div class="flex items-start">
                    <div class="flex items-center h-5">
                        <input
                            type="checkbox"
                            bind:checked={privacySettings.data_sharing}
                            class="form-checkbox"
                        />
                    </div>
                    <div class="ml-3">
                        <label class="font-medium text-gray-900">Anonymous Data Sharing</label>
                        <p class="text-sm text-gray-600 mt-1">
                            Share anonymized trading patterns with our research partners to improve market analysis. 
                            Your personal information is never shared.
                        </p>
                    </div>
                </div>
            </div>
            
            <div class="mt-6">
                <button
                    on:click={savePrivacySettings}
                    disabled={saving}
                    class="btn btn-primary"
                >
                    {saving ? 'Saving...' : 'Save Privacy Settings'}
                </button>
            </div>
        </div>
        
        <!-- Cookie Preferences -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Cookie Preferences</h2>
            
            <div class="space-y-4">
                <!-- Necessary Cookies -->
                <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div class="flex-1">
                        <h3 class="font-medium text-gray-900">Necessary Cookies</h3>
                        <p class="text-sm text-gray-600 mt-1">
                            Required for the website to function properly. Cannot be disabled.
                        </p>
                    </div>
                    <div class="ml-4">
                        <button
                            class="btn btn-sm btn-secondary opacity-50 cursor-not-allowed"
                            disabled
                        >
                            Always On
                        </button>
                    </div>
                </div>
                
                <!-- Analytics Cookies -->
                <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div class="flex-1">
                        <h3 class="font-medium text-gray-900">Analytics Cookies</h3>
                        <p class="text-sm text-gray-600 mt-1">
                            Help us understand how you use TradeSense to improve the experience.
                        </p>
                    </div>
                    <div class="ml-4">
                        <button
                            on:click={() => toggleCookiePreference('analytics')}
                            class="btn btn-sm {privacySettings.cookie_preferences.analytics ? 'btn-primary' : 'btn-secondary'}"
                        >
                            {privacySettings.cookie_preferences.analytics ? 'Enabled' : 'Disabled'}
                        </button>
                    </div>
                </div>
                
                <!-- Marketing Cookies -->
                <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div class="flex-1">
                        <h3 class="font-medium text-gray-900">Marketing Cookies</h3>
                        <p class="text-sm text-gray-600 mt-1">
                            Used to show you relevant offers and measure marketing effectiveness.
                        </p>
                    </div>
                    <div class="ml-4">
                        <button
                            on:click={() => toggleCookiePreference('marketing')}
                            class="btn btn-sm {privacySettings.cookie_preferences.marketing ? 'btn-primary' : 'btn-secondary'}"
                        >
                            {privacySettings.cookie_preferences.marketing ? 'Enabled' : 'Disabled'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Data Management -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Your Data</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Export Data -->
                <div>
                    <h3 class="font-medium text-gray-900 mb-2">Export Your Data</h3>
                    <p class="text-sm text-gray-600 mb-4">
                        Download a complete copy of all your TradeSense data in machine-readable formats.
                    </p>
                    <button
                        on:click={() => showExportModal = true}
                        class="btn btn-secondary"
                    >
                        <Icon name="download" class="w-5 h-5 mr-2" />
                        Request Data Export
                    </button>
                </div>
                
                <!-- Delete Account -->
                <div>
                    <h3 class="font-medium text-gray-900 mb-2">Delete Your Account</h3>
                    <p class="text-sm text-gray-600 mb-4">
                        Permanently delete your account and all associated data. This action cannot be undone.
                    </p>
                    <button
                        on:click={() => showDeletionModal = true}
                        class="btn btn-danger"
                    >
                        <Icon name="trash-2" class="w-5 h-5 mr-2" />
                        Delete Account
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Active Requests -->
        {#if activeRequests.length > 0}
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 class="text-xl font-semibold text-gray-900 mb-4">Active Requests</h2>
                
                <div class="space-y-3">
                    {#each activeRequests as request}
                        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                            <div>
                                <p class="font-medium text-gray-900">
                                    {request.type === 'export' ? 'Data Export' : 'Account Deletion'}
                                </p>
                                <p class="text-sm text-gray-600">
                                    Status: {request.status} • Requested: {new Date(request.requested_at).toLocaleDateString()}
                                </p>
                            </div>
                            {#if request.type === 'export' && request.status === 'completed'}
                                <button
                                    on:click={() => checkRequestStatus(request.id)}
                                    class="btn btn-sm btn-primary"
                                >
                                    Download
                                </button>
                            {:else}
                                <button
                                    on:click={() => checkRequestStatus(request.id)}
                                    class="btn btn-sm btn-secondary"
                                >
                                    Check Status
                                </button>
                            {/if}
                        </div>
                    {/each}
                </div>
            </div>
        {/if}
        
        <!-- Privacy Policy Link -->
        <div class="mt-8 text-center">
            <a href="/privacy" class="text-indigo-600 hover:text-indigo-700 font-medium">
                View our Privacy Policy →
            </a>
        </div>
    {/if}
</div>

<!-- Export Modal -->
{#if showExportModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Export Your Data</h3>
            
            <div class="mb-6">
                <p class="text-gray-600 mb-4">
                    Your data export will include:
                </p>
                <ul class="list-disc list-inside text-sm text-gray-600 space-y-1">
                    <li>Account information and settings</li>
                    <li>All trading records and analytics</li>
                    <li>Journal entries and notes</li>
                    <li>Support ticket history</li>
                    <li>Payment and subscription history</li>
                </ul>
                
                <div class="mt-4 p-3 bg-blue-50 rounded-md">
                    <p class="text-sm text-blue-800">
                        <Icon name="info" class="w-4 h-4 inline mr-1" />
                        The export will be available for download for 30 days.
                    </p>
                </div>
            </div>
            
            <div class="flex justify-end space-x-3">
                <button
                    on:click={() => showExportModal = false}
                    class="btn btn-secondary"
                >
                    Cancel
                </button>
                <button
                    on:click={requestDataExport}
                    class="btn btn-primary"
                >
                    Request Export
                </button>
            </div>
        </div>
    </div>
{/if}

<!-- Deletion Modal -->
{#if showDeletionModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Delete Your Account</h3>
            
            <div class="mb-6">
                <div class="p-3 bg-red-50 border border-red-200 rounded-md mb-4">
                    <p class="text-sm text-red-800">
                        <Icon name="alert-triangle" class="w-4 h-4 inline mr-1" />
                        <strong>Warning:</strong> This action is permanent and cannot be undone.
                    </p>
                </div>
                
                <p class="text-gray-600 mb-4">
                    Deleting your account will:
                </p>
                <ul class="list-disc list-inside text-sm text-gray-600 space-y-1 mb-4">
                    <li>Cancel any active subscriptions</li>
                    <li>Delete all your trading data</li>
                    <li>Remove all personal information</li>
                    <li>Delete your entire trading history</li>
                </ul>
                
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Confirm your password *
                        </label>
                        <input
                            type="password"
                            bind:value={deletionPassword}
                            class="form-input"
                            required
                        />
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Reason for leaving (optional)
                        </label>
                        <select bind:value={deletionReason} class="form-select">
                            <option value="">Select a reason</option>
                            <option value="not_using">Not using the service</option>
                            <option value="too_expensive">Too expensive</option>
                            <option value="missing_features">Missing features I need</option>
                            <option value="found_alternative">Found a better alternative</option>
                            <option value="privacy_concerns">Privacy concerns</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">
                            Additional feedback (optional)
                        </label>
                        <textarea
                            bind:value={deletionFeedback}
                            rows="3"
                            class="form-textarea"
                            placeholder="We'd appreciate any feedback to help us improve"
                        ></textarea>
                    </div>
                </div>
            </div>
            
            <div class="flex justify-end space-x-3">
                <button
                    on:click={() => {showDeletionModal = false; deletionPassword = '';}}
                    class="btn btn-secondary"
                >
                    Cancel
                </button>
                <button
                    on:click={requestAccountDeletion}
                    class="btn btn-danger"
                >
                    Delete My Account
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    .spinner {
        width: 2rem; height: 2rem; border-width: 4px; border-color: #c7d2fe; border-top-color: #4f46e5; border-radius: 9999px; animation: spin 1s linear infinite;
    }
    
    .form-input, .form-select, .form-textarea {
        @apply w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500;
    }
    
    .form-checkbox {
        @apply rounded border-gray-300 text-indigo-600 focus:ring-indigo-500;
    }
    
    .btn {
        padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 500; transition: background-color 0.2s, color 0.2s; display: inline-flex; align-items: center; justify-content: center;
    }
    
    .btn-primary {
        background-color: #4f46e5; color: white; @apply bg-indigo-600 text-white hover:bg-indigo-700;:hover { background-color: #4338ca; }
    }
    
    .btn-secondary {
        background-color: #e5e7eb; color: #1f2937; @apply bg-gray-200 text-gray-800 hover:bg-gray-300;:hover { background-color: #d1d5db; }
    }
    
    .btn-danger {
        background-color: #dc2626; color: white; @apply bg-red-600 text-white hover:bg-red-700;:hover { background-color: #b91c1c; }
    }
    
    .btn-sm {
        @apply px-3 py-1 text-sm;
    }
    
    .alert {
        padding: 1rem; border-radius: 0.375rem;
    }
    
    .alert-error {
        @apply bg-red-50 text-red-800 border border-red-200;
    }
    
    .alert-success {
        @apply bg-green-50 text-green-800 border border-green-200;
    }
</style>