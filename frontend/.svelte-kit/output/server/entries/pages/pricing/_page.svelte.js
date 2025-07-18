import { c as create_ssr_component, v as validate_component, e as each, b as escape } from "../../../chunks/ssr.js";
import "../../../chunks/client.js";
import "../../../chunks/client2.js";
import "../../../chunks/auth.js";
import { I as Icon } from "../../../chunks/Icon.js";
import { X } from "../../../chunks/x.js";
import { T as Trending_up } from "../../../chunks/trending-up.js";
const Check = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [["path", { "d": "M20 6 9 17l-5-5" }]];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "check" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Shield = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "shield" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const Zap = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const iconNode = [
    [
      "path",
      {
        "d": "M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"
      }
    ]
  ];
  return `${validate_component(Icon, "Icon").$$render($$result, Object.assign({}, { name: "zap" }, $$props, { iconNode }), {}, {
    default: () => {
      return `${slots.default ? slots.default({}) : ``}`;
    }
  })}`;
});
const css = {
  code: ".pricing-page.svelte-yi5o0s.svelte-yi5o0s{max-width:1200px;margin:0 auto;padding-bottom:4rem}.pricing-header.svelte-yi5o0s.svelte-yi5o0s{text-align:center;margin-bottom:3rem}.pricing-header.svelte-yi5o0s h1.svelte-yi5o0s{font-size:3rem;margin-bottom:1rem;background:linear-gradient(135deg, #10b981 0%, #059669 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}.pricing-header.svelte-yi5o0s p.svelte-yi5o0s{font-size:1.25rem;color:#666;margin-bottom:2rem}.billing-toggle.svelte-yi5o0s.svelte-yi5o0s{display:inline-flex;align-items:center;gap:1rem;padding:0.5rem;background:#f3f4f6;border-radius:100px}.billing-toggle.svelte-yi5o0s span.svelte-yi5o0s{padding:0.5rem 1rem;color:#666;transition:color 0.2s}.billing-toggle.svelte-yi5o0s span.active.svelte-yi5o0s{color:#333;font-weight:600}.toggle-switch.svelte-yi5o0s.svelte-yi5o0s{position:relative;width:56px;height:28px;background:#e5e7eb;border:none;border-radius:100px;cursor:pointer;transition:background 0.3s}.toggle-switch.annual.svelte-yi5o0s.svelte-yi5o0s{background:#10b981}.toggle-slider.svelte-yi5o0s.svelte-yi5o0s{position:absolute;top:2px;left:2px;width:24px;height:24px;background:white;border-radius:50%;transition:transform 0.3s;box-shadow:0 2px 4px rgba(0, 0, 0, 0.1)}.toggle-switch.annual.svelte-yi5o0s .toggle-slider.svelte-yi5o0s{transform:translateX(28px)}.save-badge.svelte-yi5o0s.svelte-yi5o0s{background:#10b981;color:white;padding:0.125rem 0.5rem;border-radius:12px;font-size:0.75rem;margin-left:0.5rem}.error-message.svelte-yi5o0s.svelte-yi5o0s{background:#fee;color:#dc2626;padding:1rem;border-radius:8px;text-align:center;margin-bottom:2rem}.pricing-grid.svelte-yi5o0s.svelte-yi5o0s{display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:2rem;margin-bottom:4rem}.pricing-card.svelte-yi5o0s.svelte-yi5o0s{position:relative;background:white;border:2px solid #e0e0e0;border-radius:16px;padding:2rem;transition:all 0.3s}.pricing-card.svelte-yi5o0s.svelte-yi5o0s:hover{transform:translateY(-4px);box-shadow:0 12px 24px rgba(0, 0, 0, 0.1)}.pricing-card.recommended.svelte-yi5o0s.svelte-yi5o0s{border-color:#10b981;box-shadow:0 8px 16px rgba(16, 185, 129, 0.1)}.recommended-badge.svelte-yi5o0s.svelte-yi5o0s{position:absolute;top:-1px;left:50%;transform:translateX(-50%);background:#10b981;color:white;padding:0.375rem 1.5rem;border-radius:0 0 12px 12px;font-size:0.875rem;font-weight:600;display:flex;align-items:center;gap:0.5rem}.plan-header.svelte-yi5o0s.svelte-yi5o0s{text-align:center;margin-bottom:2rem}.plan-header.svelte-yi5o0s h3.svelte-yi5o0s{font-size:1.5rem;margin-bottom:0.5rem}.plan-header.svelte-yi5o0s p.svelte-yi5o0s{color:#666}.plan-price.svelte-yi5o0s.svelte-yi5o0s{text-align:center;margin-bottom:1rem}.currency.svelte-yi5o0s.svelte-yi5o0s{font-size:1.5rem;color:#666;vertical-align:top}.amount.svelte-yi5o0s.svelte-yi5o0s{font-size:3.5rem;font-weight:700;color:#1a1a1a}.period.svelte-yi5o0s.svelte-yi5o0s{color:#666;font-size:1rem}.annual-pricing.svelte-yi5o0s.svelte-yi5o0s{text-align:center;font-size:0.875rem;color:#666;margin-bottom:2rem}.savings.svelte-yi5o0s.svelte-yi5o0s{color:#10b981;font-weight:600;margin-left:0.5rem}.subscribe-button.svelte-yi5o0s.svelte-yi5o0s{width:100%;padding:1rem;background:white;color:#333;border:2px solid #e0e0e0;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;transition:all 0.2s;margin-bottom:2rem}.subscribe-button.svelte-yi5o0s.svelte-yi5o0s:hover{background:#f3f4f6;border-color:#d1d5db}.subscribe-button.primary.svelte-yi5o0s.svelte-yi5o0s{background:#10b981;color:white;border-color:#10b981}.subscribe-button.primary.svelte-yi5o0s.svelte-yi5o0s:hover{background:#059669;border-color:#059669}.subscribe-button.svelte-yi5o0s.svelte-yi5o0s:disabled{opacity:0.6;cursor:not-allowed}.features-list.svelte-yi5o0s.svelte-yi5o0s{display:flex;flex-direction:column;gap:1rem}.feature.svelte-yi5o0s.svelte-yi5o0s{display:flex;align-items:center;gap:0.75rem;font-size:0.875rem}.feature.excluded.svelte-yi5o0s.svelte-yi5o0s{opacity:0.5}.check-icon{color:#10b981;flex-shrink:0}.x-icon{color:#e5e7eb;flex-shrink:0}.trust-section.svelte-yi5o0s.svelte-yi5o0s{display:flex;justify-content:center;gap:4rem;margin-bottom:4rem;padding:2rem;background:#f9fafb;border-radius:16px}.trust-badge.svelte-yi5o0s.svelte-yi5o0s{display:flex;align-items:center;gap:1rem}.trust-badge.svelte-yi5o0s h4.svelte-yi5o0s{font-size:1rem;margin-bottom:0.25rem}.trust-badge.svelte-yi5o0s p.svelte-yi5o0s{font-size:0.875rem;color:#666}.faq-section.svelte-yi5o0s.svelte-yi5o0s{max-width:900px;margin:0 auto}.faq-section.svelte-yi5o0s h2.svelte-yi5o0s{font-size:2rem;text-align:center;margin-bottom:2rem}.faq-grid.svelte-yi5o0s.svelte-yi5o0s{display:grid;grid-template-columns:repeat(auto-fit, minmax(400px, 1fr));gap:2rem}.faq-item.svelte-yi5o0s.svelte-yi5o0s{padding:1.5rem;background:white;border-radius:12px;border:1px solid #e0e0e0}.faq-item.svelte-yi5o0s h3.svelte-yi5o0s{font-size:1.125rem;margin-bottom:0.75rem;color:#333}.faq-item.svelte-yi5o0s p.svelte-yi5o0s{color:#666;line-height:1.6}@media(max-width: 768px){.pricing-header.svelte-yi5o0s h1.svelte-yi5o0s{font-size:2rem}.pricing-grid.svelte-yi5o0s.svelte-yi5o0s{grid-template-columns:1fr}.trust-section.svelte-yi5o0s.svelte-yi5o0s{flex-direction:column;gap:2rem}.faq-grid.svelte-yi5o0s.svelte-yi5o0s{grid-template-columns:1fr}}",
  map: '{"version":3,"file":"+page.svelte","sources":["+page.svelte"],"sourcesContent":["<script lang=\\"ts\\">import { goto } from \\"$app/navigation\\";\\nimport { Check, X, Zap, TrendingUp, Shield } from \\"lucide-svelte\\";\\nimport { billingApi } from \\"$lib/api/billing\\";\\nimport { isAuthenticated } from \\"$lib/api/auth\\";\\nimport { get } from \\"svelte/store\\";\\nlet isAnnual = false;\\nlet loading = false;\\nlet error = \\"\\";\\nconst plans = [\\n  {\\n    id: \\"free\\",\\n    name: \\"Free\\",\\n    monthlyPrice: 0,\\n    annualPrice: 0,\\n    description: \\"Start tracking your trades\\",\\n    features: [\\n      { text: \\"Up to 10 trades per month\\", included: true },\\n      { text: \\"Basic analytics\\", included: true },\\n      { text: \\"Trade journal\\", included: true },\\n      { text: \\"CSV export\\", included: true },\\n      { text: \\"Advanced analytics\\", included: false },\\n      { text: \\"Real-time data\\", included: false },\\n      { text: \\"AI insights\\", included: false },\\n      { text: \\"Priority support\\", included: false }\\n    ],\\n    limits: {\\n      trades_per_month: 10,\\n      journal_entries_per_month: 20,\\n      playbooks: 2\\n    },\\n    stripeProductId: null\\n  },\\n  {\\n    id: \\"pro\\",\\n    name: \\"Pro\\",\\n    monthlyPrice: 29,\\n    annualPrice: 290,\\n    description: \\"For serious traders\\",\\n    features: [\\n      { text: \\"Unlimited trades\\", included: true },\\n      { text: \\"Advanced analytics\\", included: true },\\n      { text: \\"Real-time data\\", included: true },\\n      { text: \\"Performance metrics\\", included: true },\\n      { text: \\"Multiple strategies\\", included: true },\\n      { text: \\"API access\\", included: true },\\n      { text: \\"AI insights\\", included: false },\\n      { text: \\"Priority support\\", included: false }\\n    ],\\n    limits: {\\n      trades_per_month: -1,\\n      journal_entries_per_month: -1,\\n      playbooks: 10\\n    },\\n    stripeProductId: \\"prod_pro_monthly\\",\\n    annualProductId: \\"prod_pro_annual\\",\\n    recommended: true\\n  },\\n  {\\n    id: \\"enterprise\\",\\n    name: \\"Enterprise\\",\\n    monthlyPrice: 99,\\n    annualPrice: 990,\\n    description: \\"For professional traders\\",\\n    features: [\\n      { text: \\"Everything in Pro\\", included: true },\\n      { text: \\"AI-powered insights\\", included: true },\\n      { text: \\"Advanced risk analytics\\", included: true },\\n      { text: \\"Custom integrations\\", included: true },\\n      { text: \\"White-glove onboarding\\", included: true },\\n      { text: \\"Dedicated account manager\\", included: true },\\n      { text: \\"24/7 priority support\\", included: true },\\n      { text: \\"Custom reporting\\", included: true }\\n    ],\\n    limits: {\\n      trades_per_month: -1,\\n      journal_entries_per_month: -1,\\n      playbooks: -1\\n    },\\n    stripeProductId: \\"prod_enterprise_monthly\\",\\n    annualProductId: \\"prod_enterprise_annual\\"\\n  }\\n];\\nasync function handleSubscribe(plan) {\\n  if (plan.id === \\"free\\") {\\n    if (!get(isAuthenticated)) {\\n      goto(\\"/register\\");\\n    } else {\\n      goto(\\"/dashboard\\");\\n    }\\n    return;\\n  }\\n  try {\\n    loading = true;\\n    error = \\"\\";\\n    if (!get(isAuthenticated)) {\\n      localStorage.setItem(\\"selectedPlan\\", JSON.stringify({\\n        planId: plan.id,\\n        isAnnual\\n      }));\\n      goto(\\"/register\\");\\n      return;\\n    }\\n    const productId = isAnnual ? plan.annualProductId : plan.stripeProductId;\\n    const { url } = await billingApi.createCheckoutSession({\\n      productId,\\n      successUrl: `${window.location.origin}/payment-success`,\\n      cancelUrl: `${window.location.origin}/pricing`\\n    });\\n    window.location.href = url;\\n  } catch (err) {\\n    console.error(\\"Failed to create checkout session:\\", err);\\n    error = err.message || \\"Failed to start checkout process\\";\\n  } finally {\\n    loading = false;\\n  }\\n}\\nfunction calculateSavings(monthlyPrice, annualPrice) {\\n  const yearlyFromMonthly = monthlyPrice * 12;\\n  return Math.round((yearlyFromMonthly - annualPrice) / yearlyFromMonthly * 100);\\n}\\n<\/script>\\n\\n<svelte:head>\\n\\t<title>Pricing - TradeSense</title>\\n</svelte:head>\\n\\n<div class=\\"pricing-page\\">\\n\\t<div class=\\"pricing-header\\">\\n\\t\\t<h1>Choose Your Trading Edge</h1>\\n\\t\\t<p>Start free and upgrade as you grow. No hidden fees.</p>\\n\\t\\t\\n\\t\\t<div class=\\"billing-toggle\\">\\n\\t\\t\\t<span class:active={!isAnnual}>Monthly</span>\\n\\t\\t\\t<button \\n\\t\\t\\t\\tclass=\\"toggle-switch\\"\\n\\t\\t\\t\\tclass:annual={isAnnual}\\n\\t\\t\\t\\ton:click={() => isAnnual = !isAnnual}\\n\\t\\t\\t>\\n\\t\\t\\t\\t<span class=\\"toggle-slider\\" />\\n\\t\\t\\t</button>\\n\\t\\t\\t<span class:active={isAnnual}>\\n\\t\\t\\t\\tAnnual\\n\\t\\t\\t\\t<span class=\\"save-badge\\">Save 20%</span>\\n\\t\\t\\t</span>\\n\\t\\t</div>\\n\\t</div>\\n\\t\\n\\t{#if error}\\n\\t\\t<div class=\\"error-message\\">{error}</div>\\n\\t{/if}\\n\\t\\n\\t<div class=\\"pricing-grid\\">\\n\\t\\t{#each plans as plan}\\n\\t\\t\\t<div class=\\"pricing-card\\" class:recommended={plan.recommended}>\\n\\t\\t\\t\\t{#if plan.recommended}\\n\\t\\t\\t\\t\\t<div class=\\"recommended-badge\\">\\n\\t\\t\\t\\t\\t\\t<Zap size={16} />\\n\\t\\t\\t\\t\\t\\tMost Popular\\n\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<div class=\\"plan-header\\">\\n\\t\\t\\t\\t\\t<h3>{plan.name}</h3>\\n\\t\\t\\t\\t\\t<p>{plan.description}</p>\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<div class=\\"plan-price\\">\\n\\t\\t\\t\\t\\t<span class=\\"currency\\">$</span>\\n\\t\\t\\t\\t\\t<span class=\\"amount\\">\\n\\t\\t\\t\\t\\t\\t{isAnnual \\n\\t\\t\\t\\t\\t\\t\\t? Math.floor(plan.annualPrice / 12) \\n\\t\\t\\t\\t\\t\\t\\t: plan.monthlyPrice}\\n\\t\\t\\t\\t\\t</span>\\n\\t\\t\\t\\t\\t<span class=\\"period\\">/month</span>\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t{#if isAnnual && plan.monthlyPrice > 0}\\n\\t\\t\\t\\t\\t<div class=\\"annual-pricing\\">\\n\\t\\t\\t\\t\\t\\t${plan.annualPrice} billed annually\\n\\t\\t\\t\\t\\t\\t<span class=\\"savings\\">\\n\\t\\t\\t\\t\\t\\t\\tSave {calculateSavings(plan.monthlyPrice, plan.annualPrice)}%\\n\\t\\t\\t\\t\\t\\t</span>\\n\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<button \\n\\t\\t\\t\\t\\tclass=\\"subscribe-button\\"\\n\\t\\t\\t\\t\\tclass:primary={plan.recommended}\\n\\t\\t\\t\\t\\ton:click={() => handleSubscribe(plan)}\\n\\t\\t\\t\\t\\tdisabled={loading}\\n\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t{plan.id === \'free\' ? \'Get Started\' : \'Subscribe\'}\\n\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<div class=\\"features-list\\">\\n\\t\\t\\t\\t\\t{#each plan.features as feature}\\n\\t\\t\\t\\t\\t\\t<div class=\\"feature\\" class:excluded={!feature.included}>\\n\\t\\t\\t\\t\\t\\t\\t{#if feature.included}\\n\\t\\t\\t\\t\\t\\t\\t\\t<Check size={18} class=\\"check-icon\\" />\\n\\t\\t\\t\\t\\t\\t\\t{:else}\\n\\t\\t\\t\\t\\t\\t\\t\\t<X size={18} class=\\"x-icon\\" />\\n\\t\\t\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t\\t\\t\\t<span>{feature.text}</span>\\n\\t\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\t{/each}\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t</div>\\n\\t\\t{/each}\\n\\t</div>\\n\\t\\n\\t<!-- Trust Badges -->\\n\\t<div class=\\"trust-section\\">\\n\\t\\t<div class=\\"trust-badge\\">\\n\\t\\t\\t<Shield size={24} />\\n\\t\\t\\t<div>\\n\\t\\t\\t\\t<h4>Bank-level Security</h4>\\n\\t\\t\\t\\t<p>Your data is encrypted and secure</p>\\n\\t\\t\\t</div>\\n\\t\\t</div>\\n\\t\\t<div class=\\"trust-badge\\">\\n\\t\\t\\t<TrendingUp size={24} />\\n\\t\\t\\t<div>\\n\\t\\t\\t\\t<h4>No Hidden Fees</h4>\\n\\t\\t\\t\\t<p>Cancel or change plans anytime</p>\\n\\t\\t\\t</div>\\n\\t\\t</div>\\n\\t</div>\\n\\t\\n\\t<!-- FAQ Section -->\\n\\t<div class=\\"faq-section\\">\\n\\t\\t<h2>Frequently Asked Questions</h2>\\n\\t\\t<div class=\\"faq-grid\\">\\n\\t\\t\\t<div class=\\"faq-item\\">\\n\\t\\t\\t\\t<h3>Can I change plans later?</h3>\\n\\t\\t\\t\\t<p>Yes! You can upgrade or downgrade your plan at any time. Changes take effect at the next billing cycle.</p>\\n\\t\\t\\t</div>\\n\\t\\t\\t<div class=\\"faq-item\\">\\n\\t\\t\\t\\t<h3>What payment methods do you accept?</h3>\\n\\t\\t\\t\\t<p>We accept all major credit cards, debit cards, and bank transfers through our secure payment processor, Stripe.</p>\\n\\t\\t\\t</div>\\n\\t\\t\\t<div class=\\"faq-item\\">\\n\\t\\t\\t\\t<h3>Is there a free trial?</h3>\\n\\t\\t\\t\\t<p>Our free plan lets you explore TradeSense with up to 10 trades per month. No credit card required.</p>\\n\\t\\t\\t</div>\\n\\t\\t\\t<div class=\\"faq-item\\">\\n\\t\\t\\t\\t<h3>How do I cancel my subscription?</h3>\\n\\t\\t\\t\\t<p>You can cancel anytime from your account settings. You\'ll continue to have access until the end of your billing period.</p>\\n\\t\\t\\t</div>\\n\\t\\t</div>\\n\\t</div>\\n</div>\\n\\n<style>\\n\\t.pricing-page {\\n\\t\\tmax-width: 1200px;\\n\\t\\tmargin: 0 auto;\\n\\t\\tpadding-bottom: 4rem;\\n\\t}\\n\\t\\n\\t.pricing-header {\\n\\t\\ttext-align: center;\\n\\t\\tmargin-bottom: 3rem;\\n\\t}\\n\\t\\n\\t.pricing-header h1 {\\n\\t\\tfont-size: 3rem;\\n\\t\\tmargin-bottom: 1rem;\\n\\t\\tbackground: linear-gradient(135deg, #10b981 0%, #059669 100%);\\n\\t\\t-webkit-background-clip: text;\\n\\t\\t-webkit-text-fill-color: transparent;\\n\\t}\\n\\t\\n\\t.pricing-header p {\\n\\t\\tfont-size: 1.25rem;\\n\\t\\tcolor: #666;\\n\\t\\tmargin-bottom: 2rem;\\n\\t}\\n\\t\\n\\t.billing-toggle {\\n\\t\\tdisplay: inline-flex;\\n\\t\\talign-items: center;\\n\\t\\tgap: 1rem;\\n\\t\\tpadding: 0.5rem;\\n\\t\\tbackground: #f3f4f6;\\n\\t\\tborder-radius: 100px;\\n\\t}\\n\\t\\n\\t.billing-toggle span {\\n\\t\\tpadding: 0.5rem 1rem;\\n\\t\\tcolor: #666;\\n\\t\\ttransition: color 0.2s;\\n\\t}\\n\\t\\n\\t.billing-toggle span.active {\\n\\t\\tcolor: #333;\\n\\t\\tfont-weight: 600;\\n\\t}\\n\\t\\n\\t.toggle-switch {\\n\\t\\tposition: relative;\\n\\t\\twidth: 56px;\\n\\t\\theight: 28px;\\n\\t\\tbackground: #e5e7eb;\\n\\t\\tborder: none;\\n\\t\\tborder-radius: 100px;\\n\\t\\tcursor: pointer;\\n\\t\\ttransition: background 0.3s;\\n\\t}\\n\\t\\n\\t.toggle-switch.annual {\\n\\t\\tbackground: #10b981;\\n\\t}\\n\\t\\n\\t.toggle-slider {\\n\\t\\tposition: absolute;\\n\\t\\ttop: 2px;\\n\\t\\tleft: 2px;\\n\\t\\twidth: 24px;\\n\\t\\theight: 24px;\\n\\t\\tbackground: white;\\n\\t\\tborder-radius: 50%;\\n\\t\\ttransition: transform 0.3s;\\n\\t\\tbox-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);\\n\\t}\\n\\t\\n\\t.toggle-switch.annual .toggle-slider {\\n\\t\\ttransform: translateX(28px);\\n\\t}\\n\\t\\n\\t.save-badge {\\n\\t\\tbackground: #10b981;\\n\\t\\tcolor: white;\\n\\t\\tpadding: 0.125rem 0.5rem;\\n\\t\\tborder-radius: 12px;\\n\\t\\tfont-size: 0.75rem;\\n\\t\\tmargin-left: 0.5rem;\\n\\t}\\n\\t\\n\\t.error-message {\\n\\t\\tbackground: #fee;\\n\\t\\tcolor: #dc2626;\\n\\t\\tpadding: 1rem;\\n\\t\\tborder-radius: 8px;\\n\\t\\ttext-align: center;\\n\\t\\tmargin-bottom: 2rem;\\n\\t}\\n\\t\\n\\t.pricing-grid {\\n\\t\\tdisplay: grid;\\n\\t\\tgrid-template-columns: repeat(auto-fit, minmax(320px, 1fr));\\n\\t\\tgap: 2rem;\\n\\t\\tmargin-bottom: 4rem;\\n\\t}\\n\\t\\n\\t.pricing-card {\\n\\t\\tposition: relative;\\n\\t\\tbackground: white;\\n\\t\\tborder: 2px solid #e0e0e0;\\n\\t\\tborder-radius: 16px;\\n\\t\\tpadding: 2rem;\\n\\t\\ttransition: all 0.3s;\\n\\t}\\n\\t\\n\\t.pricing-card:hover {\\n\\t\\ttransform: translateY(-4px);\\n\\t\\tbox-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);\\n\\t}\\n\\t\\n\\t.pricing-card.recommended {\\n\\t\\tborder-color: #10b981;\\n\\t\\tbox-shadow: 0 8px 16px rgba(16, 185, 129, 0.1);\\n\\t}\\n\\t\\n\\t.recommended-badge {\\n\\t\\tposition: absolute;\\n\\t\\ttop: -1px;\\n\\t\\tleft: 50%;\\n\\t\\ttransform: translateX(-50%);\\n\\t\\tbackground: #10b981;\\n\\t\\tcolor: white;\\n\\t\\tpadding: 0.375rem 1.5rem;\\n\\t\\tborder-radius: 0 0 12px 12px;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tfont-weight: 600;\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tgap: 0.5rem;\\n\\t}\\n\\t\\n\\t.plan-header {\\n\\t\\ttext-align: center;\\n\\t\\tmargin-bottom: 2rem;\\n\\t}\\n\\t\\n\\t.plan-header h3 {\\n\\t\\tfont-size: 1.5rem;\\n\\t\\tmargin-bottom: 0.5rem;\\n\\t}\\n\\t\\n\\t.plan-header p {\\n\\t\\tcolor: #666;\\n\\t}\\n\\t\\n\\t.plan-price {\\n\\t\\ttext-align: center;\\n\\t\\tmargin-bottom: 1rem;\\n\\t}\\n\\t\\n\\t.currency {\\n\\t\\tfont-size: 1.5rem;\\n\\t\\tcolor: #666;\\n\\t\\tvertical-align: top;\\n\\t}\\n\\t\\n\\t.amount {\\n\\t\\tfont-size: 3.5rem;\\n\\t\\tfont-weight: 700;\\n\\t\\tcolor: #1a1a1a;\\n\\t}\\n\\t\\n\\t.period {\\n\\t\\tcolor: #666;\\n\\t\\tfont-size: 1rem;\\n\\t}\\n\\t\\n\\t.annual-pricing {\\n\\t\\ttext-align: center;\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tcolor: #666;\\n\\t\\tmargin-bottom: 2rem;\\n\\t}\\n\\t\\n\\t.savings {\\n\\t\\tcolor: #10b981;\\n\\t\\tfont-weight: 600;\\n\\t\\tmargin-left: 0.5rem;\\n\\t}\\n\\t\\n\\t.subscribe-button {\\n\\t\\twidth: 100%;\\n\\t\\tpadding: 1rem;\\n\\t\\tbackground: white;\\n\\t\\tcolor: #333;\\n\\t\\tborder: 2px solid #e0e0e0;\\n\\t\\tborder-radius: 8px;\\n\\t\\tfont-size: 1rem;\\n\\t\\tfont-weight: 600;\\n\\t\\tcursor: pointer;\\n\\t\\ttransition: all 0.2s;\\n\\t\\tmargin-bottom: 2rem;\\n\\t}\\n\\t\\n\\t.subscribe-button:hover {\\n\\t\\tbackground: #f3f4f6;\\n\\t\\tborder-color: #d1d5db;\\n\\t}\\n\\t\\n\\t.subscribe-button.primary {\\n\\t\\tbackground: #10b981;\\n\\t\\tcolor: white;\\n\\t\\tborder-color: #10b981;\\n\\t}\\n\\t\\n\\t.subscribe-button.primary:hover {\\n\\t\\tbackground: #059669;\\n\\t\\tborder-color: #059669;\\n\\t}\\n\\t\\n\\t.subscribe-button:disabled {\\n\\t\\topacity: 0.6;\\n\\t\\tcursor: not-allowed;\\n\\t}\\n\\t\\n\\t.features-list {\\n\\t\\tdisplay: flex;\\n\\t\\tflex-direction: column;\\n\\t\\tgap: 1rem;\\n\\t}\\n\\t\\n\\t.feature {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tgap: 0.75rem;\\n\\t\\tfont-size: 0.875rem;\\n\\t}\\n\\t\\n\\t.feature.excluded {\\n\\t\\topacity: 0.5;\\n\\t}\\n\\t\\n\\t:global(.check-icon) {\\n\\t\\tcolor: #10b981;\\n\\t\\tflex-shrink: 0;\\n\\t}\\n\\t\\n\\t:global(.x-icon) {\\n\\t\\tcolor: #e5e7eb;\\n\\t\\tflex-shrink: 0;\\n\\t}\\n\\t\\n\\t/* Trust Section */\\n\\t.trust-section {\\n\\t\\tdisplay: flex;\\n\\t\\tjustify-content: center;\\n\\t\\tgap: 4rem;\\n\\t\\tmargin-bottom: 4rem;\\n\\t\\tpadding: 2rem;\\n\\t\\tbackground: #f9fafb;\\n\\t\\tborder-radius: 16px;\\n\\t}\\n\\t\\n\\t.trust-badge {\\n\\t\\tdisplay: flex;\\n\\t\\talign-items: center;\\n\\t\\tgap: 1rem;\\n\\t}\\n\\t\\n\\t.trust-badge h4 {\\n\\t\\tfont-size: 1rem;\\n\\t\\tmargin-bottom: 0.25rem;\\n\\t}\\n\\t\\n\\t.trust-badge p {\\n\\t\\tfont-size: 0.875rem;\\n\\t\\tcolor: #666;\\n\\t}\\n\\t\\n\\t/* FAQ Section */\\n\\t.faq-section {\\n\\t\\tmax-width: 900px;\\n\\t\\tmargin: 0 auto;\\n\\t}\\n\\t\\n\\t.faq-section h2 {\\n\\t\\tfont-size: 2rem;\\n\\t\\ttext-align: center;\\n\\t\\tmargin-bottom: 2rem;\\n\\t}\\n\\t\\n\\t.faq-grid {\\n\\t\\tdisplay: grid;\\n\\t\\tgrid-template-columns: repeat(auto-fit, minmax(400px, 1fr));\\n\\t\\tgap: 2rem;\\n\\t}\\n\\t\\n\\t.faq-item {\\n\\t\\tpadding: 1.5rem;\\n\\t\\tbackground: white;\\n\\t\\tborder-radius: 12px;\\n\\t\\tborder: 1px solid #e0e0e0;\\n\\t}\\n\\t\\n\\t.faq-item h3 {\\n\\t\\tfont-size: 1.125rem;\\n\\t\\tmargin-bottom: 0.75rem;\\n\\t\\tcolor: #333;\\n\\t}\\n\\t\\n\\t.faq-item p {\\n\\t\\tcolor: #666;\\n\\t\\tline-height: 1.6;\\n\\t}\\n\\t\\n\\t@media (max-width: 768px) {\\n\\t\\t.pricing-header h1 {\\n\\t\\t\\tfont-size: 2rem;\\n\\t\\t}\\n\\t\\t\\n\\t\\t.pricing-grid {\\n\\t\\t\\tgrid-template-columns: 1fr;\\n\\t\\t}\\n\\t\\t\\n\\t\\t.trust-section {\\n\\t\\t\\tflex-direction: column;\\n\\t\\t\\tgap: 2rem;\\n\\t\\t}\\n\\t\\t\\n\\t\\t.faq-grid {\\n\\t\\t\\tgrid-template-columns: 1fr;\\n\\t\\t}\\n\\t}\\n</style>"],"names":[],"mappings":"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"}'
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const plans = [
    {
      id: "free",
      name: "Free",
      monthlyPrice: 0,
      annualPrice: 0,
      description: "Start tracking your trades",
      features: [
        {
          text: "Up to 10 trades per month",
          included: true
        },
        { text: "Basic analytics", included: true },
        { text: "Trade journal", included: true },
        { text: "CSV export", included: true },
        {
          text: "Advanced analytics",
          included: false
        },
        { text: "Real-time data", included: false },
        { text: "AI insights", included: false },
        {
          text: "Priority support",
          included: false
        }
      ],
      limits: {
        trades_per_month: 10,
        journal_entries_per_month: 20,
        playbooks: 2
      },
      stripeProductId: null
    },
    {
      id: "pro",
      name: "Pro",
      monthlyPrice: 29,
      annualPrice: 290,
      description: "For serious traders",
      features: [
        { text: "Unlimited trades", included: true },
        {
          text: "Advanced analytics",
          included: true
        },
        { text: "Real-time data", included: true },
        {
          text: "Performance metrics",
          included: true
        },
        {
          text: "Multiple strategies",
          included: true
        },
        { text: "API access", included: true },
        { text: "AI insights", included: false },
        {
          text: "Priority support",
          included: false
        }
      ],
      limits: {
        trades_per_month: -1,
        journal_entries_per_month: -1,
        playbooks: 10
      },
      stripeProductId: "prod_pro_monthly",
      annualProductId: "prod_pro_annual",
      recommended: true
    },
    {
      id: "enterprise",
      name: "Enterprise",
      monthlyPrice: 99,
      annualPrice: 990,
      description: "For professional traders",
      features: [
        {
          text: "Everything in Pro",
          included: true
        },
        {
          text: "AI-powered insights",
          included: true
        },
        {
          text: "Advanced risk analytics",
          included: true
        },
        {
          text: "Custom integrations",
          included: true
        },
        {
          text: "White-glove onboarding",
          included: true
        },
        {
          text: "Dedicated account manager",
          included: true
        },
        {
          text: "24/7 priority support",
          included: true
        },
        { text: "Custom reporting", included: true }
      ],
      limits: {
        trades_per_month: -1,
        journal_entries_per_month: -1,
        playbooks: -1
      },
      stripeProductId: "prod_enterprise_monthly",
      annualProductId: "prod_enterprise_annual"
    }
  ];
  $$result.css.add(css);
  return `${$$result.head += `<!-- HEAD_svelte-6ox0qv_START -->${$$result.title = `<title>Pricing - TradeSense</title>`, ""}<!-- HEAD_svelte-6ox0qv_END -->`, ""} <div class="pricing-page svelte-yi5o0s"><div class="pricing-header svelte-yi5o0s"><h1 class="svelte-yi5o0s" data-svelte-h="svelte-awhlni">Choose Your Trading Edge</h1> <p class="svelte-yi5o0s" data-svelte-h="svelte-1u717qp">Start free and upgrade as you grow. No hidden fees.</p> <div class="billing-toggle svelte-yi5o0s"><span class="${["svelte-yi5o0s", "active"].join(" ").trim()}" data-svelte-h="svelte-7yt5b0">Monthly</span> <button class="${["toggle-switch svelte-yi5o0s", ""].join(" ").trim()}" data-svelte-h="svelte-1cm48pf"><span class="toggle-slider svelte-yi5o0s"></span></button> <span class="${["svelte-yi5o0s", ""].join(" ").trim()}" data-svelte-h="svelte-1opbk07">Annual
				<span class="save-badge svelte-yi5o0s">Save 20%</span></span></div></div> ${``} <div class="pricing-grid svelte-yi5o0s">${each(plans, (plan) => {
    return `<div class="${["pricing-card svelte-yi5o0s", plan.recommended ? "recommended" : ""].join(" ").trim()}">${plan.recommended ? `<div class="recommended-badge svelte-yi5o0s">${validate_component(Zap, "Zap").$$render($$result, { size: 16 }, {}, {})}
						Most Popular
					</div>` : ``} <div class="plan-header svelte-yi5o0s"><h3 class="svelte-yi5o0s">${escape(plan.name)}</h3> <p class="svelte-yi5o0s">${escape(plan.description)}</p></div> <div class="plan-price svelte-yi5o0s"><span class="currency svelte-yi5o0s" data-svelte-h="svelte-x0zc7w">$</span> <span class="amount svelte-yi5o0s">${escape(plan.monthlyPrice)}</span> <span class="period svelte-yi5o0s" data-svelte-h="svelte-11pr63l">/month</span></div> ${``} <button class="${["subscribe-button svelte-yi5o0s", plan.recommended ? "primary" : ""].join(" ").trim()}" ${""}>${escape(plan.id === "free" ? "Get Started" : "Subscribe")}</button> <div class="features-list svelte-yi5o0s">${each(plan.features, (feature) => {
      return `<div class="${["feature svelte-yi5o0s", !feature.included ? "excluded" : ""].join(" ").trim()}">${feature.included ? `${validate_component(Check, "Check").$$render($$result, { size: 18, class: "check-icon" }, {}, {})}` : `${validate_component(X, "X").$$render($$result, { size: 18, class: "x-icon" }, {}, {})}`} <span>${escape(feature.text)}</span> </div>`;
    })}</div> </div>`;
  })}</div>  <div class="trust-section svelte-yi5o0s"><div class="trust-badge svelte-yi5o0s">${validate_component(Shield, "Shield").$$render($$result, { size: 24 }, {}, {})} <div data-svelte-h="svelte-10m9y9r"><h4 class="svelte-yi5o0s">Bank-level Security</h4> <p class="svelte-yi5o0s">Your data is encrypted and secure</p></div></div> <div class="trust-badge svelte-yi5o0s">${validate_component(Trending_up, "TrendingUp").$$render($$result, { size: 24 }, {}, {})} <div data-svelte-h="svelte-1bwn1vz"><h4 class="svelte-yi5o0s">No Hidden Fees</h4> <p class="svelte-yi5o0s">Cancel or change plans anytime</p></div></div></div>  <div class="faq-section svelte-yi5o0s" data-svelte-h="svelte-hmkne8"><h2 class="svelte-yi5o0s">Frequently Asked Questions</h2> <div class="faq-grid svelte-yi5o0s"><div class="faq-item svelte-yi5o0s"><h3 class="svelte-yi5o0s">Can I change plans later?</h3> <p class="svelte-yi5o0s">Yes! You can upgrade or downgrade your plan at any time. Changes take effect at the next billing cycle.</p></div> <div class="faq-item svelte-yi5o0s"><h3 class="svelte-yi5o0s">What payment methods do you accept?</h3> <p class="svelte-yi5o0s">We accept all major credit cards, debit cards, and bank transfers through our secure payment processor, Stripe.</p></div> <div class="faq-item svelte-yi5o0s"><h3 class="svelte-yi5o0s">Is there a free trial?</h3> <p class="svelte-yi5o0s">Our free plan lets you explore TradeSense with up to 10 trades per month. No credit card required.</p></div> <div class="faq-item svelte-yi5o0s"><h3 class="svelte-yi5o0s">How do I cancel my subscription?</h3> <p class="svelte-yi5o0s">You can cancel anytime from your account settings. You&#39;ll continue to have access until the end of your billing period.</p></div></div></div> </div>`;
});
export {
  Page as default
};
