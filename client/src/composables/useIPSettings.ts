import {computed} from 'vue'
import { migratePortSettings, validatePortSettings } from '@/utils/portMigration'

// Run migration on module load
migratePortSettings();
validatePortSettings();

// Middleware port - frontend connects to middleware which proxies to backends
const MIDDLEWARE_PORT = "8002";

// declare IP settings
export const API_IP_ADDRESS = computed(() => localStorage.getItem("apiIPAddress") || "localhost")
// API_PORT points to middleware which handles backend routing
export const API_PORT = computed(() => MIDDLEWARE_PORT)
export const API_URL = computed(() => `http://${API_IP_ADDRESS.value}:${API_PORT.value}`)

// Debug mode setting
export const DEBUG_MODE = computed(() => localStorage.getItem("debugMode") === "true")

const ipAddressRegex = /^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)(\.(?!$)|$)){4}$|localhost$/;

// update IP Address
export function updateAPIAddress(ipAddress: string): void {
    // check if the ip address is valid
    if (!ipAddressRegex.test(ipAddress)) {
        throw new Error("Invalid IP address");
    }
    localStorage.setItem("apiIPAddress", ipAddress)
}

// update debug mode
export function updateDebugMode(enabled: boolean): void {
    localStorage.setItem("debugMode", enabled.toString())
}
