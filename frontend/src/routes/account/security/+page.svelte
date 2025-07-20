<script>
    import { onMount } from 'svelte';
    import { page } from '$app/stores';
    import { goto } from '$app/navigation';
    import MFASetup from '$lib/components/MFASetup.svelte';
    import Icon from '$lib/components/Icon.svelte';
    import { api } from '$lib/api/client-safe';
    
    let user = null;
    let trustedDevices = [];
    let loading = true;
    let error = null;
    
    async function loadSecurityData() {
        try {
            loading = true;
            error = null;
            
            // Get user data
            user = await api.get('/auth/me');
            
            // Get trusted devices
            const devicesData = await api.get('/mfa/trusted-devices');
            trustedDevices = devicesData.trusted_devices || [];
            
        } catch (err) {
            error = err.message || 'Failed to load security settings';
        } finally {
            loading = false;
        }
    }
    
    async function removeTrustedDevice(deviceId) {
        if (!confirm('Remove this trusted device?')) return;
        
        try {
            await api.delete(`/mfa/trusted-devices/${deviceId}`);
            await loadSecurityData();
        } catch (err) {
            alert(err.message || 'Failed to remove device');
        }
    }
    
    function handleMFAComplete() {
        // Reload data after MFA setup
        loadSecurityData();
    }
    
    onMount(() => {
        loadSecurityData();
    });
</script>

<svelte:head>
    <title>Security Settings - TradeSense</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
        <div class="flex items-center mb-4">
            <button
                on:click={() => goto('/account')}
                class="text-gray-500 hover:text-gray-700 mr-3"
            >
                <Icon name="arrow-left" class="w-5 h-5" />
            </button>
            <h1 class="text-3xl font-bold text-gray-900">Security Settings</h1>
        </div>
        <p class="text-gray-600">
            Manage your account security and authentication settings
        </p>
    </div>
    
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="spinner"></div>
        </div>
    {:else if error}
        <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
        </div>
    {:else if user}
        <div class="space-y-6">
            <!-- Two-Factor Authentication -->
            <MFASetup {user} onComplete={handleMFAComplete} />
            
            <!-- Trusted Devices -->
            {#if trustedDevices.length > 0}
                <div class="bg-white rounded-lg shadow-sm border border-gray-200">
                    <div class="p-6 border-b border-gray-200">
                        <h2 class="text-xl font-bold text-gray-900">Trusted Devices</h2>
                        <p class="mt-2 text-gray-600">
                            These devices won't require MFA for 30 days
                        </p>
                    </div>
                    
                    <div class="p-6">
                        <div class="space-y-3">
                            {#each trustedDevices as device}
                                <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                                    <div>
                                        <p class="font-medium text-gray-900">
                                            {device.name}
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Added {new Date(device.created_at).toLocaleDateString()}
                                            • Last used {new Date(device.last_used_at).toLocaleDateString()}
                                            • From {device.last_ip}
                                        </p>
                                        <p class="text-xs text-gray-500 mt-1">
                                            Expires {new Date(device.expires_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <button
                                        on:click={() => removeTrustedDevice(device.id)}
                                        class="text-red-600 hover:text-red-700"
                                        title="Remove device"
                                    >
                                        <Icon name="trash-2" class="w-5 h-5" />
                                    </button>
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>
            {/if}
            
            <!-- Password Change -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200">
                <div class="p-6 border-b border-gray-200">
                    <h2 class="text-xl font-bold text-gray-900">Password</h2>
                    <p class="mt-2 text-gray-600">
                        Change your account password
                    </p>
                </div>
                
                <div class="p-6">
                    <button
                        on:click={() => goto('/account/change-password')}
                        class="btn btn-secondary"
                    >
                        Change Password
                    </button>
                </div>
            </div>
            
            <!-- Security Recommendations -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <div class="flex">
                    <Icon name="shield" class="w-6 h-6 text-blue-600 mr-3 flex-shrink-0" />
                    <div>
                        <h3 class="font-semibold text-blue-900 mb-2">Security Recommendations</h3>
                        <ul class="space-y-1 text-sm text-blue-800">
                            <li class="flex items-start">
                                <Icon name="check" class="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                                Use a unique, strong password for your TradeSense account
                            </li>
                            <li class="flex items-start">
                                <Icon name="check" class="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                                Enable two-factor authentication for maximum security
                            </li>
                            <li class="flex items-start">
                                <Icon name="check" class="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                                Regularly review and remove unused trusted devices
                            </li>
                            <li class="flex items-start">
                                <Icon name="check" class="w-4 h-4 mr-2 mt-0.5 flex-shrink-0" />
                                Keep your authenticator app backed up or save your backup codes
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .spinner {
        width: 2rem;
        height: 2rem;
        border-width: 4px;
        border-color: #c7d2fe;
        border-top-color: #4f46e5;
        border-radius: 9999px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .btn {
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: background-color 0.2s, color 0.2s;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }
    
    .btn-secondary {
        background-color: #e5e7eb;
        color: #1f2937;
    }
    
    .btn-secondary:hover {
        background-color: #d1d5db;
    }
</style>