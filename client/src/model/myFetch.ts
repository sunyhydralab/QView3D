const API_ROOT = import.meta.env.VITE_API_ROOT as string;

export function rest(url: string, body?: unknown, method?: string, headers?: HeadersInit){
    console.log(body instanceof FormData)
    const contentType = body instanceof FormData ? 'multipart/form-data' : 'application/json';
    console.log(contentType)
    return fetch(url, {
        method: method ?? (body ? "POST" : "GET"),
        headers: {
            // 'Content-Type': 'application/json',
            'Content-Type': contentType,
            ...headers
        },
        body: body ? JSON.stringify(body) : undefined
    })
        .then(response => response.ok 
            ? response.json()
            : response.json().then(err => Promise.reject(err))    )
}

export function api(action: string, body?: unknown, method?: string, headers?: HeadersInit){
    return rest(`${API_ROOT}/${action}`, body, method, headers);
}