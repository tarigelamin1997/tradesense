module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    project: './tsconfig.json',
    extraFileExtensions: ['.svelte']
  },
  env: {
    browser: true,
    es2017: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'plugin:svelte/recommended',
    'prettier'
  ],
  plugins: ['@typescript-eslint'],
  overrides: [
    {
      files: ['*.svelte'],
      parser: 'svelte-eslint-parser',
      parserOptions: {
        parser: '@typescript-eslint/parser'
      }
    }
  ],
  settings: {
    'svelte3/typescript': () => require('typescript')
  },
  rules: {
    // TypeScript rules
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-non-null-assertion': 'warn',
    '@typescript-eslint/strict-boolean-expressions': 'off',
    
    // General rules
    'no-console': ['warn', { allow: ['warn', 'error'] }],
    'no-debugger': 'error',
    'prefer-const': 'error',
    'no-var': 'error',
    
    // Svelte specific
    'svelte/no-at-html-tags': 'error',
    'svelte/no-target-blank': 'error',
    'svelte/no-unused-svelte-ignore': 'error',
    'svelte/no-reactive-functions': 'error',
    'svelte/no-reactive-literals': 'error',
    
    // Accessibility
    'svelte/valid-compile': 'error',
    'svelte/no-dom-manipulating': 'warn'
  },
  ignorePatterns: [
    '*.cjs',
    'node_modules',
    'build',
    '.svelte-kit',
    'dist',
    'coverage'
  ]
};