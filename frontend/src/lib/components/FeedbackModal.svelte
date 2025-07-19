<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { X, Camera, AlertCircle, Bug, Zap, Layout, HelpCircle } from 'lucide-svelte';
  import { page } from '$app/stores';
  import { feedbackApi } from '$lib/api/feedback';
  import { capturePageContext } from '$lib/utils/feedbackContext';
  import html2canvas from 'html2canvas';

  const dispatch = createEventDispatcher();

  // Form data
  let type: 'bug' | 'feature' | 'performance' | 'ux' | 'other' = 'bug';
  let severity: 'critical' | 'high' | 'medium' | 'low' = 'medium';
  let title = '';
  let description = '';
  let expectedBehavior = '';
  let actualBehavior = '';
  let email = '';
  let includeScreenshot = false;
  let screenshot: string | null = null;
  let submitting = false;
  let submitted = false;
  let trackingId = '';

  // Context data
  const context = capturePageContext();
  
  const typeIcons = {
    bug: Bug,
    feature: HelpCircle,
    performance: Zap,
    ux: Layout,
    other: AlertCircle
  };

  const severityColors = {
    critical: '#ef4444',
    high: '#f97316',
    medium: '#eab308',
    low: '#3b82f6'
  };

  async function captureScreenshot() {
    try {
      const canvas = await html2canvas(document.body, {
        logging: false,
        useCORS: true,
        scale: 0.5, // Reduce size
        ignoreElements: (element) => {
          return element.classList.contains('feedback-modal-overlay');
        }
      });
      screenshot = canvas.toDataURL('image/jpeg', 0.8);
      includeScreenshot = true;
    } catch (error) {
      console.error('Screenshot capture failed:', error);
    }
  }

  async function handleSubmit() {
    if (!title || !description) return;

    submitting = true;

    try {
      const feedbackData = {
        type,
        severity,
        title,
        description,
        expectedBehavior,
        actualBehavior,
        email: email || undefined,
        url: $page.url.pathname,
        userAgent: navigator.userAgent,
        screenResolution: `${window.screen.width}x${window.screen.height}`,
        previousPages: context.previousPages,
        lastActions: context.lastActions,
        errorLogs: context.errorLogs,
        screenshot: includeScreenshot ? screenshot : undefined,
        timestamp: new Date().toISOString()
      };

      const response = await feedbackApi.submit(feedbackData);
      trackingId = response.trackingId;
      submitted = true;

      // Track feedback submission
      if (window.gtag) {
        window.gtag('event', 'feedback_submitted', {
          feedback_type: type,
          severity: severity
        });
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      submitting = false;
    }
  }

  function close() {
    dispatch('close');
  }

  // Auto-capture screenshot for bug reports
  onMount(() => {
    if (type === 'bug') {
      captureScreenshot();
    }
  });
</script>

<div class="feedback-modal-overlay" on:click={close}>
  <div class="feedback-modal" on:click|stopPropagation>
    <div class="modal-header">
      <h2>{submitted ? '🙏 Thank You!' : '📝 Send Feedback'}</h2>
      <button class="close-button" on:click={close}>
        <X size={20} />
      </button>
    </div>

    {#if submitted}
      <div class="thank-you-content">
        <div class="success-icon">✅</div>
        <h3>Your feedback has been received!</h3>
        <p>We truly appreciate you taking the time to help us improve TradeSense.</p>
        
        <div class="tracking-info">
          <p><strong>Tracking ID:</strong> #{trackingId}</p>
          {#if email}
            <p>We'll send updates to: <strong>{email}</strong></p>
          {/if}
        </div>

        <div class="severity-message" style="border-color: {severityColors[severity]}">
          {#if severity === 'critical'}
            <p>🚨 We're treating this as urgent and will address it immediately.</p>
          {:else if severity === 'high'}
            <p>⚡ This is a high priority issue. We'll look into it within 24 hours.</p>
          {:else}
            <p>📋 We typically resolve {type} issues within 48-72 hours.</p>
          {/if}
        </div>

        <button class="submit-button" on:click={close}>
          Continue Trading
        </button>
      </div>
    {:else}
      <form on:submit|preventDefault={handleSubmit}>
        <!-- Feedback Type -->
        <div class="form-section">
          <label>What type of feedback is this?</label>
          <div class="type-grid">
            {#each Object.entries(typeIcons) as [value, Icon]}
              <button
                type="button"
                class="type-button"
                class:selected={type === value}
                on:click={() => type = value}
              >
                <Icon size={20} />
                <span>{value.charAt(0).toUpperCase() + value.slice(1)}</span>
              </button>
            {/each}
          </div>
        </div>

        <!-- Severity -->
        <div class="form-section">
          <label>How severe is this issue?</label>
          <div class="severity-grid">
            {#each Object.entries(severityColors) as [value, color]}
              <button
                type="button"
                class="severity-button"
                class:selected={severity === value}
                style="--severity-color: {color}"
                on:click={() => severity = value}
              >
                {value.charAt(0).toUpperCase() + value.slice(1)}
              </button>
            {/each}
          </div>
        </div>

        <!-- Title -->
        <div class="form-section">
          <label for="title">Brief summary <span class="required">*</span></label>
          <input
            id="title"
            type="text"
            bind:value={title}
            placeholder="e.g., Chart not loading on analytics page"
            required
          />
        </div>

        <!-- Description -->
        <div class="form-section">
          <label for="description">Detailed description <span class="required">*</span></label>
          <textarea
            id="description"
            bind:value={description}
            placeholder="Please describe what happened..."
            rows="4"
            required
          />
        </div>

        <!-- Expected vs Actual (for bugs) -->
        {#if type === 'bug'}
          <div class="form-section">
            <label for="expected">What did you expect to happen?</label>
            <textarea
              id="expected"
              bind:value={expectedBehavior}
              placeholder="e.g., Chart should display my trading data"
              rows="2"
            />
          </div>

          <div class="form-section">
            <label for="actual">What actually happened?</label>
            <textarea
              id="actual"
              bind:value={actualBehavior}
              placeholder="e.g., Chart shows blank screen"
              rows="2"
            />
          </div>
        {/if}

        <!-- Screenshot -->
        <div class="form-section">
          <label>
            <input
              type="checkbox"
              bind:checked={includeScreenshot}
              on:change={() => {
                if (includeScreenshot && !screenshot) {
                  captureScreenshot();
                }
              }}
            />
            Include screenshot
          </label>
          {#if includeScreenshot && screenshot}
            <div class="screenshot-preview">
              <img src={screenshot} alt="Screenshot" />
              <button type="button" on:click={captureScreenshot}>
                <Camera size={16} /> Retake
              </button>
            </div>
          {/if}
        </div>

        <!-- Email (optional) -->
        <div class="form-section">
          <label for="email">Email (optional - for updates)</label>
          <input
            id="email"
            type="email"
            bind:value={email}
            placeholder="your@email.com"
          />
        </div>

        <!-- Context Info -->
        <details class="context-details">
          <summary>Technical details (auto-collected)</summary>
          <div class="context-info">
            <p><strong>Page:</strong> {$page.url.pathname}</p>
            <p><strong>Browser:</strong> {context.browser}</p>
            <p><strong>Screen:</strong> {window.screen.width}x{window.screen.height}</p>
            <p><strong>Recent actions:</strong> {context.lastActions.length} tracked</p>
            <p><strong>Error logs:</strong> {context.errorLogs.length} found</p>
          </div>
        </details>

        <button 
          type="submit" 
          class="submit-button"
          disabled={submitting || !title || !description}
        >
          {submitting ? 'Submitting...' : 'Submit Feedback'}
        </button>
      </form>
    {/if}
  </div>
</div>

<style>
  .feedback-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
    z-index: 1001;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  .feedback-modal {
    background: white;
    border-radius: 0.75rem;
    width: 100%;
    max-width: 600px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .modal-header h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 700;
  }

  .close-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 0.375rem;
    color: #6b7280;
    transition: all 0.2s;
  }

  .close-button:hover {
    background: #f3f4f6;
    color: #374151;
  }

  form {
    padding: 1.5rem;
  }

  .form-section {
    margin-bottom: 1.5rem;
  }

  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: #374151;
    font-size: 0.875rem;
  }

  .required {
    color: #ef4444;
  }

  input[type="text"],
  input[type="email"],
  textarea {
    width: 100%;
    padding: 0.5rem 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    transition: all 0.2s;
  }

  input:focus,
  textarea:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  textarea {
    resize: vertical;
    min-height: 60px;
  }

  .type-grid,
  .severity-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 0.5rem;
  }

  .type-button,
  .severity-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 0.75rem;
    border: 2px solid #e5e7eb;
    border-radius: 0.5rem;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .type-button:hover,
  .severity-button:hover {
    border-color: #667eea;
    background: #f3f4f6;
  }

  .type-button.selected {
    border-color: #667eea;
    background: #eef2ff;
    color: #667eea;
  }

  .severity-button.selected {
    border-color: var(--severity-color);
    background: var(--severity-color);
    color: white;
  }

  .screenshot-preview {
    margin-top: 0.5rem;
    position: relative;
    border-radius: 0.375rem;
    overflow: hidden;
  }

  .screenshot-preview img {
    width: 100%;
    height: 150px;
    object-fit: cover;
  }

  .screenshot-preview button {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    border: none;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.75rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .context-details {
    margin-top: 1rem;
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 0.375rem;
    padding: 0.75rem;
  }

  .context-details summary {
    cursor: pointer;
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
  }

  .context-info {
    margin-top: 0.75rem;
    font-size: 0.75rem;
    color: #6b7280;
  }

  .context-info p {
    margin: 0.25rem 0;
  }

  .submit-button {
    width: 100%;
    padding: 0.75rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .submit-button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  }

  .submit-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Thank you state */
  .thank-you-content {
    padding: 2rem;
    text-align: center;
  }

  .success-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
  }

  .thank-you-content h3 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }

  .thank-you-content p {
    color: #6b7280;
    margin-bottom: 1rem;
  }

  .tracking-info {
    background: #f3f4f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 1.5rem 0;
  }

  .tracking-info p {
    margin: 0.25rem 0;
    font-size: 0.875rem;
  }

  .severity-message {
    border-left: 4px solid;
    padding-left: 1rem;
    margin: 1.5rem 0;
    text-align: left;
  }

  /* Mobile */
  @media (max-width: 640px) {
    .feedback-modal {
      max-height: 100vh;
      border-radius: 0;
    }

    .type-grid {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>