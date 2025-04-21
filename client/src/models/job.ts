export interface Job {
    id: number
    name: string
    file: File
    download_link?: string
    file_name_original: string
    date?: Date
    status?: string
    progress?: number //store progress of job
    gcode_num?: number //store gcode of job
    printer: string //store printer name
    printerid: number
  
    td_id: number //store td_id of job
  
    max_layer_height?: number //store max layer height of job
    current_layer_height?: number //store current layer height of job
  
    errorid?: number
    error?: string // store issue name
  
    comments?: string // store comments
  
    extruded?: number
    filament?: string
  
    file_pause: number
    priority?: string
    favorite?: boolean
    released?: number
    job_server?: [number, Date | string, Date | string, Date | string] // this saves all the data from the backend.Only changed if there is a pause involved.
  
    job_client?: {
      // this is frontend data CALCULATED based on the backend data
      total_time: number
      eta: number
      elapsed_time: number
      extra_time: number
      remaining_time: number
    }
    time_started?: number
    colorbuff?: number 
    printer_name?: string
    queue_selected?: boolean
  }