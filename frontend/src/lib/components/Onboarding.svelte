<script>
    import { onMount, createEventDispatcher } from 'svelte';
    import { fade, fly, scale } from 'svelte/transition';
    import { api } from '$lib/api';
    import Icon from '$lib/components/Icon.svelte';
    import analytics from '$lib/analytics';
    
    export let user = null;
    export let visible = true;
    
    const dispatch = createEventDispatcher();
    
    let state = null;
    let loading = true;
    let error = null;
    let currentStepIndex = 0;
    let animating = false;
    
    // Step components
    let stepComponents = {
        welcome: WelcomeStep,
        profile_setup: ProfileStep,
        trading_preferences: PreferencesStep,
        first_trade: FirstTradeStep,
        analytics_tour: AnalyticsTourStep,
        plan_selection: PlanSelectionStep
    };
    
    // Profile form data
    let profileData = {
        full_name: user?.full_name || '',
        trading_experience: '',
        trading_goals: '',
        preferred_markets: [],
        risk_tolerance: 'medium'
    };
    
    // Preferences form data
    let preferencesData = {
        default_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        currency: 'USD',
        notification_preferences: {
            email_daily_summary: true,
            email_weekly_report: true,
            email_trade_alerts: false
        },
        display_preferences: {
            theme: 'light',
            compact_view: false
        }
    };
    
    async function loadOnboardingState() {
        try {
            loading = true;
            error = null;
            
            const response = await api.get('/onboarding/state');
            state = response;
            
            // Find current step index
            const steps = ['welcome', 'profile_setup', 'trading_preferences', 'first_trade', 'analytics_tour', 'plan_selection'];
            currentStepIndex = steps.indexOf(state.current_step) || 0;
            
            analytics.trackPageView('/onboarding');
            
        } catch (err) {
            error = err.message || 'Failed to load onboarding state';
        } finally {
            loading = false;
        }
    }
    
    async function completeStep(stepId, stepData = null) {
        try {
            animating = true;
            
            const response = await api.post('/onboarding/complete-step', {
                step: stepId,
                data: stepData
            });
            
            if (response.success) {
                analytics.trackAction('complete_onboarding_step', 'onboarding', { step: stepId });
                
                if (response.is_completed) {
                    // Onboarding completed
                    dispatch('completed');
                    visible = false;
                } else {
                    // Move to next step
                    await loadOnboardingState();
                    currentStepIndex++;
                }
            }
            
        } catch (err) {
            error = err.message || 'Failed to complete step';
        } finally {
            animating = false;
        }
    }
    
    async function skipStep(stepId, reason = null) {
        try {
            const response = await api.post('/onboarding/skip-step', {
                step: stepId,
                reason
            });
            
            if (response.success) {
                analytics.trackAction('skip_onboarding_step', 'onboarding', { step: stepId, reason });
                await loadOnboardingState();
                currentStepIndex++;
            }
            
        } catch (err) {
            error = err.message || 'Failed to skip step';
        }
    }
    
    async function dismissOnboarding() {
        if (!confirm('Are you sure you want to skip the setup process? You can always access these features later from settings.')) {
            return;
        }
        
        try {
            await api.post('/onboarding/dismiss', { reason: 'user_dismissed' });
            
            analytics.trackAction('dismiss_onboarding', 'onboarding');
            
            dispatch('dismissed');
            visible = false;
            
        } catch (err) {
            error = err.message || 'Failed to dismiss onboarding';
        }
    }
    
    // Step-specific handlers
    async function completeProfile() {
        const response = await api.post('/onboarding/profile', profileData);
        if (response.success) {
            await completeStep('profile_setup', profileData);
        }
    }
    
    async function completePreferences() {
        const response = await api.post('/onboarding/preferences', preferencesData);
        if (response.success) {
            await completeStep('trading_preferences', preferencesData);
        }
    }
    
    async function completeFirstTrade() {
        await completeStep('first_trade', { import_method: 'completed' });
    }
    
    async function completeAnalyticsTour() {
        await completeStep('analytics_tour', { tour_completed: true });
    }
    
    async function completePlanSelection(selectedPlan) {
        await completeStep('plan_selection', { selected_plan: selectedPlan });
    }
    
    onMount(() => {
        if (visible) {
            loadOnboardingState();
        }
    });
