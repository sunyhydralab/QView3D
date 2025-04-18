// TODO: Allow env file to update config.
const API_IP_ADDRESS = import.meta.env.DEV ? "localhost" : import.meta.env.API_IP_ADDRESS
const API_PORT = import.meta.env.DEV ? "8000" : import.meta.env.API_PORT
const API_URL = "/api"

export function rest(url: string, body: object | null, method: 'GET' | 'POST' | 'PATCH' | 'DELETE') {
    // creates empty request object. 
    let request = {} as RequestInit
    // sets method of request (POST, GET, etc).
    request.method = method

    // Check if body is FormData object, otherwise, send JSON.
    if (body instanceof FormData) {  // FormData holds gcode file and extra metadata.
        request.body = body
    } else { 
        request.headers = {"Content-Type": "application/json"}
        request.body = JSON.stringify(body)
    }

    // Send a rest compliant request to the backend.
    return fetch(`${API_IP_ADDRESS}:${API_PORT}${API_URL}${url}`, request)
    .then(response => {
        return response.json()
    }).catch(err => {
        console.error(err)
    })
}