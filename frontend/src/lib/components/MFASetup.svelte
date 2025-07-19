<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import Icon from '$lib/components/Icon.svelte';
    import QRCode from 'qrcode';
    
    export let user;
    export let onComplete = () => {};
    
    let mfaStatus = null;
    let activeTab = 'totp';
    let loading = false;
    let error = null;
    
    // TOTP Setup
    let qrCodeUrl = null;
    let manualKey = null;
    let totpCode = '';
    let backupCodes = [];
    
    // SMS Setup
    let phoneNumber = '';
    let smsCode = '';
    let smsSetupStarted = false;
    
    async function loadMFAStatus() {
        try {
            mfaStatus = await api.get('/mfa/status');
        } catch (err) {
            error = err.message || 'Failed to load MFA status';
        }
    }
    
    async function setupTOTP() {
        try {
            loading = true;
            error = null;
            
            const result = await api.post('/mfa/totp/setup', {});
            qrCodeUrl = result.qr_code;
            manualKey = result.manual_entry_key;
            
        } catch (err) {
            error = err.message || 'Failed to setup authenticator app';
        } finally {
            loading = false;
        }
    }
    
    async function verifyTOTP() {
        try {
            loading = true;
            error = null;
            
            const result = await api.post('/mfa/totp/verify', { code: totpCode });
            
            if (result.backup_codes) {
                backupCodes = result.backup_codes;
            }
            
            // Reload status
            await loadMFAStatus();
            
        } catch (err) {
            error = err.message || 'Invalid verification code';
        } finally {
            loading = false;
        }
    }
    
    async function setupSMS() {
        try {
            loading = true;
            error = null;
            
            const result = await api.post('/mfa/sms/setup', { phone_number: phoneNumber });
            smsSetupStarted = true;
            
        } catch (err) {
            error = err.message || 'Failed to send SMS';
        } finally {
            loading = false;
        }
    }
    
    async function verifySMS() {
        try {
            loading = true;
            error = null;
            
            await api.post('/mfa/sms/verify', { code: smsCode });
            
            // Reload status
            await loadMFAStatus();
            smsSetupStarted = false;
            
        } catch (err) {
            error = err.message || 'Invalid verification code';
        } finally {
            loading = false;
        }
    }
    
    async function regenerateBackupCodes() {
        if (!confirm('This will invalidate your existing backup codes. Continue?')) return;
        
        try {
            loading = true;
            error = null;
            
            const result = await api.post('/mfa/backup-codes/regenerate', {});
            backupCodes = result.backup_codes;
            
        } catch (err) {
            error = err.message || 'Failed to regenerate backup codes';
        } finally {
            loading = false;
        }
    }
    
    async function disableMFA() {
        const password = prompt('Enter your password to disable MFA:');
        if (!password) return;
        
        try {
            loading = true;
            error = null;
            
            await api.delete('/mfa/disable', { params: { password } });
            
            // Reload status
            await loadMFAStatus();
            
        } catch (err) {
            error = err.message || 'Failed to disable MFA';
        } finally {
            loading = false;
        }
    }
    
    function downloadBackupCodes() {
        const content = backupCodes.join('\n');
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'tradesense-backup-codes.txt';
        a.click();
        URL.revokeObjectURL(url);
    }
    
    onMount(() => {
        loadMFAStatus();
    });
</script>

