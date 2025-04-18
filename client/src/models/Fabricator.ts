import { ref } from 'vue'

// Keeps track of all registered fabricators
export const fabrictorList = ref<Fabricator[]>([])

// Represents the Fabricator object
export interface Fabricator 

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

// Sets the fabricator information, adds a Fabricator to the fabricatorList, and returns a Fabricator
export function registerFabricator(userSubmission : {customName: string; description: string; modelName: string, date: number;}) : Fabricator
{
	const newFabricator : Fabricator = {
		customName: userSubmission.customName,
		description: userSubmission.description,
		dateRegistered: userSubmission.date,
		modelName: userSubmission.modelName,
		jobQueue: [],
		isQueueExpanded : false,
		isWaitingForResponse : false

	}
	fabrictorList.value.push(newFabricator)
	return newFabricator
}

/*
WIP
add_job(fabricator_id : number, job : Job)
remove_job(fabricator_id : number, job_id : number)
get_job_status(fabricator_id: number)
edit_job_status(fabricator_id: number, job_status : string)
move_job(fabricator_id: number, job_id : number, new_position : number)
edit_name(fabricator_id: number, custom_name : string)
rerun_job(fabricator_id: number, job_id: number)
start_job(fabricator_id: number)
get_registered()
get_all()
*/




