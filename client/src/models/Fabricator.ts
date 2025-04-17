import { ref } from 'vue'

export const fabrictors_list = ref<Fabricator[]>([])

interface Fabricator 
{
	id? : number
	hardwareId? : string
	customName : string
    description? : string
	dateRegistered: number
	modelName : string
	jobQueue : Job[]
	isQueueExpanded : boolean
	isWaitingForResponse : boolean
}

/*
WIP
add_job(fabricator_id : number, job : Job)
remove_job(fabricator_id : number, job_id : number)
get_job_status(fabricator_id: number)
register_fabricator(fabricator : Fabricator)
edit_job_status(fabricator_id: number, job_status : string)
move_job(fabricator_id: number, job_id : number, new_position : number)
edit_name(fabricator_id: number, custom_name : string)
rerun_job(fabricator_id: number, job_id: number)
start_job(fabricator_id: number)
get_registered()
get_all()
*/




