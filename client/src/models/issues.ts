// src/models/issues.ts
import { ref } from 'vue';
import type { Ref } from 'vue';

/*
export interface Issue {
  id: string;
  job_id: string;
  type: 'No issues' | 'Hardware issues' | 'File/Input issues';
  description?: string;
  created_at?: string;
}
*/

export interface Issue {
  id: number;        // matches backend db.Integer
  job_id: number;    // matches backend db.Integer
  issue: string;     // descriptive text from backend
  type: 'No issues' | 'Hardware issues' | 'File/Input issues';
}

/*
export async function get_issues(): Promise<Issue[]> {
  // mock data
  try{
    issues.value = [
    { id: 1, job_id: 101, issue: 'Power supply failure', type: 'Hardware issues'  },
    { id: 2, job_id: 102, issue: 'Invalid G-code file', type: 'File/Input issues' },
     { id: 3, job_id: 103, issue: 'No issues detected', type: 'No issues' },
    ];
    return issues.value;
 const res = await fetch('/api/issues');
    const data = await res.json();
    if (data.success) {
      issues.value = data.issues;
      return issues.value;
    } else {``
      console.error('Failed to fetch issues:', data.message);
      return [];
    } catch (err) {
    console.error('Error fetching issues:', err);
    return [];
  }
  */

  export const issues = ref<Issue[]>([
  { id: 1, job_id: 101, issue: 'Power supply failure', type: 'Hardware issues' },
  { id: 2, job_id: 102, issue: 'Invalid G-code file', type: 'File/Input issues' },
  { id: 3, job_id: 103, issue: 'No issues detected', type: 'No issues' },
]);

export async function get_issues() {
  return issues.value;

}