<div class="max-w-4xl mx-auto p-6">
    <div class="bg-white rounded-lg shadow-sm border border-gray-200">
        <div class="p-6 border-b border-gray-200">
            <h2 class="text-2xl font-bold text-gray-900">Two-Factor Authentication</h2>
            <p class="mt-2 text-gray-600">
                Add an extra layer of security to your account
            </p>
        </div>
        
        {#if mfaStatus}
            {#if mfaStatus.mfa_enabled}
                <!-- MFA Enabled -->
                <div class="p-6">
                    <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                        <div class="flex items-center">
                            <Icon name="shield-check" class="w-6 h-6 text-green-600 mr-3" />
                            <div>
                                <h3 class="font-semibold text-green-900">MFA is enabled</h3>
                                <p class="text-sm text-green-700">
                                    Your account is protected with two-factor authentication
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Active Methods -->
                    <div class="mb-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-3">Active Methods</h3>
                        <div class="space-y-3">
                            {#each mfaStatus.devices as device}
                                {#if device.status === 'active'}
                                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                        <div class="flex items-center">
                                            <Icon 
                                                name={device.type === 'totp' ? 'smartphone' : device.type === 'sms' ? 'message-square' : 'key'} 
                                                class="w-5 h-5 text-gray-600 mr-3" 
                                            />
                                            <div>
                                                <p class="font-medium text-gray-900">{device.name}</p>
                                                <p class="text-sm text-gray-500">
                                                    Added {new Date(device.created_at).toLocaleDateString()}
                                                </p>
                                            </div>
                                        </div>
                                        {#if device.last_used_at}
                                            <span class="text-sm text-gray-500">
                                                Last used {new Date(device.last_used_at).toLocaleDateString()}
                                            </span>
                                        {/if}
                                    </div>
                                {/if}
                            {/each}
                        </div>
                    </div>
                    
                    <!-- Actions -->
                    <div class="flex space-x-3">
                        {#if !mfaStatus.methods.includes('sms')}
                            <button
                                on:click={() => activeTab = 'sms'}
                                class="btn btn-secondary"
                            >
                                Add Phone Number
                            </button>
                        {/if}
                        
                        <button
                            on:click={regenerateBackupCodes}
                            class="btn btn-secondary"
                        >
                            Regenerate Backup Codes
                        </button>
                        
                        <button
                            on:click={disableMFA}
                            class="btn btn-danger"
                        >
                            Disable MFA
                        </button>
                    </div>
                </div>
            {:else}
                <!-- MFA Setup -->
                <div class="p-6">
                    <!-- Tabs -->
                    <div class="border-b border-gray-200 mb-6">
                        <nav class="-mb-px flex space-x-8">
                            <button
                                on:click={() => activeTab = 'totp'}
                                class="py-2 px-1 border-b-2 font-medium text-sm"
                                class:border-indigo-500={activeTab === 'totp'}
                                class:text-indigo-600={activeTab === 'totp'}
                                class:border-transparent={activeTab !== 'totp'}
                                class:text-gray-500={activeTab !== 'totp'}
                            >
                                Authenticator App
                            </button>
                            <button
                                on:click={() => activeTab = 'sms'}
                                class="py-2 px-1 border-b-2 font-medium text-sm"
                                class:border-indigo-500={activeTab === 'sms'}
                                class:text-indigo-600={activeTab === 'sms'}
                                class:border-transparent={activeTab !== 'sms'}
                                class:text-gray-500={activeTab !== 'sms'}
                            >
                                SMS
                            </button>
                        </nav>
                    </div>
                    
                    {#if error}
                        <div class="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                            {error}
                        </div>
                    {/if}
                    
                    <!-- TOTP Setup -->
                    {#if activeTab === 'totp'}
                        <div>
                            {#if !qrCodeUrl}
                                <div class="text-center py-8">
                                    <Icon name="smartphone" class="w-16 h-16 text-gray-400 mx-auto mb-4" />
                                    <h3 class="text-lg font-semibold text-gray-900 mb-2">
                                        Set up Authenticator App
                                    </h3>
                                    <p class="text-gray-600 mb-6 max-w-md mx-auto">
                                        Use an authenticator app like Google Authenticator, Authy, or 1Password to generate time-based codes
                                    </p>
                                    <button
                                        on:click={setupTOTP}
                                        disabled={loading}
                                        class="btn btn-primary"
                                    >
                                        {#if loading}
                                            <span class="spinner mr-2"></span>
                                        {/if}
                                        Set Up Authenticator
                                    </button>
                                </div>
                            {:else if !backupCodes.length}
                                <div>
                                    <h3 class="text-lg font-semibold text-gray-900 mb-4">
                                        Scan QR Code
                                    </h3>
                                    
                                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <p class="text-sm text-gray-600 mb-4">
                                                Scan this QR code with your authenticator app:
                                            </p>
                                            <div class="bg-white p-4 border border-gray-200 rounded-lg inline-block">
                                                <img src={qrCodeUrl} alt="QR Code" class="w-48 h-48" />
                                            </div>
                                        </div>
                                        
                                        <div>
                                            <p class="text-sm text-gray-600 mb-2">
                                                Or enter this key manually:
                                            </p>
                                            <div class="bg-gray-50 p-3 rounded-lg font-mono text-sm break-all mb-4">
                                                {manualKey}
                                            </div>
                                            
                                            <div class="mt-6">
                                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                                    Enter verification code
                                                </label>
                                                <input
                                                    type="text"
                                                    bind:value={totpCode}
                                                    placeholder="000000"
                                                    maxlength="6"
                                                    class="form-input w-32 text-center text-lg"
                                                />
                                                <button
                                                    on:click={verifyTOTP}
                                                    disabled={loading || totpCode.length !== 6}
                                                    class="btn btn-primary ml-3"
                                                >
                                                    Verify
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            {:else}
                                <!-- Backup Codes -->
                                <div>
                                    <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                                        <div class="flex">
                                            <Icon name="alert-triangle" class="w-5 h-5 text-yellow-600 mr-3 flex-shrink-0 mt-0.5" />
                                            <div>
                                                <h3 class="font-semibold text-yellow-900">Save your backup codes</h3>
                                                <p class="text-sm text-yellow-700 mt-1">
                                                    Store these codes in a safe place. Each code can only be used once.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div class="bg-gray-50 p-4 rounded-lg mb-4">
                                        <div class="grid grid-cols-2 gap-2 font-mono text-sm">
                                            {#each backupCodes as code}
                                                <div class="p-2 bg-white rounded border border-gray-200">
                                                    {code}
                                                </div>
                                            {/each}
                                        </div>
                                    </div>
                                    
                                    <div class="flex space-x-3">
                                        <button
                                            on:click={downloadBackupCodes}
                                            class="btn btn-secondary"
                                        >
                                            <Icon name="download" class="w-4 h-4 mr-2" />
                                            Download Codes
                                        </button>
                                        <button
                                            on:click={() => { onComplete(); }}
                                            class="btn btn-primary"
                                        >
                                            Complete Setup
                                        </button>
                                    </div>
                                </div>
                            {/if}
                        </div>
                    {/if}
                    
                    <!-- SMS Setup -->
                    {#if activeTab === 'sms'}
                        <div>
                            {#if !smsSetupStarted}
                                <div class="max-w-md">
                                    <h3 class="text-lg font-semibold text-gray-900 mb-4">
                                        Add Phone Number
                                    </h3>
                                    <p class="text-sm text-gray-600 mb-4">
                                        We'll send verification codes to this number when you sign in
                                    </p>
                                    
                                    <div class="mb-4">
                                        <label class="block text-sm font-medium text-gray-700 mb-2">
                                            Phone Number
                                        </label>
                                        <input
                                            type="tel"
                                            bind:value={phoneNumber}
                                            placeholder="+1 (555) 123-4567"
                                            class="form-input"
                                        />
                                    </div>
                                    
                                    <button
                                        on:click={setupSMS}
                                        disabled={loading || !phoneNumber}
                                        class="btn btn-primary"
                                    >
                                        {#if loading}
                                            <span class="spinner mr-2"></span>
                                        {/if}
                                        Send Verification Code
                                    </button>
                                </div>
                            {:else}
                                <div class="max-w-md">
                                    <h3 class="text-lg font-semibold text-gray-900 mb-4">
                                        Enter Verification Code
                                    </h3>
                                    <p class="text-sm text-gray-600 mb-4">
                                        We sent a 6-digit code to {phoneNumber}
                                    </p>
                                    
                                    <div class="mb-4">
                                        <input
                                            type="text"
                                            bind:value={smsCode}
                                            placeholder="000000"
                                            maxlength="6"
                                            class="form-input w-32 text-center text-lg"
                                        />
                                    </div>
                                    
                                    <div class="flex space-x-3">
                                        <button
                                            on:click={verifySMS}
                                            disabled={loading || smsCode.length !== 6}
                                            class="btn btn-primary"
                                        >
                                            Verify
                                        </button>
                                        <button
                                            on:click={() => { smsSetupStarted = false; smsCode = ''; }}
                                            class="btn btn-secondary"
                                        >
                                            Change Number
                                        </button>
                                    </div>
                                </div>
                            {/if}
                        </div>
                    {/if}
                </div>
            {/if}
        {:else}
            <div class="p-12 text-center">
                <div class="spinner mx-auto"></div>
            </div>
        {/if}
    </div>
</div>

<style>
    .form-input {
        @apply block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500;
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
    
    .btn:disabled {
        @apply opacity-50 cursor-not-allowed;
    }
    
    .spinner {
        @apply w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin;
    }
</style>