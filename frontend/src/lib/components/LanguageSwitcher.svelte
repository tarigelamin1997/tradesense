<script lang="ts">
  import { locale } from 'svelte-i18n';
  import { languages } from '$lib/i18n/languages';
  import { saveLanguagePreference } from '$lib/i18n';
  
  let isOpen = false;
  
  $: currentLanguage = languages[$locale] || languages.en;
  
  function handleLanguageChange(langCode: string) {
    locale.set(langCode);
    saveLanguagePreference(langCode);
    isOpen = false;
    
    // Update HTML lang attribute
    if (typeof document !== 'undefined') {
      document.documentElement.lang = langCode;
    }
  }
  
  function toggleDropdown() {
    isOpen = !isOpen;
  }
  
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.language-switcher')) {
      isOpen = false;
    }
  }
</script>

<svelte:window on:click={handleClickOutside} />

<div class="language-switcher">
  <button
    class="language-button"
    on:click={toggleDropdown}
    aria-label="Select language"
    aria-expanded={isOpen}
    aria-haspopup="listbox"
  >
    <span class="flag">{currentLanguage.flag}</span>
    <span class="name">{currentLanguage.nativeName}</span>
    <svg
      class="chevron"
      class:rotated={isOpen}
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
    >
      <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
  </button>
  
  {#if isOpen}
    <ul class="language-dropdown" role="listbox">
      {#each Object.values(languages) as language}
        <li>
          <button
            class="language-option"
            class:active={language.code === $locale}
            on:click={() => handleLanguageChange(language.code)}
            role="option"
            aria-selected={language.code === $locale}
          >
            <span class="flag">{language.flag}</span>
            <span class="name">{language.nativeName}</span>
            {#if language.code === $locale}
              <svg
                class="check"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            {/if}
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .language-switcher {
    position: relative;
  }
  
  .language-button {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: 1px solid var(--color-border);
    border-radius: 0.375rem;
    color: var(--color-text);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all 150ms;
  }
  
  .language-button:hover {
    background: var(--color-surface);
  }
  
  .flag {
    font-size: 1.25rem;
    line-height: 1;
  }
  
  .name {
    min-width: 80px;
    text-align: left;
  }
  
  .chevron {
    transition: transform 150ms;
  }
  
  .chevron.rotated {
    transform: rotate(180deg);
  }
  
  .language-dropdown {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    background: var(--color-background);
    border: 1px solid var(--color-border);
    border-radius: 0.375rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    list-style: none;
    margin: 0;
    padding: 0.25rem;
    min-width: 180px;
    z-index: 50;
  }
  
  .language-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: none;
    color: var(--color-text);
    font-size: 0.875rem;
    text-align: left;
    cursor: pointer;
    transition: background 150ms;
    border-radius: 0.25rem;
  }
  
  .language-option:hover {
    background: var(--color-surface);
  }
  
  .language-option.active {
    background: var(--color-primary);
    color: white;
  }
  
  .check {
    margin-left: auto;
  }
  
  /* Dark mode adjustments */
  :global(.dark) .language-dropdown {
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
  }
</style>