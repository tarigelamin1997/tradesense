import * as client_hooks from '../../../src/hooks.client.ts';


export { matchers } from './matchers.js';

export const nodes = [
	() => import('./nodes/0'),
	() => import('./nodes/1'),
	() => import('./nodes/2'),
	() => import('./nodes/3'),
	() => import('./nodes/4'),
	() => import('./nodes/5'),
	() => import('./nodes/6'),
	() => import('./nodes/7'),
	() => import('./nodes/8'),
	() => import('./nodes/9'),
	() => import('./nodes/10'),
	() => import('./nodes/11'),
	() => import('./nodes/12'),
	() => import('./nodes/13'),
	() => import('./nodes/14'),
	() => import('./nodes/15'),
	() => import('./nodes/16'),
	() => import('./nodes/17'),
	() => import('./nodes/18'),
	() => import('./nodes/19'),
	() => import('./nodes/20'),
	() => import('./nodes/21'),
	() => import('./nodes/22'),
	() => import('./nodes/23'),
	() => import('./nodes/24'),
	() => import('./nodes/25'),
	() => import('./nodes/26'),
	() => import('./nodes/27'),
	() => import('./nodes/28'),
	() => import('./nodes/29'),
	() => import('./nodes/30'),
	() => import('./nodes/31'),
	() => import('./nodes/32'),
	() => import('./nodes/33'),
	() => import('./nodes/34'),
	() => import('./nodes/35'),
	() => import('./nodes/36'),
	() => import('./nodes/37'),
	() => import('./nodes/38'),
	() => import('./nodes/39'),
	() => import('./nodes/40'),
	() => import('./nodes/41'),
	() => import('./nodes/42'),
	() => import('./nodes/43'),
	() => import('./nodes/44'),
	() => import('./nodes/45')
];

export const server_loads = [];

export const dictionary = {
		"/": [5],
		"/account/security": [6],
		"/admin": [7,[2]],
		"/admin/backup": [8,[2]],
		"/admin/experiments": [9,[2]],
		"/admin/feature-flags": [10,[2]],
		"/admin/feedback": [11,[2]],
		"/admin/users": [12,[2]],
		"/ai-insights": [13],
		"/alerts": [14],
		"/analytics": [15],
		"/billing": [16],
		"/change-password": [17],
		"/dashboards": [19],
		"/dashboards/[id]": [20],
		"/dashboard": [18],
		"/debug": [21],
		"/forgot-password": [22],
		"/journal": [23],
		"/login": [24,[3]],
		"/payment-success": [25],
		"/playbook": [26],
		"/portfolio": [27],
		"/pricing": [28],
		"/privacy": [29],
		"/register": [30,[4]],
		"/reset-password": [31],
		"/security": [32],
		"/settings": [33],
		"/settings/privacy": [34],
		"/subscription": [35],
		"/support": [36],
		"/terms": [37],
		"/test-insights": [39],
		"/test-ssr": [40],
		"/test": [38],
		"/tradelog": [41],
		"/trades": [42],
		"/trades/new": [43],
		"/upload": [44],
		"/verify-email": [45]
	};

export const hooks = {
	handleError: client_hooks.handleError || (({ error }) => { console.error(error) }),
	init: client_hooks.init,
	reroute: (() => {}),
	transport: {}
};

export const decoders = Object.fromEntries(Object.entries(hooks.transport).map(([k, v]) => [k, v.decode]));

export const hash = false;

export const decode = (type, value) => decoders[type](value);

export { default as root } from '../root.svelte';