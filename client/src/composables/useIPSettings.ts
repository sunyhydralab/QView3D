import {computed} from 'vue'

// declare IP settings
export const API_IP_ADDRESS = computed(() => localStorage.getItem("apiIPAddress") || "localhost")
export const API_PORT = computed(() => localStorage.getItem("apiPort") || "8000")
export const API_URL = computed(() => `http://${API_IP_ADDRESS.value}:${API_PORT.value}`)

const ipAddressRegex = /^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$|localhost$/;
const portRegex = /^(6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]?\d{1,4})$/;

function saveAPIPort(port: string): void {
    localStorage.setItem("apiPort", port)
}

// update IP Address
export function updateAPIAddress(ipAddress: string): void {
    // check if the ip address is valid
    if (!ipAddressRegex.test(ipAddress)) {
        throw new Error("Invalid IP address");
    }
    localStorage.setItem("apiIPAddress", ipAddress)
}

// update API port
export function updateAPIPort(port: string): void {
    // check if the port is valid
    if (!portRegex.test(port)) {
        throw new Error("Invalid port");
    }
    saveAPIPort(port)
}
