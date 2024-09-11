import { doHandleApi } from './ports'

export interface Issue {
    id: number,
    issue: string
}

export function useGetIssues() {
    return {
        async issues() {
            const res = await doHandleApi('getissues', undefined, 'get issues', 'fetching the issues', true)
            return res.issues
        }
    }
}

export function useCreateIssues() {
    return {
        async createIssue(issue: string) {
            await doHandleApi('createissue', { issue }, 'create issue', 'creating the issue')
        }
    }
}

export function useAssignIssue() {
    return {
        async assign(issueid: number, jobid: number) {
            await doHandleApi('assignissue', { issueid, jobid }, 'assign issue', 'assigning the issue')
        }
    }
}

export function useDeleteIssue() {
    return {
        async deleteIssue(issue: Issue) {
            await doHandleApi('deleteissue', issue.id, 'delete issue', 'deleting the issue')
        }
    }
}

export function useEditIssue() {
    return {
        async editIssue(issueid: number | undefined, issuenew: string) {
            await doHandleApi('editissue', { issueid, issuenew }, 'edit issue', 'editing the issue')
        }
    }
}
