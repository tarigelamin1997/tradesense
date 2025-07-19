<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import Icon from '$lib/components/Icon.svelte';
    
    export let sessionId;
    export let methods = [];
    export let onSuccess = () => {};
    export let onCancel = () => {};
    
    let selectedMethod = methods[0] || 'totp';
    let verificationCode = '';
    let trustDevice = false;
    let deviceName = '';
    let loading = false;
    let error = null;
    let codeSent = false;
    
    async function sendChallenge(method) {
        try {
            loading = true;
            error = null;
            
            const result = await api.post('/mfa/challenge', {
                method: method,
                session_id: sessionId
            });
            
            if (method === 'sms' || method === 'email') {
                codeSent = true;
            }
            
        } catch (err) {
            error = err.message || 'Failed to send verification code';
        } finally {
            loading = false;
        }
    }
    
    async function verifyCode() {
        try {
            loading = true;
            error = null;
            
            const result = await api.post('/mfa/verify', {
                method: selectedMethod,
                code: verificationCode,
                trust_device: trustDevice,
                device_name: trustDevice ? (deviceName || navigator.userAgent) : null,
                session_id: sessionId
            });
            
            if (result.success) {
                // Store trust token if device was trusted
                if (result.trust_token) {
                    localStorage.setItem('mfa_trust_token', result.trust_token);
                }
                
                // Call success callback with auth data
                onSuccess({
                    access_token: result.access_token,
                    token_type: result.token_type
                });
            }
            
        } catch (err) {
            error = err.message || 'Invalid verification code';
            verificationCode = '';
        } finally {
            loading = false;
        }
    }
    
    function selectMethod(method) {
        selectedMethod = method;
        verificationCode = '';
        codeSent = false;
        error = null;
        
        // Auto-send challenge for SMS/Email
        if (method === 'sms' || method === 'email') {
            sendChallenge(method);
        }
    }
    
    function handleKeydown(event) {
        if (event.key === 'Enter' && verificationCode.length >= 6) {
            verifyCode();
        }
    }
    
    onMount(() => {
        // Auto-send challenge for SMS/Email if it's the default method
        if (selectedMethod === 'sms' || selectedMethod === 'email') {
            sendChallenge(selectedMethod);
        }
    });
</script>

<div class="max-w-md mx-auto p-6">
    <div class="bg-white rounded-lg shadow-lg border border-gray-200">
        <div class="p-6 border-b border-gray-200">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-2xl font-bold text-gray-900">Two-Factor Authentication</h2>
                <button
                    on:click={onCancel}
                    class="text-gray-500 hover:text-gray-700"
                >
                    <Icon name="x" class="w-5 h-5" />
                </button>
            </div>
            <p class="text-gray-600">
                Enter your verification code to complete sign in
            </p>
        </div>
        
        <div class="p-6">
            <!-- Method Selection -->
            {#if methods.length > 1}
                <div class="mb-6">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Verification Method
                    </label>
                    <div class="grid grid-cols-1 gap-2">
                        {#each methods as method}
                            <button
                                on:click={() => selectMethod(method)}
                                class="p-3 border rounded-lg text-left transition-colors"
                                class:border-indigo-500={selectedMethod === method}
                                class:bg-indigo-50={selectedMethod === method}
                                class:border-gray-200={selectedMethod !== method}
                            >
                                <div class="flex items-center">
                                    <Icon 
                                        name={
                                            method === 'totp' ? 'smartphone' : 
                                            method === 'sms' ? 'message-square' : 
                                            method === 'email' ? 'mail' : 
                                            'key'
                                        } 
                                        class="w-5 h-5 mr-3 text-gray-600" 
                                    />
                                    <span class="font-medium">
                                        {method === 'totp' ? 'Authenticator App' :
                                         method === 'sms' ? 'Text Message' :
                                         method === 'email' ? 'Email' :
                                         'Backup Code'}
                                    </span>
                                </div>
                            </button>
                        {/each}
                    </div>
                </div>
            {/if}
            
            {#if error}
                <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                </div>
            {/if}
            
            <!-- Code Input -->
            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    {selectedMethod === 'backup_codes' ? 'Backup Code' : 'Verification Code'}
                </label>
                
                {#if selectedMethod === 'sms' && !codeSent}
                    <p class="text-sm text-gray-600 mb-3">
                        Sending code to your phone...
                    </p>
                {:else if selectedMethod === 'email' && !codeSent}
                    <p class="text-sm text-gray-600 mb-3">
                        Sending code to your email...
                    </p>
                {/if}
                
                <input
                    type="text"
                    bind:value={verificationCode}
                    on:keydown={handleKeydown}
                    placeholder={selectedMethod === 'backup_codes' ? 'XXXX-XXXX' : '000000'}
                    maxlength={selectedMethod === 'backup_codes' ? 9 : 6}
                    class="form-input text-center text-lg font-mono"
                    autocomplete="off"
                />
                
                {#if selectedMethod === 'totp'}
                    <p class="text-xs text-gray-500 mt-2">
                        Enter the 6-digit code from your authenticator app
                    </p>
                {:else if selectedMethod === 'backup_codes'}
                    <p class="text-xs text-gray-500 mt-2">
                        Enter one of your backup recovery codes
                    </p>
                {/if}
            </div>
            
            <!-- Trust Device Option -->
            <div class="mb-6">
                <label class="flex items-center">
                    <input
                        type="checkbox"
                        bind:checked={trustDevice}
                        class="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 mr-2"
                    />
                    <span class="text-sm text-gray-700">
                        Trust this device for 30 days
                    </span>
                </label>
                
                {#if trustDevice}
                    <input
                        type="text"
                        bind:value={deviceName}
                        placeholder="Device name (optional)"
                        class="form-input mt-2 text-sm"
                    />
                {/if}
            </div>
            
            <!-- Actions -->
            <div class="flex space-x-3">
                <button
                    on:click={verifyCode}
                    disabled={loading || verificationCode.length < 6}
                    class="btn btn-primary flex-1"
                >
                    {#if loading}
                        <span class="spinner mr-2"></span>
                    {/if}
                    Verify
                </button>
                
                {#if (selectedMethod === 'sms' || selectedMethod === 'email') && codeSent}
                    <button
                        on:click={() => sendChallenge(selectedMethod)}
                        disabled={loading}
                        class="btn btn-secondary"
                    >
                        Resend Code
                    </button>
                {/if}
            </div>
            
            <!-- Help Text -->
            <div class="mt-6 text-center">
                <p class="text-sm text-gray-600">
                    Having trouble?
                    {#if methods.includes('backup_codes')}
                        Try using a <button
                            on:click={() => selectMethod('backup_codes')}
                            class="text-indigo-600 hover:text-indigo-700 font-medium"
                        >
                            backup code
                        </button>
                    {:else}
                        Contact support for help
                    {/if}
                </p>
            </div>
        </div>
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
    
    .btn:disabled {
        @apply opacity-50 cursor-not-allowed;
    }
    
    .spinner {
        @apply w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin;
    }
</style>