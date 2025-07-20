<script>
    import { onMount } from 'svelte';
    import { api } from '$lib/api';
    import Icon from '$lib/components/Icon.svelte';
    
    export let onClose = () => {};
    export let onSuccess = () => {};
    export let template = null;
    
    // Alert types
    const alertTypes = {
        price: [
            { value: 'price_above', label: 'Price Above' },
            { value: 'price_below', label: 'Price Below' },
            { value: 'price_change_percent', label: 'Price Change %' }
        ],
        performance: [
            { value: 'daily_pnl', label: 'Daily P&L' },
            { value: 'weekly_pnl', label: 'Weekly P&L' },
            { value: 'win_rate', label: 'Win Rate' },
            { value: 'loss_streak', label: 'Loss Streak' },
            { value: 'win_streak', label: 'Win Streak' }
        ],
        risk: [
            { value: 'drawdown', label: 'Drawdown' },
            { value: 'position_size', label: 'Position Size' },
            { value: 'exposure_limit', label: 'Exposure Limit' }
        ],
        pattern: [
            { value: 'pattern_detected', label: 'Pattern Detected' },
            { value: 'strategy_signal', label: 'Strategy Signal' }
        ],
        market: [
            { value: 'volume_spike', label: 'Volume Spike' },
            { value: 'volatility', label: 'Volatility' },
            { value: 'news_sentiment', label: 'News Sentiment' }
        ],
        account: [
            { value: 'margin_call', label: 'Margin Call' },
            { value: 'account_balance', label: 'Account Balance' },
            { value: 'trade_execution', label: 'Trade Execution' }
        ]
    };
    
    // Form data
    let name = '';
    let description = '';
    let selectedCategory = 'price';
    let selectedType = 'price_above';
    let conditions = [{ field: 'current_price', operator: 'gt', value: '' }];
    let channels = { email: true, in_app: true, sms: false, webhook: false };
    let priority = 'medium';
    let symbols = '';
    let strategies = '';
    let cooldownMinutes = 60;
    let maxTriggersPerDay = null;
    let expiresAt = null;
    let webhookUrl = '';
    
    let loading = false;
    let error = null;
    let step = 1;
    
    // Initialize from template if provided
    if (template) {
        name = template.name;
        description = template.description || '';
        selectedType = template.type;
        conditions = template.default_conditions;
        priority = template.default_priority;
        
        // Set channels
        channels = {
            email: template.default_channels.includes('email'),
            in_app: template.default_channels.includes('in_app'),
            sms: template.default_channels.includes('sms'),
            webhook: template.default_channels.includes('webhook')
        };
        
        // Find category
        for (const [cat, types] of Object.entries(alertTypes)) {
            if (types.some(t => t.value === selectedType)) {
                selectedCategory = cat;
                break;
            }
        }
    }
    
    function addCondition() {
        conditions = [...conditions, { field: '', operator: 'gt', value: '' }];
    }
    
    function removeCondition(index) {
        conditions = conditions.filter((_, i) => i !== index);
    }
    
    function getConditionFields(alertType) {
        // Return relevant fields based on alert type
        const fieldMap = {
            price_above: ['current_price', 'ask_price', 'bid_price'],
            price_below: ['current_price', 'ask_price', 'bid_price'],
            price_change_percent: ['price_change_percent', 'price_change_amount'],
            daily_pnl: ['current_value', 'pnl_amount', 'pnl_percent'],
            weekly_pnl: ['current_value', 'pnl_amount', 'pnl_percent'],
            win_rate: ['current_value', 'win_count', 'total_trades'],
            loss_streak: ['current_value', 'consecutive_losses'],
            win_streak: ['current_value', 'consecutive_wins'],
            drawdown: ['current_value', 'drawdown_percent', 'drawdown_amount'],
            position_size: ['position_size_percent', 'position_value', 'shares'],
            pattern_detected: ['pattern_name', 'pattern_confidence', 'pattern_type'],
            volume_spike: ['volume_ratio', 'current_volume', 'average_volume'],
            account_balance: ['account_balance', 'available_balance', 'margin_used']
        };
        
        return fieldMap[alertType] || ['current_value'];
    }
    
    async function createAlert() {
        if (!name || conditions.length === 0) {
            error = 'Please fill in all required fields';
            return;
        }
        
        loading = true;
        error = null;
        
        try {
            // Build channels array
            const selectedChannels = Object.entries(channels)
                .filter(([_, enabled]) => enabled)
                .map(([channel, _]) => channel);
            
            if (selectedChannels.length === 0) {
                throw new Error('Select at least one notification channel');
            }
            
            // Build request
            const request = {
                name,
                description: description || null,
                type: selectedType,
                conditions: conditions.filter(c => c.field && c.value !== ''),
                channels: selectedChannels,
                priority,
                symbols: symbols ? symbols.split(',').map(s => s.trim()) : null,
                strategies: strategies ? strategies.split(',').map(s => s.trim()) : null,
                cooldown_minutes: cooldownMinutes,
                max_triggers_per_day: maxTriggersPerDay || null,
                expires_at: expiresAt || null,
                webhook_url: channels.webhook ? webhookUrl : null
            };
            
            await api.post('/alerts/create', request);
            
            onSuccess();
            onClose();
            
        } catch (err) {
            error = err.message || 'Failed to create alert';
        } finally {
            loading = false;
        }
    }
    
    function nextStep() {
        if (step === 1 && !name) {
            error = 'Please enter an alert name';
            return;
        }
        error = null;
        step++;
    }
    
    function prevStep() {
        error = null;
        step--;
    }
    
    $: {
        // Update first condition field when alert type changes
        if (conditions.length > 0 && !conditions[0].field) {
            const fields = getConditionFields(selectedType);
            conditions[0].field = fields[0];
        }
    }