</script>

{#if visible && !loading && state}
    <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" transition:fade>
        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden" 
             transition:scale={{ duration: 300 }}>
            
            <!-- Header -->
            <div class="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-6">
                <div class="flex justify-between items-start">
                    <div>
                        <h2 class="text-2xl font-bold">Welcome to TradeSense!</h2>
                        <p class="mt-2 text-indigo-100">Let's get you set up in just a few steps</p>
                    </div>
                    <button
                        on:click={dismissOnboarding}
                        class="text-white/80 hover:text-white"
                        title="Skip setup"
                    >
                        <Icon name="x" class="w-6 h-6" />
                    </button>
                </div>
                
                <!-- Progress bar -->
                <div class="mt-6">
                    <div class="flex justify-between text-xs text-indigo-200 mb-2">
                        <span>Step {currentStepIndex + 1} of 6</span>
                        <span>{state.progress_percentage}% Complete</span>
                    </div>
                    <div class="w-full bg-white/20 rounded-full h-2">
                        <div 
                            class="bg-white rounded-full h-2 transition-all duration-500"
                            style="width: {state.progress_percentage}%"
                        ></div>
                    </div>
                </div>
            </div>
            
            <!-- Content -->
            <div class="p-6" style="max-height: calc(90vh - 200px); overflow-y: auto;">
                {#if error}
                    <div class="alert alert-error mb-4">{error}</div>
                {/if}
                
                {#if state.current_step === 'welcome'}
                    <div class="text-center py-8" in:fly={{ x: 50, duration: 300 }}>
                        <Icon name="rocket" class="w-16 h-16 text-indigo-600 mx-auto mb-4" />
                        <h3 class="text-2xl font-bold text-gray-900 mb-4">Welcome aboard!</h3>
                        <p class="text-gray-600 mb-8 max-w-md mx-auto">
                            TradeSense helps you track, analyze, and improve your trading performance. 
                            Let's set up your account to get the most out of our platform.
                        </p>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                            <div class="text-center">
                                <Icon name="upload" class="w-12 h-12 text-indigo-500 mx-auto mb-2" />
                                <h4 class="font-medium text-gray-900">Import Trades</h4>
                                <p class="text-sm text-gray-600">CSV, API, or manual entry</p>
                            </div>
                            <div class="text-center">
                                <Icon name="bar-chart-2" class="w-12 h-12 text-indigo-500 mx-auto mb-2" />
                                <h4 class="font-medium text-gray-900">Analyze Performance</h4>
                                <p class="text-sm text-gray-600">Advanced analytics & insights</p>
                            </div>
                            <div class="text-center">
                                <Icon name="trending-up" class="w-12 h-12 text-indigo-500 mx-auto mb-2" />
                                <h4 class="font-medium text-gray-900">Improve Trading</h4>
                                <p class="text-sm text-gray-600">Data-driven decisions</p>
                            </div>
                        </div>
                        
                        <button
                            on:click={() => completeStep('welcome')}
                            class="btn btn-primary btn-lg"
                            disabled={animating}
                        >
                            Get Started
                            <Icon name="arrow-right" class="w-5 h-5 ml-2" />
                        </button>
                    </div>
                    
                {:else if state.current_step === 'profile_setup'}
                    <div in:fly={{ x: 50, duration: 300 }}>
                        <h3 class="text-xl font-bold text-gray-900 mb-4">Complete Your Profile</h3>
                        <p class="text-gray-600 mb-6">Tell us a bit about yourself and your trading experience</p>
                        
                        <form on:submit|preventDefault={completeProfile} class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">
                                    Full Name
                                </label>
                                <input
                                    type="text"
                                    bind:value={profileData.full_name}
                                    class="form-input"
                                    required
                                />
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">
                                    Trading Experience
                                </label>
                                <select bind:value={profileData.trading_experience} class="form-select" required>
                                    <option value="">Select experience level</option>
                                    <option value="beginner">Beginner (< 1 year)</option>
                                    <option value="intermediate">Intermediate (1-3 years)</option>
                                    <option value="experienced">Experienced (3-5 years)</option>
                                    <option value="professional">Professional (5+ years)</option>
                                </select>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">
                                    Trading Goals
                                </label>
                                <textarea
                                    bind:value={profileData.trading_goals}
                                    rows="3"
                                    class="form-textarea"
                                    placeholder="What do you hope to achieve with TradeSense?"
                                ></textarea>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">
                                    Preferred Markets (select all that apply)
                                </label>
                                <div class="space-y-2">
                                    {#each ['Stocks', 'Options', 'Futures', 'Forex', 'Crypto'] as market}
                                        <label class="flex items-center">
                                            <input
                                                type="checkbox"
                                                value={market.toLowerCase()}
                                                on:change={(e) => {
                                                    if (e.target.checked) {
                                                        profileData.preferred_markets = [...profileData.preferred_markets, e.target.value];
                                                    } else {
                                                        profileData.preferred_markets = profileData.preferred_markets.filter(m => m !== e.target.value);
                                                    }
                                                }}
                                                class="form-checkbox"
                                            />
                                            <span class="ml-2">{market}</span>
                                        </label>
                                    {/each}
                                </div>
                            </div>
                            
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">
                                    Risk Tolerance
                                </label>
                                <select bind:value={profileData.risk_tolerance} class="form-select">
                                    <option value="conservative">Conservative</option>
                                    <option value="moderate">Moderate</option>
                                    <option value="aggressive">Aggressive</option>
                                </select>
                            </div>
                            
                            <div class="flex justify-between pt-4">
                                <button
                                    type="button"
                                    on:click={() => skipStep('profile_setup', 'later')}
                                    class="btn btn-secondary"
                                    disabled={animating}
                                >
                                    Skip for now
                                </button>
                                <button
                                    type="submit"
                                    class="btn btn-primary"
                                    disabled={animating}
                                >
                                    Continue
                                    <Icon name="arrow-right" class="w-5 h-5 ml-2" />
                                </button>
                            </div>
                        </form>
                    </div>
                    
                {:else if state.current_step === 'trading_preferences'}
                    <div in:fly={{ x: 50, duration: 300 }}>
                        <h3 class="text-xl font-bold text-gray-900 mb-4">Trading Preferences</h3>
                        <p class="text-gray-600 mb-6">Customize TradeSense to match your workflow</p>
                        
                        <form on:submit|preventDefault={completePreferences} class="space-y-4">
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">
                                        Default Timezone
                                    </label>
                                    <select bind:value={preferencesData.default_timezone} class="form-select">
                                        <option value="America/New_York">Eastern Time</option>
                                        <option value="America/Chicago">Central Time</option>
                                        <option value="America/Denver">Mountain Time</option>
                                        <option value="America/Los_Angeles">Pacific Time</option>
                                        <option value="Europe/London">London</option>
                                        <option value="Asia/Tokyo">Tokyo</option>
                                    </select>
                                </div>
                                
                                <div>
                                    <label class="block text-sm font-medium text-gray-700 mb-1">
                                        Currency
                                    </label>
                                    <select bind:value={preferencesData.currency} class="form-select">
                                        <option value="USD">USD ($)</option>
                                        <option value="EUR">EUR (€)</option>
                                        <option value="GBP">GBP (£)</option>
                                        <option value="JPY">JPY (¥)</option>
                                        <option value="CAD">CAD ($)</option>
                                        <option value="AUD">AUD ($)</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div>
                                <h4 class="font-medium text-gray-900 mb-2">Email Notifications</h4>
                                <div class="space-y-2">
                                    <label class="flex items-center">
                                        <input
                                            type="checkbox"
                                            bind:checked={preferencesData.notification_preferences.email_daily_summary}
                                            class="form-checkbox"
                                        />
                                        <span class="ml-2">Daily trading summary</span>
                                    </label>
                                    <label class="flex items-center">
                                        <input
                                            type="checkbox"
                                            bind:checked={preferencesData.notification_preferences.email_weekly_report}
                                            class="form-checkbox"
                                        />
                                        <span class="ml-2">Weekly performance report</span>
                                    </label>
                                    <label class="flex items-center">
                                        <input
                                            type="checkbox"
                                            bind:checked={preferencesData.notification_preferences.email_trade_alerts}
                                            class="form-checkbox"
                                        />
                                        <span class="ml-2">Trade alerts and notifications</span>
                                    </label>
                                </div>
                            </div>
                            
                            <div>
                                <h4 class="font-medium text-gray-900 mb-2">Display Preferences</h4>
                                <div class="space-y-2">
                                    <label class="flex items-center">
                                        <input
                                            type="checkbox"
                                            bind:checked={preferencesData.display_preferences.compact_view}
                                            class="form-checkbox"
                                        />
                                        <span class="ml-2">Compact view (show more data)</span>
                                    </label>
                                </div>
                            </div>
                            
                            <div class="flex justify-between pt-4">
                                <button
                                    type="button"
                                    on:click={() => skipStep('trading_preferences', 'use_defaults')}
                                    class="btn btn-secondary"
                                    disabled={animating}
                                >
                                    Use defaults
                                </button>
                                <button
                                    type="submit"
                                    class="btn btn-primary"
                                    disabled={animating}
                                >
                                    Continue
                                    <Icon name="arrow-right" class="w-5 h-5 ml-2" />
                                </button>
                            </div>
                        </form>
                    </div>
                    
                {:else if state.current_step === 'first_trade'}
                    <div in:fly={{ x: 50, duration: 300 }}>
                        <h3 class="text-xl font-bold text-gray-900 mb-4">Import Your First Trade</h3>
                        <p class="text-gray-600 mb-6">Let's add some trades to start analyzing your performance</p>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                            <a
                                href="/trades/import"
                                class="block p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 transition-colors"
                            >
                                <Icon name="upload-cloud" class="w-8 h-8 text-indigo-600 mb-2" />
                                <h4 class="font-medium text-gray-900">CSV Import</h4>
                                <p class="text-sm text-gray-600 mt-1">Upload your trade history</p>
                            </a>
                            
                            <a
                                href="/trades/new"
                                class="block p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 transition-colors"
                            >
                                <Icon name="edit" class="w-8 h-8 text-indigo-600 mb-2" />
                                <h4 class="font-medium text-gray-900">Manual Entry</h4>
                                <p class="text-sm text-gray-600 mt-1">Add trades one by one</p>
                            </a>
                            
                            <a
                                href="/settings/integrations"
                                class="block p-4 border-2 border-gray-200 rounded-lg hover:border-indigo-500 transition-colors"
                            >
                                <Icon name="link" class="w-8 h-8 text-indigo-600 mb-2" />
                                <h4 class="font-medium text-gray-900">Broker Connect</h4>
                                <p class="text-sm text-gray-600 mt-1">Sync automatically</p>
                            </a>
                        </div>
                        
                        {#if state.user_stats.trade_count > 0}
                            <div class="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                                <p class="text-sm text-green-800">
                                    ✓ Great! You already have {state.user_stats.trade_count} trade{state.user_stats.trade_count > 1 ? 's' : ''} imported.
                                </p>
                            </div>
                            
                            <button
                                on:click={completeFirstTrade}
                                class="btn btn-primary w-full"
                                disabled={animating}
                            >
                                Continue to Analytics
                                <Icon name="arrow-right" class="w-5 h-5 ml-2" />
                            </button>
                        {:else}
                            <p class="text-sm text-gray-500 text-center">
                                Import at least one trade to continue, or skip this step for now.
                            </p>
                            
                            <div class="flex justify-center mt-4">
                                <button
                                    on:click={() => skipStep('first_trade', 'import_later')}
                                    class="btn btn-secondary"
                                    disabled={animating}
                                >
                                    I'll import later
                                </button>
                            </div>
                        {/if}
                    </div>
                    
                {:else if state.current_step === 'analytics_tour'}
                    <div in:fly={{ x: 50, duration: 300 }}>
                        <h3 class="text-xl font-bold text-gray-900 mb-4">Explore Your Analytics</h3>
                        <p class="text-gray-600 mb-6">Discover powerful insights about your trading performance</p>
                        
                        <div class="space-y-4">
                            <div class="flex items-start">
                                <Icon name="pie-chart" class="w-6 h-6 text-indigo-600 mt-1 mr-3 flex-shrink-0" />
                                <div>
                                    <h4 class="font-medium text-gray-900">Performance Overview</h4>
                                    <p class="text-sm text-gray-600 mt-1">
                                        Track your P&L, win rate, and key metrics at a glance
                                    </p>
                                </div>
                            </div>
                            
                            <div class="flex items-start">
                                <Icon name="trending-up" class="w-6 h-6 text-indigo-600 mt-1 mr-3 flex-shrink-0" />
                                <div>
                                    <h4 class="font-medium text-gray-900">Trade Analysis</h4>
                                    <p class="text-sm text-gray-600 mt-1">
                                        Deep dive into individual trades and patterns
                                    </p>
                                </div>
                            </div>
                            
                            <div class="flex items-start">
                                <Icon name="calendar" class="w-6 h-6 text-indigo-600 mt-1 mr-3 flex-shrink-0" />
                                <div>
                                    <h4 class="font-medium text-gray-900">Time-based Insights</h4>
                                    <p class="text-sm text-gray-600 mt-1">
                                        Understand your performance across different time periods
                                    </p>
                                </div>
                            </div>
                            
                            <div class="flex items-start">
                                <Icon name="target" class="w-6 h-6 text-indigo-600 mt-1 mr-3 flex-shrink-0" />
                                <div>
                                    <h4 class="font-medium text-gray-900">Risk Management</h4>
                                    <p class="text-sm text-gray-600 mt-1">
                                        Monitor your risk exposure and position sizing
                                    </p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-6 flex justify-between">
                            <button
                                on:click={() => skipStep('analytics_tour', 'explore_later')}
                                class="btn btn-secondary"
                                disabled={animating}
                            >
                                Explore later
                            </button>
                            <a
                                href="/analytics"
                                on:click={() => completeAnalyticsTour()}
                                class="btn btn-primary"
                            >
                                Show me the analytics
                                <Icon name="arrow-right" class="w-5 h-5 ml-2" />
                            </a>
                        </div>
                    </div>
                    
                {:else if state.current_step === 'plan_selection'}
                    <div in:fly={{ x: 50, duration: 300 }}>
                        <h3 class="text-xl font-bold text-gray-900 mb-4">Choose Your Plan</h3>
                        <p class="text-gray-600 mb-6">Select the plan that best fits your trading needs</p>
                        
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <!-- Free Plan -->
                            <div class="border-2 border-gray-200 rounded-lg p-4">
                                <h4 class="text-lg font-bold text-gray-900">Free</h4>
                                <p class="text-3xl font-bold text-gray-900 mt-2">$0<span class="text-sm font-normal text-gray-500">/month</span></p>
                                <ul class="mt-4 space-y-2 text-sm">
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>100 trades per month</span>
                                    </li>
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Basic analytics</span>
                                    </li>
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Email support</span>
                                    </li>
                                </ul>
                                <button
                                    on:click={() => completePlanSelection('free')}
                                    class="w-full mt-4 btn btn-secondary"
                                    disabled={animating}
                                >
                                    Continue with Free
                                </button>
                            </div>
                            
                            <!-- Pro Plan -->
                            <div class="border-2 border-indigo-500 rounded-lg p-4 relative">
                                <div class="absolute top-0 right-0 bg-indigo-500 text-white text-xs px-2 py-1 rounded-bl-md rounded-tr-md">
                                    Popular
                                </div>
                                <h4 class="text-lg font-bold text-gray-900">Pro</h4>
                                <p class="text-3xl font-bold text-gray-900 mt-2">$49<span class="text-sm font-normal text-gray-500">/month</span></p>
                                <ul class="mt-4 space-y-2 text-sm">
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Unlimited trades</span>
                                    </li>
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Advanced analytics</span>
                                    </li>
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Priority support</span>
                                    </li>
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>API access</span>
                                    </li>
                                </ul>
                                <a
                                    href="/subscription"
                                    on:click={() => completePlanSelection('pro')}
                                    class="block w-full mt-4 btn btn-primary text-center"
                                >
                                    Start Pro Trial
                                </a>
                            </div>
                            
                            <!-- Premium Plan -->
                            <div class="border-2 border-gray-200 rounded-lg p-4">
                                <h4 class="text-lg font-bold text-gray-900">Premium</h4>
                                <p class="text-3xl font-bold text-gray-900 mt-2">$99<span class="text-sm font-normal text-gray-500">/month</span></p>
                                <ul class="mt-4 space-y-2 text-sm">
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Everything in Pro</span>
                                    </li>
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Real-time alerts</span>
                                    </li>
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Custom reports</span>
                                    </li>
                                    <li class="flex items-start">
                                        <Icon name="check" class="w-5 h-5 text-green-500 mr-2 flex-shrink-0" />
                                        <span>Phone support</span>
                                    </li>
                                </ul>
                                <a
                                    href="/subscription"
                                    on:click={() => completePlanSelection('premium')}
                                    class="block w-full mt-4 btn btn-secondary text-center"
                                >
                                    Start Premium Trial
                                </a>
                            </div>
                        </div>
                        
                        <p class="text-sm text-gray-500 text-center mt-6">
                            All paid plans include a 14-day free trial. No credit card required.
                        </p>
                    </div>
                    
                {:else}
                    <div class="text-center py-8">
                        <Icon name="check-circle" class="w-16 h-16 text-green-500 mx-auto mb-4" />
                        <h3 class="text-2xl font-bold text-gray-900 mb-4">You're all set!</h3>
                        <p class="text-gray-600 mb-8">
                            Your account is ready. Start exploring TradeSense!
                        </p>
                        <a href="/dashboard" class="btn btn-primary btn-lg">
                            Go to Dashboard
                            <Icon name="arrow-right" class="w-5 h-5 ml-2" />
                        </a>
                    </div>
                {/if}
            </div>
            
            <!-- Quick tips -->
            {#if state.tips && state.tips.length > 0}
                <div class="bg-gray-50 border-t border-gray-200 p-4">
                    <h4 class="text-sm font-medium text-gray-700 mb-2">
                        <Icon name="lightbulb" class="w-4 h-4 inline mr-1" />
                        Quick Tips
                    </h4>
                    <div class="space-y-2">
                        {#each state.tips as tip}
                            <div class="flex items-start text-sm">
                                <Icon name="info" class="w-4 h-4 text-indigo-500 mr-2 mt-0.5 flex-shrink-0" />
                                <div>
                                    <span class="font-medium">{tip.title}:</span>
                                    <span class="text-gray-600">{tip.content}</span>
                                    {#if tip.link}
                                        <a href={tip.link} class="text-indigo-600 hover:text-indigo-700 ml-1">
                                            Learn more →
                                        </a>
                                    {/if}
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    </div>
{/if}

<style>
    .form-input, .form-select, .form-textarea {
        @apply w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500;
    }
    
    .form-checkbox {
        @apply rounded border-gray-300 text-indigo-600 focus:ring-indigo-500;
    }
    
    .btn {
        @apply px-4 py-2 rounded-md font-medium transition-colors inline-flex items-center justify-center;
    }
    
    .btn-primary {
        @apply bg-indigo-600 text-white hover:bg-indigo-700;
    }
    
    .btn-secondary {
        @apply bg-gray-200 text-gray-800 hover:bg-gray-300;
    }
    
    .btn-lg {
        @apply px-6 py-3 text-lg;
    }
    
    .alert {
        @apply p-4 rounded-md;
    }
    
    .alert-error {
        @apply bg-red-50 text-red-800 border border-red-200;
    }
</style>