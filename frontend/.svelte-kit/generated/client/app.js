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
	() => import('./nodes/29')
];

export const server_loads = [];

export const dictionary = {
		"/": [4],
		"/analytics": [5],
		"/billing": [6],
		"/change-password": [7],
		"/dashboard": [8],
		"/debug": [9],
		"/forgot-password": [10],
		"/journal": [11],
		"/login": [12,[2]],
		"/payment-success": [13],
		"/playbook": [14],
		"/portfolio": [15],
		"/pricing": [16],
		"/privacy": [17],
		"/register": [18,[3]],
		"/reset-password": [19],
		"/security": [20],
		"/settings": [21],
		"/terms": [22],
		"/test-insights": [24],
		"/test": [23],
		"/tradelog": [25],
		"/trades": [26],
		"/trades/new": [27],
		"/upload": [28],
		"/verify-email": [29]
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