</script>

<div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <!-- Header -->
        <div class="p-6 border-b border-gray-200 sticky top-0 bg-white z-10">
            <div class="flex items-center justify-between">
                <h2 class="text-2xl font-bold text-gray-900">
                    {template ? `Create Alert from Template` : 'Create New Alert'}
                </h2>
                <button
                    on:click={onClose}
                    class="text-gray-500 hover:text-gray-700"
                >
                    <Icon name="x" class="w-6 h-6" />
                </button>
            </div>
            
            <!-- Step indicators -->
            <div class="mt-4 flex items-center justify-center">
                <div class="flex items-center space-x-2">
                    <div class="step" class:active={step === 1}>1</div>
                    <div class="step-line" class:active={step > 1}></div>
                    <div class="step" class:active={step === 2}>2</div>
                    <div class="step-line" class:active={step > 2}></div>
                    <div class="step" class:active={step === 3}>3</div>
                </div>
            </div>
        </div>
        
        <!-- Body -->
        <div class="p-6">
            {#if error}
                <div class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                </div>
            {/if}
            
            <!-- Step 1: Basic Info -->
            {#if step === 1}
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Alert Name <span class="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            bind:value={name}
                            placeholder="e.g., SPY Price Alert"
                            class="form-input"
                            maxlength="100"
                        />
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Description
                        </label>
                        <textarea
                            bind:value={description}
                            placeholder="Optional description of what this alert does"
                            class="form-input"
                            rows="2"
                            maxlength="500"
                        />
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Alert Category
                        </label>
                        <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            {#each Object.keys(alertTypes) as category}
                                <button
                                    on:click={() => { selectedCategory = category; selectedType = alertTypes[category][0].value; }}
                                    class="p-3 border rounded-lg text-center capitalize transition-colors"
                                    class:border-indigo-500={selectedCategory === category}
                                    class:bg-indigo-50={selectedCategory === category}
                                    class:border-gray-200={selectedCategory !== category}
                                >
                                    {category}
                                </button>
                            {/each}
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Alert Type
                        </label>
                        <select bind:value={selectedType} class="form-input">
                            {#each alertTypes[selectedCategory] as type}
                                <option value={type.value}>{type.label}</option>
                            {/each}
                        </select>
                    </div>
                </div>
            {/if}
            
            <!-- Step 2: Conditions -->
            {#if step === 2}
                <div class="space-y-4">
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <label class="text-sm font-medium text-gray-700">
                                Alert Conditions <span class="text-red-500">*</span>
                            </label>
                            <button
                                on:click={addCondition}
                                class="text-sm text-indigo-600 hover:text-indigo-700"
                            >
                                + Add Condition
                            </button>
                        </div>
                        
                        <div class="space-y-3">
                            {#each conditions as condition, i}
                                <div class="flex items-center space-x-2">
                                    <select
                                        bind:value={condition.field}
                                        class="form-input flex-1"
                                    >
                                        <option value="">Select field</option>
                                        {#each getConditionFields(selectedType) as field}
                                            <option value={field}>
                                                {field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                            </option>
                                        {/each}
                                    </select>
                                    
                                    <select
                                        bind:value={condition.operator}
                                        class="form-input w-32"
                                    >
                                        <option value="gt">Greater than</option>
                                        <option value="gte">Greater or equal</option>
                                        <option value="lt">Less than</option>
                                        <option value="lte">Less or equal</option>
                                        <option value="eq">Equals</option>
                                    </select>
                                    
                                    <input
                                        type="text"
                                        bind:value={condition.value}
                                        placeholder="Value"
                                        class="form-input w-32"
                                    />
                                    
                                    {#if conditions.length > 1}
                                        <button
                                            on:click={() => removeCondition(i)}
                                            class="text-red-600 hover:text-red-700"
                                        >
                                            <Icon name="trash-2" class="w-4 h-4" />
                                        </button>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Symbols (optional)
                        </label>
                        <input
                            type="text"
                            bind:value={symbols}
                            placeholder="e.g., AAPL, GOOGL, SPY (comma-separated)"
                            class="form-input"
                        />
                        <p class="text-xs text-gray-500 mt-1">
                            Leave empty to monitor all symbols
                        </p>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Strategies (optional)
                        </label>
                        <input
                            type="text"
                            bind:value={strategies}
                            placeholder="e.g., momentum, mean-reversion (comma-separated)"
                            class="form-input"
                        />
                    </div>
                </div>
            {/if}
            
            <!-- Step 3: Notifications -->
            {#if step === 3}
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Notification Channels <span class="text-red-500">*</span>
                        </label>
                        <div class="space-y-2">
                            <label class="flex items-center">
                                <input
                                    type="checkbox"
                                    bind:checked={channels.email}
                                    class="rounded border-gray-300 text-indigo-600 mr-2"
                                />
                                <Icon name="mail" class="w-4 h-4 mr-2 text-gray-600" />
                                Email
                            </label>
                            <label class="flex items-center">
                                <input
                                    type="checkbox"
                                    bind:checked={channels.in_app}
                                    class="rounded border-gray-300 text-indigo-600 mr-2"
                                />
                                <Icon name="bell" class="w-4 h-4 mr-2 text-gray-600" />
                                In-App Notifications
                            </label>
                            <label class="flex items-center">
                                <input
                                    type="checkbox"
                                    bind:checked={channels.sms}
                                    class="rounded border-gray-300 text-indigo-600 mr-2"
                                />
                                <Icon name="message-square" class="w-4 h-4 mr-2 text-gray-600" />
                                SMS (requires phone number)
                            </label>
                            <label class="flex items-center">
                                <input
                                    type="checkbox"
                                    bind:checked={channels.webhook}
                                    class="rounded border-gray-300 text-indigo-600 mr-2"
                                />
                                <Icon name="link" class="w-4 h-4 mr-2 text-gray-600" />
                                Webhook
                            </label>
                        </div>
                    </div>
                    
                    {#if channels.webhook}
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Webhook URL
                            </label>
                            <input
                                type="url"
                                bind:value={webhookUrl}
                                placeholder="https://example.com/webhook"
                                class="form-input"
                            />
                        </div>
                    {/if}
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Priority
                        </label>
                        <select bind:value={priority} class="form-input">
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                            <option value="critical">Critical</option>
                        </select>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Cooldown (minutes)
                            </label>
                            <input
                                type="number"
                                bind:value={cooldownMinutes}
                                min="1"
                                max="1440"
                                class="form-input"
                            />
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Max Triggers/Day
                            </label>
                            <input
                                type="number"
                                bind:value={maxTriggersPerDay}
                                min="1"
                                max="100"
                                placeholder="Unlimited"
                                class="form-input"
                            />
                        </div>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Expires On (optional)
                        </label>
                        <input
                            type="datetime-local"
                            bind:value={expiresAt}
                            class="form-input"
                        />
                    </div>
                </div>
            {/if}
        </div>
        
        <!-- Footer -->
        <div class="p-6 border-t border-gray-200 bg-gray-50">
            <div class="flex justify-between">
                <button
                    on:click={step > 1 ? prevStep : onClose}
                    class="btn btn-secondary"
                >
                    {step > 1 ? 'Back' : 'Cancel'}
                </button>
                
                {#if step < 3}
                    <button
                        on:click={nextStep}
                        class="btn btn-primary"
                    >
                        Next
                    </button>
                {:else}
                    <button
                        on:click={createAlert}
                        disabled={loading}
                        class="btn btn-primary"
                    >
                        {#if loading}
                            <span class="spinner mr-2"></span>
                        {/if}
                        Create Alert
                    </button>
                {/if}
            </div>
        </div>
    </div>
</div>

<style>
    .form-input {
        display: block;
        width: 100%;
        padding: 0.5rem 0.75rem;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
    }
    
    .form-input:focus {
        outline: none;
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }
    
    .btn {
        padding: 0.5rem 1rem; border-radius: 0.375rem; font-weight: 500; transition: background-color 0.2s, color 0.2s; display: inline-flex; align-items: center; justify-content: center;
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
    
    .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    
    .spinner {
        width: 1rem;
        height: 1rem;
        border-width: 2px;
        border-style: solid;
        border-color: white;
        border-top-color: transparent;
        border-radius: 9999px;
        animation: spin 1s linear infinite;
    }
    
    .step {
        width: 2rem;
        height: 2rem;
        border-radius: 9999px;
        background-color: #e5e7eb;
        color: #4b5563;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        transition: background-color 0.15s ease-in-out, color 0.15s ease-in-out;
    }
    
    .step.active {
        background-color: #4f46e5;
        color: white;
    }
    
    .step-line {
        width: 4rem;
        height: 0.125rem;
        background-color: #e5e7eb;
        transition: background-color 0.15s ease-in-out;
    }
    
    .step-line.active {
        background-color: #4f46e5;
    }
</style>