import { useRouter } from "vue-router"
import { ref, computed } from 'vue';
import * as myFetch from "./myFetch";

export function api(action: string, body?: unknown, method?: string, headers?: any) {
        headers = headers ?? {};
    return myFetch.api(`${action}`, body, method, headers)
        .catch(err => console.log(err))
  }

 export interface Device {
    device: string;
    description: string;
    hwid: string;
  }

export function useGetPorts(){
    const router = useRouter();
    return {
        async ports(){
            try{
                const response = await api('getports'); 
                return response; 
            }catch(error){
                console.error(error);
            }
        }
    }
}