<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { api } from '$lib/api';
    import { authStore } from '$lib/stores/auth';
    import Icon from '$lib/components/Icon.svelte';
    import analytics from '$lib/analytics';
    
    let user = null;
    let currentPlan = null;
    let plans = [];
    let usage = null;
    let loading = true;
    let error = null;
    let showCancelModal = false;
    let cancelReason = '';
    let cancelFeedback = '';
    
    authStore.subscribe(value => {
        user = value.user;
    });
    
    async function loadSubscriptionData() {
        try {
            loading = true;
            error = null;
            
            const [plansData, currentData, usageData] = await Promise.all([
                api.get('/subscription/plans'),
                api.get('/subscription/current'),
                api.get('/subscription/usage')
            ]);
            
            plans = plansData.plans;
            currentPlan = currentData;
            usage = usageData;
            
            analytics.trackPageView('/subscription');
            
        } catch (err) {
            error = err.message || 'Failed to load subscription data';
        } finally {
            loading = false;
        }
    }
    
    async function selectPlan(planId) {
        if (planId === currentPlan.plan) return;
        
        try {
            if (planId === 'free') {
                // Downgrade to free
                showCancelModal = true;
            } else if (currentPlan.plan === 'free') {
                // Upgrade from free - go to checkout
                const response = await api.post('/subscription/checkout', {
                    plan: planId,
                    success_url: `${window.location.origin}/subscription/success`,
                    cancel_url: `${window.location.origin}/subscription`
                });
                
                analytics.trackAction('start_checkout', 'subscription', { plan: planId });
                
                // Redirect to Stripe checkout
                window.location.href = response.checkout_url;
            } else {
                // Change between paid plans
                const response = await api.post('/subscription/change-plan', {
                    new_plan: planId
                });
                
                if (response.success) {
                    analytics.trackSubscription(
                        response.new_plan > currentPlan.plan ? 'upgraded' : 'downgraded',
                        planId,
                        plans.find(p => p.id === planId).price
                    );
                    
                    await loadSubscriptionData();
                }
            }
        } catch (err) {
            error = err.message || 'Failed to change plan';
        }
    }
    
    async function cancelSubscription() {
        try {
            await api.post('/subscription/cancel', {
                reason: cancelReason,
                feedback: cancelFeedback
            });
            
            analytics.trackSubscription('cancelled', 'free', 0);
            
            showCancelModal = false;
            await loadSubscriptionData();
            
        } catch (err) {
            error = err.message || 'Failed to cancel subscription';
        }
    }
    
    async function reactivateSubscription() {
        try {
            await api.post('/subscription/reactivate');
            
            analytics.trackAction('reactivate_subscription', 'subscription');
            
            await loadSubscriptionData();
            
        } catch (err) {
            error = err.message || 'Failed to reactivate subscription';
        }
    }
    
    async function openCustomerPortal() {
        try {
            const response = await api.post('/subscription/customer-portal', {
                return_url: window.location.href
            });
            
            analytics.trackAction('open_customer_portal', 'subscription');
            
            window.location.href = response.portal_url;
            
        } catch (err) {
            error = err.message || 'Failed to open customer portal';
        }
    }
    
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }
    
    function formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    
    function getUsageColor(percentage) {
        if (percentage >= 90) return 'text-red-600 bg-red-100';
        if (percentage >= 75) return 'text-yellow-600 bg-yellow-100';
        return 'text-green-600 bg-green-100';
    }
    
    onMount(() => {
        loadSubscriptionData();
    });
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    {#if loading}
        <div class="flex justify-center py-12">
            <div class="spinner"></div>
        </div>
    {:else if error}
        <div class="alert alert-error mb-6">{error}</div>
    {:else}
        <!-- Current Plan Section -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
            <h2 class="text-2xl font-bold text-gray-900 mb-4">Current Subscription</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <p class="text-sm text-gray-600">Plan</p>
                    <p class="text-xl font-semibold text-gray-900 capitalize">{currentPlan.plan}</p>
                    
                    <p class="text-sm text-gray-600 mt-4">Status</p>
                    <div class="flex items-center mt-1">
                        <span class="w-2 h-2 rounded-full mr-2 
                                   {currentPlan.status === 'active' ? 'bg-green-400' : 
                                    currentPlan.status === 'past_due' ? 'bg-yellow-400' : 
                                    'bg-gray-400'}"></span>
                        <span class="text-lg capitalize">{currentPlan.status}</span>
                    </div>
                    
                    {#if currentPlan.current_period_end}
                        <p class="text-sm text-gray-600 mt-4">Next billing date</p>
                        <p class="text-lg">{formatDate(currentPlan.current_period_end)}</p>
                    {/if}
                    
                    {#if currentPlan.cancel_at_period_end}
                        <div class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                            <p class="text-sm text-yellow-800">
                                Your subscription will end on {formatDate(currentPlan.current_period_end)}
                            </p>
                            <button
                                on:click={reactivateSubscription}
                                class="text-sm font-medium text-yellow-800 hover:text-yellow-900 mt-1"
                            >
                                Reactivate subscription
                            </button>
                        </div>
                    {/if}
                </div>
                
                <div>
                    <p class="text-sm text-gray-600">Features</p>
                    <ul class="mt-2 space-y-2">
                        {#each currentPlan.features as feature}
                            <li class="flex items-start">
                                <Icon name="check" class="w-5 h-5 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                                <span class="text-sm text-gray-700">{feature}</span>
                            </li>
                        {/each}
                    </ul>
                    
                    {#if currentPlan.plan !== 'free'}
                        <button
                            on:click={openCustomerPortal}
                            class="mt-4 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                        >
                            Manage billing & payment methods →
                        </button>
                    {/if}
                </div>
            </div>
        </div>
        
        <!-- Usage Section -->
        {#if usage}
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Current Usage</h3>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Trades Usage -->
                    <div>
                        <div class="flex justify-between items-baseline mb-2">
                            <span class="text-sm font-medium text-gray-700">Trades This Month</span>
                            <span class="text-sm text-gray-600">
                                {usage.usage.trades.unlimited ? 'Unlimited' : `${usage.usage.trades.current} / ${usage.usage.trades.limit}`}
                            </span>
                        </div>
                        {#if !usage.usage.trades.unlimited}
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                    class="h-2 rounded-full transition-all duration-300
                                           {usage.usage.trades.percentage >= 90 ? 'bg-red-500' :
                                            usage.usage.trades.percentage >= 75 ? 'bg-yellow-500' :
                                            'bg-green-500'}"
                                    style="width: {Math.min(usage.usage.trades.percentage, 100)}%"
                                ></div>
                            </div>
                        {:else}
                            <div class="text-xs text-gray-500">No limits on {currentPlan.plan} plan</div>
                        {/if}
                    </div>
                    
                    <!-- API Usage -->
                    <div>
                        <div class="flex justify-between items-baseline mb-2">
                            <span class="text-sm font-medium text-gray-700">API Calls Today</span>
                            <span class="text-sm text-gray-600">
                                {usage.usage.api_calls.unlimited ? 'Unlimited' : `${usage.usage.api_calls.current} / ${usage.usage.api_calls.limit}`}
                            </span>
                        </div>
                        {#if !usage.usage.api_calls.unlimited}
                            <div class="w-full bg-gray-200 rounded-full h-2">
                                <div 
                                    class="h-2 rounded-full transition-all duration-300
                                           {usage.usage.api_calls.percentage >= 90 ? 'bg-red-500' :
                                            usage.usage.api_calls.percentage >= 75 ? 'bg-yellow-500' :
                                            'bg-green-500'}"
                                    style="width: {Math.min(usage.usage.api_calls.percentage, 100)}%"
                                ></div>
                            </div>
                        {:else}
                            <div class="text-xs text-gray-500">No limits on {currentPlan.plan} plan</div>
                        {/if}
                    </div>
                </div>
            </div>
        {/if}
        
        <!-- Plans Section -->
        <div>
            <h3 class="text-xl font-bold text-gray-900 mb-6">Available Plans</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                {#each plans as plan}
                    <div class="bg-white rounded-lg shadow-sm border-2 transition-all
                                {plan.id === currentPlan.plan ? 'border-indigo-500' : 'border-gray-200'}
                                {plan.popular ? 'transform scale-105' : ''}">
                        {#if plan.popular}
                            <div class="bg-indigo-500 text-white text-sm font-medium text-center py-2 rounded-t-md">
                                Most Popular
                            </div>
                        {/if}
                        
                        <div class="p-6">
                            <h4 class="text-xl font-bold text-gray-900">{plan.name}</h4>
                            <div class="mt-4 flex items-baseline">
                                <span class="text-4xl font-extrabold text-gray-900">
                                    {formatCurrency(plan.price)}
                                </span>
                                <span class="ml-1 text-gray-500">/month</span>
                            </div>
                            
                            <ul class="mt-6 space-y-3">
                                {#each plan.features as feature}
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                                        <span class="text-sm text-gray-700">{feature}</span>
                                    </li>
                                {/each}
                            </ul>
                            
                            <button
                                on:click={() => selectPlan(plan.id)}
                                disabled={plan.id === currentPlan.plan}
                                class="mt-8 w-full py-2 px-4 rounded-md font-medium transition-colors
                                       {plan.id === currentPlan.plan ? 
                                        'bg-gray-100 text-gray-400 cursor-not-allowed' :
                                        plan.popular ? 
                                        'bg-indigo-600 text-white hover:bg-indigo-700' :
                                        'bg-gray-800 text-white hover:bg-gray-900'}"
                            >
                                {plan.id === currentPlan.plan ? 'Current Plan' : 
                                 plan.price > (plans.find(p => p.id === currentPlan.plan)?.price || 0) ? 'Upgrade' : 
                                 plan.price === 0 ? 'Downgrade' : 'Switch Plan'}
                            </button>
                        </div>
                    </div>
                {/each}
            </div>
        </div>
    {/if}
</div>

<!-- Cancel Subscription Modal -->
{#if showCancelModal}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Cancel Subscription</h3>
            
            <p class="text-gray-600 mb-4">
                We're sorry to see you go. Your subscription will remain active until the end of your current billing period.
            </p>
            
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Reason for cancelling (optional)
                    </label>
                    <select bind:value={cancelReason} class="form-select">
                        <option value="">Select a reason</option>
                        <option value="too_expensive">Too expensive</option>
                        <option value="not_using">Not using enough</option>
                        <option value="missing_features">Missing features</option>
                        <option value="found_alternative">Found alternative</option>
                        <option value="other">Other</option>
                    </select>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">
                        Additional feedback (optional)
                    </label>
                    <textarea
                        bind:value={cancelFeedback}
                        rows="3"
                        class="form-textarea"
                        placeholder="Let us know how we can improve..."
                    ></textarea>
                </div>
            </div>
            
            <div class="mt-6 flex justify-end space-x-3">
                <button
                    on:click={() => showCancelModal = false}
                    class="btn btn-secondary"
                >
                    Keep Subscription
                </button>
                <button
                    on:click={cancelSubscription}
                    class="btn btn-danger"
                >
                    Cancel Subscription
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    .spinner {
        width: 2rem; height: 2rem; border-width: 4px; border-color: #c7d2fe; border-top-color: #4f46e5; border-radius: 9999px; animation: spin 1s linear infinite;
    }
    
    .form-select, .form-textarea {
        width: 100%;
        border-radius: 0.375rem;
        border-color: #d1d5db;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    .form-select:focus, .form-textarea:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    .btn {
        padding: 0.5rem 1rem;
        border-radius: 0.375rem;
        font-weight: 500;
        transition: background-color 0.15s ease-in-out, color 0.15s ease-in-out;
    }
    
    .btn-secondary {
        background-color: #e5e7eb;
        color: #1f2937;
    }
    
    .btn-secondary:hover {
        background-color: #d1d5db;
    }
    
    .btn-danger {
        background-color: #dc2626;
        color: white;
    }
    
    .btn-danger:hover {
        background-color: #b91c1c;
    }
</style>