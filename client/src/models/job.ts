import { api } from '@/myFetch'
import { ref } from 'vue'
// import type { Log } from '@/log'

export const newJobResponse = ref<Job | null>(null)

interface Job 
{
    id?: number
    name: string
    gcode_file: FormData  // Contains gcode file as bytes.
    gcode_file_name: string
    status: JobStatus
    date_created: Date
    date_completed: Date
    is_favorite: boolean
    attached_logs: Log[]
    ticket_id: number
}

//  TODO: Make log.ts.
export async function get_logs(job_id: number): Promise<Log[]> {
    const res = await api('/jobs/${job_id}/logs')
    return res.logs
}


/*
WIP:
get_all()
delete_job(job_id: number)
get_all_as_csv()
search_job(query : Query)
create_log(job_id: number, log: Log)
edit_log(job_id: number, edited_log : number)
delete_log(job_id: number, log_id: number)
*/