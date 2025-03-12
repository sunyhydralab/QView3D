import { type Config } from '@/model/config';
import io from 'socket.io-client';
import {ref, computed} from 'vue';

const config = ref<Config>({
    apiIPAddress: '0.0.0.0',
    apiPort: 0
});

const storedIP = localStorage.getItem('apiIPAddress') || '127.0.0.1';
const storedPort = localStorage.getItem('apiPort') || '8000';
localStorage.setItem('apiIPAddress', storedIP);
localStorage.setItem('apiPort', storedPort);
config.value.apiIPAddress = storedIP;
config.value.apiPort = parseInt(storedPort, 10);

export const API_IP_ADDRESS = computed(() => localStorage.getItem('apiIPAddress'));
export const API_PORT = computed(() => localStorage.getItem('apiPort'));
export const API_ROOT = computed(() => `http://${API_IP_ADDRESS.value}:${API_PORT.value}`);

// socket.io setup for status updates, using the config.json variable
// moved this to myFetch.ts to make it easier to use in other files
export const socket = ref(io(API_ROOT.value, {
    transports: ['websocket']
}));

export function rest(url: string, body?: unknown, method?: string, headers?: HeadersInit) {
    const isFormData = body instanceof FormData;
    const options: RequestInit = {
        method: method ?? (body ? "POST" : "GET"),
        headers: {
            ...headers
        },
        body: isFormData ? body : JSON.stringify(body)
    };

    if (!isFormData) {
        options.headers = options.headers || {};
        (options.headers as Record<string, string>)['Content-Type'] = 'application/json';
    }

    return fetch(url, options)
        .then(response => response.ok
            ? response.json()
            : response.json().then(err => Promise.reject(err)))
}

export function api(action: string, body?: unknown, method?: string, headers?: HeadersInit) {
    return rest(`${API_ROOT.value}/${action}`, body, method, headers);
}

export function setServerIP(ip: string) {
    // test if the ip is valid
    const ipArray = ip.split('.');
    if (ipArray.length !== 4) {
        throw new Error('Invalid IP address');
    }
    for (const octet of ipArray) {
        const num = parseInt(octet);
        if (num < 0 || num > 255) {
            throw new Error('Invalid IP address');
        }
    }
    config.value.apiIPAddress = ip;
    socketUpdate(ip, Number(API_PORT.value ?? 8000));
    localStorage.setItem('apiIPAddress', ip);
}

export function setServerPort(port: number) {
    // test if the port is valid
    if (port < 1 || port > 65535) {
        throw new Error('Invalid port number');
    }
    config.value.apiPort = port;
    socketUpdate(API_IP_ADDRESS.value ?? '127.0.0.1', port);
    localStorage.setItem('apiPort', port.toString());
}

function socketUpdate(ip: string, port: number) {
    socket.value.disconnect();
    socket.value = io(`http://${ip}:${port}`, {
        transports: ['websocket']
    });
    window.location.reload();
}