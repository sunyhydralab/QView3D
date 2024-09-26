import io from 'socket.io-client';
import { ref, computed } from 'vue';
export const API_IP_ADDRESS = ref<string>("192.168.1.106");
export const API_PORT = ref<number>(8000);
export const API_ROOT = computed(() => `http://${API_IP_ADDRESS.value}:${API_PORT.value}`);
// socket.io setup for status updates, using the VITE_API_ROOT environment variable
// moved this to myFetch.ts to make it easier to use in other files
export const socket = computed(() => io(API_ROOT.value, {
    transports: ['websocket']
}));

export function rest(url: string, body?: unknown, method?: string, headers?: HeadersInit){
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
            : response.json().then(err => Promise.reject(err))    )
}

export function api(action: string, body?: unknown, method?: string, headers?: HeadersInit){
    return rest(`${API_ROOT.value}/${action}`, body, method, headers);
}

export function setServerIP(ip: string){
    // test if the ip is valid
    const ipArray = ip.split('.');
    if (ipArray.length !== 4){
        throw new Error('Invalid IP address');
    }
    for (const octet of ipArray){
        const num = parseInt(octet);
        if (num < 0 || num > 255){
            throw new Error('Invalid IP address');
        }
    }
    API_IP_ADDRESS.value = ip;
}
export function setServerPort(port: number){
    // test if the port is valid
    if (port < 1 || port > 65535){
        throw new Error('Invalid port number');
    }
    API_PORT.value = port;
}