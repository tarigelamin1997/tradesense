import { c as create_ssr_component, a as add_attribute, b as escape, v as validate_component, e as each, m as missing_component } from "../../../chunks/ssr.js";
import { S as Send, P as Phone, M as Map_pin } from "../../../chunks/send.js";
import { M as Mail } from "../../../chunks/mail.js";
import { M as Message_square } from "../../../chunks/message-square.js";
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  let formData = {
    name: "",
    email: "",
    subject: ""
  };
  const contactInfo = [
    {
      icon: Mail,
      title: "Email",
      content: "support@tradesense.com",
      link: "mailto:support@tradesense.com"
    },
    {
      icon: Message_square,
      title: "Live Chat",
      content: "Available Mon-Fri, 9AM-6PM EST",
      action: () => {
      }
    },
    {
      icon: Phone,
      title: "Phone",
      content: "+1 (555) 123-4567",
      link: "tel:+15551234567"
    },
    {
      icon: Map_pin,
      title: "Office",
      content: "123 Trading Street, New York, NY 10001",
      link: "https://maps.google.com"
    }
  ];
  return `${$$result.head += `<!-- HEAD_svelte-1jmteu2_START -->${$$result.title = `<title>Contact Us - TradeSense</title>`, ""}<meta name="description" content="Get in touch with the TradeSense team. We're here to help with any questions about our trading analytics platform."><!-- HEAD_svelte-1jmteu2_END -->`, ""} <div class="min-h-screen bg-gray-50 dark:bg-gray-900"> <section class="pt-20 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-gray-50 dark:from-gray-800 dark:to-gray-900" data-svelte-h="svelte-s8gidv"><div class="max-w-7xl mx-auto text-center"><h1 class="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">Get in Touch</h1> <p class="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">Have questions about TradeSense? We&#39;re here to help. Reach out to our team and we&#39;ll get back to you as soon as possible.</p></div></section>  <section class="py-16 px-4 sm:px-6 lg:px-8"><div class="max-w-7xl mx-auto"><div class="grid lg:grid-cols-3 gap-12"> <div class="lg:col-span-2"><div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-8"><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6" data-svelte-h="svelte-vezdez">Send us a Message</h2> ${``} ${``} <form class="space-y-6"><div class="grid md:grid-cols-2 gap-6"><div><label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-z0lwcl">Your Name</label> <input id="name" type="text" required class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"${add_attribute("value", formData.name, 0)}></div> <div><label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1vs8mhw">Email Address</label> <input id="email" type="email" required class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"${add_attribute("value", formData.email, 0)}></div></div> <div><label for="subject" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-4rbqji">Subject</label> <input id="subject" type="text" required class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"${add_attribute("value", formData.subject, 0)}></div> <div><label for="message" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2" data-svelte-h="svelte-1clmnv8">Message</label> <textarea id="message" required rows="6" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none">${escape("")}</textarea></div> <button type="submit" ${""} class="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">${`${validate_component(Send, "Send").$$render($$result, { class: "h-5 w-5" }, {}, {})}
									Send Message`}</button></form></div></div>  <div class="space-y-6"><div><h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6" data-svelte-h="svelte-1ekxe4l">Other Ways to Reach Us</h2> <div class="space-y-4">${each(contactInfo, (info) => {
    return `<div class="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm"><div class="flex items-start gap-4"><div class="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">${validate_component(info.icon || missing_component, "svelte:component").$$render(
      $$result,
      {
        class: "h-6 w-6 text-blue-600 dark:text-blue-400"
      },
      {},
      {}
    )}</div> <div><h3 class="font-semibold text-gray-900 dark:text-white mb-1">${escape(info.title)}</h3> ${info.link ? `<a${add_attribute("href", info.link, 0)} class="text-blue-600 dark:text-blue-400 hover:underline"${add_attribute("target", info.link.startsWith("http") ? "_blank" : void 0, 0)}${add_attribute(
      "rel",
      info.link.startsWith("http") ? "noopener noreferrer" : void 0,
      0
    )}>${escape(info.content)} </a>` : `${info.action ? `<button class="text-blue-600 dark:text-blue-400 hover:underline text-left">${escape(info.content)} </button>` : `<p class="text-gray-600 dark:text-gray-400">${escape(info.content)} </p>`}`} </div></div> </div>`;
  })}</div></div>  <div class="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6" data-svelte-h="svelte-1fxyz42"><h3 class="font-semibold text-gray-900 dark:text-white mb-2">Looking for quick answers?</h3> <p class="text-gray-600 dark:text-gray-400 mb-4">Check out our frequently asked questions for instant help.</p> <a href="/support/kb" class="inline-flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:underline font-medium">Visit Knowledge Base →</a></div></div></div></div></section></div>`;
});
export {
  Page as default
};
