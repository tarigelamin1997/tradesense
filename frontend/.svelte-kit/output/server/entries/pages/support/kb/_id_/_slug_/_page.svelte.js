import { c as create_ssr_component, v as validate_component, b as escape, e as each, a as add_attribute } from "../../../../../../chunks/ssr.js";
import "@sveltejs/kit/internal";
import "../../../../../../chunks/exports.js";
import "../../../../../../chunks/state.svelte.js";
import { B as Breadcrumb } from "../../../../../../chunks/Breadcrumb.js";
import { A as Arrow_left } from "../../../../../../chunks/arrow-left.js";
import { C as Clock } from "../../../../../../chunks/clock.js";
import { B as Book_open } from "../../../../../../chunks/book-open.js";
import { S as Share_2, P as Printer, T as Thumbs_down } from "../../../../../../chunks/thumbs-down.js";
import { T as Thumbs_up } from "../../../../../../chunks/thumbs-up.js";
import { C as Chevron_right } from "../../../../../../chunks/chevron-right.js";
const css = {
  code: "@media print{header.svelte-1pye1ze button.svelte-1pye1ze,header.svelte-1pye1ze div.svelte-1pye1ze,div.svelte-1pye1ze.svelte-1pye1ze:has(> button),section.svelte-1pye1ze.svelte-1pye1ze:last-child{display:none !important}article.svelte-1pye1ze.svelte-1pye1ze{padding:0 !important}}",
  map: `{"version":3,"file":"+page.svelte","sources":["+page.svelte"],"sourcesContent":["<script lang=\\"ts\\">\\"use strict\\";\\nimport { page } from \\"$app/stores\\";\\nimport {\\n  ArrowLeft,\\n  Clock,\\n  BookOpen,\\n  ThumbsUp,\\n  ThumbsDown,\\n  Share2,\\n  Printer,\\n  ChevronRight\\n} from \\"lucide-svelte\\";\\nimport { goto } from \\"$app/navigation\\";\\nimport Breadcrumb from \\"$lib/components/ui/Breadcrumb.svelte\\";\\nconst article = {\\n  id: \\"1\\",\\n  title: \\"Getting Started with TradeSense\\",\\n  category: \\"Getting Started\\",\\n  readTime: \\"5 min\\",\\n  lastUpdated: /* @__PURE__ */ new Date(\\"2024-01-15\\"),\\n  author: \\"TradeSense Team\\",\\n  content: \`\\n\\t\\t\\t<h2>Welcome to TradeSense</h2>\\n\\t\\t\\t<p>TradeSense is a comprehensive trading journal and analytics platform designed to help you track, analyze, and improve your trading performance. This guide will walk you through the basics of getting started with our platform.</p>\\n\\t\\t\\t\\n\\t\\t\\t<h3>1. Setting Up Your Account</h3>\\n\\t\\t\\t<p>After signing up, you'll need to complete a few steps to set up your account:</p>\\n\\t\\t\\t<ul>\\n\\t\\t\\t\\t<li><strong>Complete your profile:</strong> Add your name and trading preferences</li>\\n\\t\\t\\t\\t<li><strong>Choose your subscription:</strong> Select a plan that fits your needs</li>\\n\\t\\t\\t\\t<li><strong>Set your timezone:</strong> Ensure accurate timestamps for your trades</li>\\n\\t\\t\\t\\t<li><strong>Configure your preferences:</strong> Customize how you want to use TradeSense</li>\\n\\t\\t\\t</ul>\\n\\t\\t\\t\\n\\t\\t\\t<h3>2. Adding Your First Trade</h3>\\n\\t\\t\\t<p>There are several ways to add trades to TradeSense:</p>\\n\\t\\t\\t<ol>\\n\\t\\t\\t\\t<li><strong>Manual Entry:</strong> Click \\"Add Trade\\" and fill in the details</li>\\n\\t\\t\\t\\t<li><strong>CSV Import:</strong> Upload a CSV file with your trading history</li>\\n\\t\\t\\t\\t<li><strong>Broker Integration:</strong> Connect your broker for automatic imports</li>\\n\\t\\t\\t</ol>\\n\\t\\t\\t\\n\\t\\t\\t<h3>3. Understanding Your Dashboard</h3>\\n\\t\\t\\t<p>Your dashboard provides a comprehensive overview of your trading performance:</p>\\n\\t\\t\\t<ul>\\n\\t\\t\\t\\t<li><strong>Performance Summary:</strong> Key metrics like win rate and profit factor</li>\\n\\t\\t\\t\\t<li><strong>P&L Chart:</strong> Visual representation of your profit/loss over time</li>\\n\\t\\t\\t\\t<li><strong>Recent Trades:</strong> Quick access to your latest trading activity</li>\\n\\t\\t\\t\\t<li><strong>AI Insights:</strong> Personalized recommendations based on your trading patterns</li>\\n\\t\\t\\t</ul>\\n\\t\\t\\t\\n\\t\\t\\t<h3>4. Exploring Analytics</h3>\\n\\t\\t\\t<p>The Analytics section offers deep insights into your trading:</p>\\n\\t\\t\\t<ul>\\n\\t\\t\\t\\t<li><strong>Performance Metrics:</strong> Detailed statistics about your trading</li>\\n\\t\\t\\t\\t<li><strong>Trade Analysis:</strong> Breakdown by symbol, strategy, and time</li>\\n\\t\\t\\t\\t<li><strong>Risk Management:</strong> Analysis of your risk/reward ratios</li>\\n\\t\\t\\t\\t<li><strong>Custom Reports:</strong> Create tailored reports for your needs</li>\\n\\t\\t\\t</ul>\\n\\t\\t\\t\\n\\t\\t\\t<h3>5. Next Steps</h3>\\n\\t\\t\\t<p>Now that you're familiar with the basics, here are some recommended next steps:</p>\\n\\t\\t\\t<ul>\\n\\t\\t\\t\\t<li>Import your historical trades to see your full trading history</li>\\n\\t\\t\\t\\t<li>Set up trade tags and categories for better organization</li>\\n\\t\\t\\t\\t<li>Explore the AI Insights to identify patterns in your trading</li>\\n\\t\\t\\t\\t<li>Create custom dashboards to focus on metrics that matter to you</li>\\n\\t\\t\\t</ul>\\n\\t\\t\\t\\n\\t\\t\\t<div class=\\"bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg mt-6\\">\\n\\t\\t\\t\\t<p class=\\"text-blue-700 dark:text-blue-400\\"><strong>Pro Tip:</strong> Start by importing at least 20-30 trades to get meaningful analytics and AI insights. The more data you provide, the better our algorithms can help you improve.</p>\\n\\t\\t\\t</div>\\n\\t\\t\`,\\n  relatedArticles: [\\n    { id: \\"2\\", title: \\"Your First Trade Import\\", slug: \\"your-first-trade-import\\" },\\n    { id: \\"3\\", title: \\"Dashboard Overview\\", slug: \\"dashboard-overview\\" },\\n    { id: \\"4\\", title: \\"Understanding Win Rate and Profit Factor\\", slug: \\"understanding-win-rate\\" }\\n  ]\\n};\\nlet helpful = null;\\nfunction handleHelpful(value) {\\n  helpful = value;\\n}\\nfunction shareArticle() {\\n  if (navigator.share) {\\n    navigator.share({\\n      title: article.title,\\n      url: window.location.href\\n    });\\n  } else {\\n    navigator.clipboard.writeText(window.location.href);\\n  }\\n}\\nfunction printArticle() {\\n  window.print();\\n}\\n<\/script>\\n\\n<svelte:head>\\n\\t<title>{article.title} - TradeSense Knowledge Base</title>\\n\\t<meta name=\\"description\\" content={article.content.substring(0, 150).replace(/<[^>]*>/g, '')} />\\n</svelte:head>\\n\\n<div class=\\"min-h-screen bg-white dark:bg-gray-900\\">\\n\\t<!-- Breadcrumb -->\\n\\t<div class=\\"border-b border-gray-200 dark:border-gray-800\\">\\n\\t\\t<div class=\\"max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4\\">\\n\\t\\t\\t<Breadcrumb items={[\\n\\t\\t\\t\\t{ label: 'Support', href: '/support' },\\n\\t\\t\\t\\t{ label: 'Knowledge Base', href: '/support/kb' },\\n\\t\\t\\t\\t{ label: article.category, href: \`/support/kb?category=\${article.category}\` },\\n\\t\\t\\t\\t{ label: article.title }\\n\\t\\t\\t]} />\\n\\t\\t</div>\\n\\t</div>\\n\\n\\t<!-- Article Content -->\\n\\t<article class=\\"py-8 px-4 sm:px-6 lg:px-8\\">\\n\\t\\t<div class=\\"max-w-4xl mx-auto\\">\\n\\t\\t\\t<!-- Header -->\\n\\t\\t\\t<header class=\\"mb-8\\">\\n\\t\\t\\t\\t<button\\n\\t\\t\\t\\t\\ton:click={() => goto('/support/kb')}\\n\\t\\t\\t\\t\\tclass=\\"flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mb-4\\"\\n\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t<ArrowLeft class=\\"h-4 w-4\\" />\\n\\t\\t\\t\\t\\tBack to Knowledge Base\\n\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<h1 class=\\"text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4\\">\\n\\t\\t\\t\\t\\t{article.title}\\n\\t\\t\\t\\t</h1>\\n\\t\\t\\t\\t\\n\\t\\t\\t\\t<div class=\\"flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400\\">\\n\\t\\t\\t\\t\\t<div class=\\"flex items-center gap-1\\">\\n\\t\\t\\t\\t\\t\\t<Clock class=\\"h-4 w-4\\" />\\n\\t\\t\\t\\t\\t\\t<span>{article.readTime} read</span>\\n\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\t<div class=\\"flex items-center gap-1\\">\\n\\t\\t\\t\\t\\t\\t<BookOpen class=\\"h-4 w-4\\" />\\n\\t\\t\\t\\t\\t\\t<span>{article.category}</span>\\n\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\t<div>\\n\\t\\t\\t\\t\\t\\tLast updated: {article.lastUpdated.toLocaleDateString()}\\n\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t</header>\\n\\n\\t\\t\\t<!-- Actions -->\\n\\t\\t\\t<div class=\\"flex items-center gap-4 mb-8 pb-8 border-b border-gray-200 dark:border-gray-800\\">\\n\\t\\t\\t\\t<button\\n\\t\\t\\t\\t\\ton:click={shareArticle}\\n\\t\\t\\t\\t\\tclass=\\"flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white\\"\\n\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t<Share2 class=\\"h-4 w-4\\" />\\n\\t\\t\\t\\t\\tShare\\n\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t<button\\n\\t\\t\\t\\t\\ton:click={printArticle}\\n\\t\\t\\t\\t\\tclass=\\"flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white\\"\\n\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t<Printer class=\\"h-4 w-4\\" />\\n\\t\\t\\t\\t\\tPrint\\n\\t\\t\\t\\t</button>\\n\\t\\t\\t</div>\\n\\n\\t\\t\\t<!-- Content -->\\n\\t\\t\\t<div class=\\"prose prose-lg dark:prose-invert max-w-none mb-12\\">\\n\\t\\t\\t\\t{@html article.content}\\n\\t\\t\\t</div>\\n\\n\\t\\t\\t<!-- Feedback -->\\n\\t\\t\\t<div class=\\"border-t border-gray-200 dark:border-gray-800 pt-8 mb-12\\">\\n\\t\\t\\t\\t<div class=\\"text-center\\">\\n\\t\\t\\t\\t\\t<h3 class=\\"text-lg font-semibold text-gray-900 dark:text-white mb-4\\">\\n\\t\\t\\t\\t\\t\\tWas this article helpful?\\n\\t\\t\\t\\t\\t</h3>\\n\\t\\t\\t\\t\\t<div class=\\"flex items-center justify-center gap-4\\">\\n\\t\\t\\t\\t\\t\\t<button\\n\\t\\t\\t\\t\\t\\t\\ton:click={() => handleHelpful(true)}\\n\\t\\t\\t\\t\\t\\t\\tclass=\\"flex items-center gap-2 px-4 py-2 rounded-lg transition-colors\\n\\t\\t\\t\\t\\t\\t\\t\\t{helpful === true \\n\\t\\t\\t\\t\\t\\t\\t\\t\\t? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' \\n\\t\\t\\t\\t\\t\\t\\t\\t\\t: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}\\"\\n\\t\\t\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t\\t\\t<ThumbsUp class=\\"h-5 w-5\\" />\\n\\t\\t\\t\\t\\t\\t\\tYes\\n\\t\\t\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t\\t\\t<button\\n\\t\\t\\t\\t\\t\\t\\ton:click={() => handleHelpful(false)}\\n\\t\\t\\t\\t\\t\\t\\tclass=\\"flex items-center gap-2 px-4 py-2 rounded-lg transition-colors\\n\\t\\t\\t\\t\\t\\t\\t\\t{helpful === false \\n\\t\\t\\t\\t\\t\\t\\t\\t\\t? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' \\n\\t\\t\\t\\t\\t\\t\\t\\t\\t: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'}\\"\\n\\t\\t\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t\\t\\t<ThumbsDown class=\\"h-5 w-5\\" />\\n\\t\\t\\t\\t\\t\\t\\tNo\\n\\t\\t\\t\\t\\t\\t</button>\\n\\t\\t\\t\\t\\t</div>\\n\\t\\t\\t\\t\\t{#if helpful !== null}\\n\\t\\t\\t\\t\\t\\t<p class=\\"mt-4 text-gray-600 dark:text-gray-400\\">\\n\\t\\t\\t\\t\\t\\t\\tThank you for your feedback!\\n\\t\\t\\t\\t\\t\\t</p>\\n\\t\\t\\t\\t\\t{/if}\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t</div>\\n\\n\\t\\t\\t<!-- Related Articles -->\\n\\t\\t\\t<div class=\\"bg-gray-50 dark:bg-gray-800 rounded-lg p-6\\">\\n\\t\\t\\t\\t<h3 class=\\"text-lg font-semibold text-gray-900 dark:text-white mb-4\\">\\n\\t\\t\\t\\t\\tRelated Articles\\n\\t\\t\\t\\t</h3>\\n\\t\\t\\t\\t<div class=\\"space-y-3\\">\\n\\t\\t\\t\\t\\t{#each article.relatedArticles as related}\\n\\t\\t\\t\\t\\t\\t<a\\n\\t\\t\\t\\t\\t\\t\\thref=\\"/support/kb/{related.id}/{related.slug}\\"\\n\\t\\t\\t\\t\\t\\t\\tclass=\\"flex items-center justify-between p-3 bg-white dark:bg-gray-900 rounded-lg hover:shadow-sm transition-shadow group\\"\\n\\t\\t\\t\\t\\t\\t>\\n\\t\\t\\t\\t\\t\\t\\t<span class=\\"text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400\\">\\n\\t\\t\\t\\t\\t\\t\\t\\t{related.title}\\n\\t\\t\\t\\t\\t\\t\\t</span>\\n\\t\\t\\t\\t\\t\\t\\t<ChevronRight class=\\"h-4 w-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400\\" />\\n\\t\\t\\t\\t\\t\\t</a>\\n\\t\\t\\t\\t\\t{/each}\\n\\t\\t\\t\\t</div>\\n\\t\\t\\t</div>\\n\\t\\t</div>\\n\\t</article>\\n\\n\\t<!-- Contact Support -->\\n\\t<section class=\\"py-8 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20\\">\\n\\t\\t<div class=\\"max-w-4xl mx-auto text-center\\">\\n\\t\\t\\t<h3 class=\\"text-lg font-semibold text-gray-900 dark:text-white mb-2\\">\\n\\t\\t\\t\\tNeed more help?\\n\\t\\t\\t</h3>\\n\\t\\t\\t<p class=\\"text-gray-600 dark:text-gray-400 mb-4\\">\\n\\t\\t\\t\\tContact our support team for personalized assistance.\\n\\t\\t\\t</p>\\n\\t\\t\\t<a\\n\\t\\t\\t\\thref=\\"/contact\\"\\n\\t\\t\\t\\tclass=\\"inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium\\"\\n\\t\\t\\t>\\n\\t\\t\\t\\tContact Support\\n\\t\\t\\t</a>\\n\\t\\t</div>\\n\\t</section>\\n</div>\\n\\n<style>\\n\\t@media print {\\n\\t\\t/* Hide non-content elements when printing */\\n\\t\\tnav, header button, header div, \\n\\t\\tdiv:has(> button), \\n\\t\\tsection:last-child {\\n\\t\\t\\tdisplay: none !important;\\n\\t\\t}\\n\\t\\t\\n\\t\\tarticle {\\n\\t\\t\\tpadding: 0 !important;\\n\\t\\t}\\n\\t}\\n</style>"],"names":[],"mappings":"AAyPC,OAAO,KAAM,CAEP,qBAAM,CAAC,qBAAM,CAAE,qBAAM,CAAC,kBAAG,CAC9B,iCAAG,KAAK,CAAC,CAAC,MAAM,CAAC,CACjB,qCAAO,WAAY,CAClB,OAAO,CAAE,IAAI,CAAC,UACf,CAEA,qCAAQ,CACP,OAAO,CAAE,CAAC,CAAC,UACZ,CACD"}`
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  const article = {
    title: "Getting Started with TradeSense",
    category: "Getting Started",
    readTime: "5 min",
    lastUpdated: /* @__PURE__ */ new Date("2024-01-15"),
    content: `
			<h2>Welcome to TradeSense</h2>
			<p>TradeSense is a comprehensive trading journal and analytics platform designed to help you track, analyze, and improve your trading performance. This guide will walk you through the basics of getting started with our platform.</p>
			
			<h3>1. Setting Up Your Account</h3>
			<p>After signing up, you'll need to complete a few steps to set up your account:</p>
			<ul>
				<li><strong>Complete your profile:</strong> Add your name and trading preferences</li>
				<li><strong>Choose your subscription:</strong> Select a plan that fits your needs</li>
				<li><strong>Set your timezone:</strong> Ensure accurate timestamps for your trades</li>
				<li><strong>Configure your preferences:</strong> Customize how you want to use TradeSense</li>
			</ul>
			
			<h3>2. Adding Your First Trade</h3>
			<p>There are several ways to add trades to TradeSense:</p>
			<ol>
				<li><strong>Manual Entry:</strong> Click "Add Trade" and fill in the details</li>
				<li><strong>CSV Import:</strong> Upload a CSV file with your trading history</li>
				<li><strong>Broker Integration:</strong> Connect your broker for automatic imports</li>
			</ol>
			
			<h3>3. Understanding Your Dashboard</h3>
			<p>Your dashboard provides a comprehensive overview of your trading performance:</p>
			<ul>
				<li><strong>Performance Summary:</strong> Key metrics like win rate and profit factor</li>
				<li><strong>P&L Chart:</strong> Visual representation of your profit/loss over time</li>
				<li><strong>Recent Trades:</strong> Quick access to your latest trading activity</li>
				<li><strong>AI Insights:</strong> Personalized recommendations based on your trading patterns</li>
			</ul>
			
			<h3>4. Exploring Analytics</h3>
			<p>The Analytics section offers deep insights into your trading:</p>
			<ul>
				<li><strong>Performance Metrics:</strong> Detailed statistics about your trading</li>
				<li><strong>Trade Analysis:</strong> Breakdown by symbol, strategy, and time</li>
				<li><strong>Risk Management:</strong> Analysis of your risk/reward ratios</li>
				<li><strong>Custom Reports:</strong> Create tailored reports for your needs</li>
			</ul>
			
			<h3>5. Next Steps</h3>
			<p>Now that you're familiar with the basics, here are some recommended next steps:</p>
			<ul>
				<li>Import your historical trades to see your full trading history</li>
				<li>Set up trade tags and categories for better organization</li>
				<li>Explore the AI Insights to identify patterns in your trading</li>
				<li>Create custom dashboards to focus on metrics that matter to you</li>
			</ul>
			
			<div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg mt-6">
				<p class="text-blue-700 dark:text-blue-400"><strong>Pro Tip:</strong> Start by importing at least 20-30 trades to get meaningful analytics and AI insights. The more data you provide, the better our algorithms can help you improve.</p>
			</div>
		`,
    relatedArticles: [
      {
        id: "2",
        title: "Your First Trade Import",
        slug: "your-first-trade-import"
      },
      {
        id: "3",
        title: "Dashboard Overview",
        slug: "dashboard-overview"
      },
      {
        id: "4",
        title: "Understanding Win Rate and Profit Factor",
        slug: "understanding-win-rate"
      }
    ]
  };
  $$result.css.add(css);
  return `${$$result.head += `<!-- HEAD_svelte-1il6q1s_START -->${$$result.title = `<title>${escape(article.title)} - TradeSense Knowledge Base</title>`, ""}<meta name="description"${add_attribute("content", article.content.substring(0, 150).replace(/<[^>]*>/g, ""), 0)}><!-- HEAD_svelte-1il6q1s_END -->`, ""} <div class="min-h-screen bg-white dark:bg-gray-900 svelte-1pye1ze"> <div class="border-b border-gray-200 dark:border-gray-800 svelte-1pye1ze"><div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 svelte-1pye1ze">${validate_component(Breadcrumb, "Breadcrumb").$$render(
    $$result,
    {
      items: [
        { label: "Support", href: "/support" },
        {
          label: "Knowledge Base",
          href: "/support/kb"
        },
        {
          label: article.category,
          href: `/support/kb?category=${article.category}`
        },
        { label: article.title }
      ]
    },
    {},
    {}
  )}</div></div>  <article class="py-8 px-4 sm:px-6 lg:px-8 svelte-1pye1ze"><div class="max-w-4xl mx-auto svelte-1pye1ze"> <header class="mb-8 svelte-1pye1ze"><button class="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline mb-4 svelte-1pye1ze">${validate_component(Arrow_left, "ArrowLeft").$$render($$result, { class: "h-4 w-4" }, {}, {})}
					Back to Knowledge Base</button> <h1 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">${escape(article.title)}</h1> <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600 dark:text-gray-400 svelte-1pye1ze"><div class="flex items-center gap-1 svelte-1pye1ze">${validate_component(Clock, "Clock").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span>${escape(article.readTime)} read</span></div> <div class="flex items-center gap-1 svelte-1pye1ze">${validate_component(Book_open, "BookOpen").$$render($$result, { class: "h-4 w-4" }, {}, {})} <span>${escape(article.category)}</span></div> <div class="svelte-1pye1ze">Last updated: ${escape(article.lastUpdated.toLocaleDateString())}</div></div></header>  <div class="flex items-center gap-4 mb-8 pb-8 border-b border-gray-200 dark:border-gray-800 svelte-1pye1ze"><button class="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">${validate_component(Share_2, "Share2").$$render($$result, { class: "h-4 w-4" }, {}, {})}
					Share</button> <button class="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">${validate_component(Printer, "Printer").$$render($$result, { class: "h-4 w-4" }, {}, {})}
					Print</button></div>  <div class="prose prose-lg dark:prose-invert max-w-none mb-12 svelte-1pye1ze"><!-- HTML_TAG_START -->${article.content}<!-- HTML_TAG_END --></div>  <div class="border-t border-gray-200 dark:border-gray-800 pt-8 mb-12 svelte-1pye1ze"><div class="text-center svelte-1pye1ze"><h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-u879j0">Was this article helpful?</h3> <div class="flex items-center justify-center gap-4 svelte-1pye1ze"><button class="${"flex items-center gap-2 px-4 py-2 rounded-lg transition-colors " + escape(
    "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700",
    true
  )}">${validate_component(Thumbs_up, "ThumbsUp").$$render($$result, { class: "h-5 w-5" }, {}, {})}
							Yes</button> <button class="${"flex items-center gap-2 px-4 py-2 rounded-lg transition-colors " + escape(
    "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700",
    true
  )}">${validate_component(Thumbs_down, "ThumbsDown").$$render($$result, { class: "h-5 w-5" }, {}, {})}
							No</button></div> ${``}</div></div>  <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-6 svelte-1pye1ze"><h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4" data-svelte-h="svelte-mnhe1u">Related Articles</h3> <div class="space-y-3 svelte-1pye1ze">${each(article.relatedArticles, (related) => {
    return `<a href="${"/support/kb/" + escape(related.id, true) + "/" + escape(related.slug, true)}" class="flex items-center justify-between p-3 bg-white dark:bg-gray-900 rounded-lg hover:shadow-sm transition-shadow group"><span class="text-gray-700 dark:text-gray-300 group-hover:text-blue-600 dark:group-hover:text-blue-400">${escape(related.title)}</span> ${validate_component(Chevron_right, "ChevronRight").$$render(
      $$result,
      {
        class: "h-4 w-4 text-gray-400 group-hover:text-blue-600 dark:group-hover:text-blue-400"
      },
      {},
      {}
    )} </a>`;
  })}</div></div></div></article>  <section class="py-8 px-4 sm:px-6 lg:px-8 bg-blue-50 dark:bg-blue-900/20 svelte-1pye1ze" data-svelte-h="svelte-otzdvt"><div class="max-w-4xl mx-auto text-center svelte-1pye1ze"><h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">Need more help?</h3> <p class="text-gray-600 dark:text-gray-400 mb-4">Contact our support team for personalized assistance.</p> <a href="/contact" class="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium">Contact Support</a></div></section> </div>`;
});
export {
  Page as default
};
