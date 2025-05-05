// in .env: VITE_API_ROOT="api url"
import {API_URL} from "@/composables/useIPSettings";

export async function api(endPoint: string, body?: unknown, method?: string, headers?: HeadersInit) {
    // Check if body is FormData
    const isFormData = body instanceof FormData;
    // initializes the RequestOptions object
    const requestOptions: RequestInit = {
        method: method ?? (body ? "POST" : "GET"),
        headers: isFormData ? headers : {
            'Content-Type': 'application/json',
            ...headers,
        },
        body: isFormData ? body : body ? JSON.stringify(body) : undefined,
    };
    
    try {
        // sends the request to the server and sets the response
        const response = await fetch(`${API_URL.value}/${endPoint}`, requestOptions);
        // set the response in json form
        const dataInJson = await response.json();
        // check if the response is ok
        if (!response.ok) {
            console.error(`Error: ${dataInJson.message}`); // try .error as well
        }
        return dataInJson;
    } catch (error) {
        // sends an error if the request fails
        console.error("API request error:", error);
    }
}