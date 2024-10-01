import { api } from './ports'
import { toast } from './toast'

export interface Issue {
    id: number,
    issue: string
}

export function useGetIssues() {
    return {
        async issues() {
            try {
                const response = await api('getissues') // pass rerun job the Job object and desired printer
                if (response.success === true) {
                    return response.issues
                }
            } catch (error) {
                console.error(error)
                toast.error('An error occurred while fetching issues')
            }
        }
    }
}

export function useCreateIssues() {
    return {
        async createIssue(issue: string) {
            try {
                const response = await api('createissue', { issue })
                if (response) {
                    if (response.success == false) {
                        toast.error(response.message)
                    } else if (response.success === true) {
                        toast.success(response.message)
                    } else {
                        console.error('Unexpected response:', response)
                        toast.error('Failed to create issue. Unexpected response')
                    }
                } else {
                    console.error('Response is undefined or null')
                    toast.error('Failed to create issue. Unexpected response')
                }
            } catch (error) {
                console.error(error)
                toast.error('An error occurred while creating the issue')
            }
        }
    }
}

export function useAssignIssue() {
    return {
        async assign(issueid: number, jobid: number) {
            try {
                const response = await api('assignissue', { issueid, jobid })
                if (response) {
                    if (response.success == false) {
                        toast.error(response.message)
                    } else if (response.success === true) {
                        toast.success(response.message)
                    } else {
                        console.error('Unexpected response:', response)
                        toast.error('Failed to assign issue. Unexpected response')
                    }
                } else {
                    console.error('Response is undefined or null')
                    toast.error('Failed to assign issue. Unexpected response')
                }
            } catch (error) {
                console.error(error)
                toast.error('An error occurred while assigning the issue')
            }
        }
    }
}

export function useDeleteIssue() {
    return {
        async deleteIssue(issue: Issue) {
            const issueid = issue.id
            try {
                const response = await api(`deleteissue`, { issueid })
                if (response) {
                    if (response.success == false) {
                        toast.error(response.message)
                    } else if (response.success === true) {
                        toast.success(response.message)
                    } else {
                        console.error('Unexpected response:', response)
                        toast.error('Failed to delete issue. Unexpected response')
                    }
                } else {
                    console.error('Response is undefined or null')
                    toast.error('Failed to delete issue. Unexpected response')
                }
            } catch (error) {
                console.error(error)
                toast.error('An error occurred while deleting the issue')
            }
        }
    }
}

export function useEditIssue() {
    return {
        async editIssue(issueid: number | undefined, issuenew: string) {
            try {
                const response = await api(`editissue`, { issueid, issuenew })
                if (response) {
                    if (response.success == false) {
                        toast.error(response.message)
                    } else if (response.success === true) {
                        toast.success(response.message)
                    } else {
                        console.error('Unexpected response:', response)
                        toast.error('Failed to edit issue. Unexpected response')
                    }
                } else {
                    console.error('Response is undefined or null')
                    toast.error('Failed to edit issue. Unexpected response')
                }
            } catch (error) {
                console.error(error)
                toast.error('An error occurred while editing the issue')
            }
        }
    }
}
