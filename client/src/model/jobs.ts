// ts file to retrieve job information 
import { useRouter } from "vue-router"
import {api} from "./ports"
import {toast} from "./toast";

export interface Job{
    name: string; 
    file: File; 
    date: Date;
    status: string; 
    printer: string; //store printer name 
}

export function useGetJobs(){
    return {
        async jobhistory(){
            try{
                const response = await api('getjobs');
                return response; 
            }catch(error){
                console.error(error)
                toast.error("An error occurred while retrieving the jobs");
            }
        }
    }
}

//function to add job to queue
export function useAddJobToQueue(){
    return {
        async addJobToQueue(job: Job){
            try{
                const response = await api('addjobtoqueue', job);
                return response; 
            }catch(error){
                console.error(error)
                toast.error("An error occurred while creating the job");
            }
        }
    }
}