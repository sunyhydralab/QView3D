import { ref, onMounted } from 'vue';

export type IssueType =
  | 'No issues'
  | 'Hardware issues'
  | 'File/Input issues';
export interface EmulatorPrinter {
  id: string | number;
  name: string;
  description: string;
  date: string;
  hwid: string; // hardware ID
  issues?: IssueType; // e.g., 'No issues', 'Hardware issues', etc.
}

export const emulatorPrinters = ref<EmulatorPrinter[]>(
  [
    {
      id: 'emu-mock-1',
      name: 'Emulator Printer (Mock) 1',
      description: 'Virtual 3D Printer for Testing',
      date: new Date().toISOString(),
      hwid: 'EMU-MOCK-1234',
      issues: 'No issues', // or 'Hardware issues', 'File/Input issues'
    },
    {
      id: 'emu-mock-2',
      name: 'Emulator Printer (Mock) 2',
      description: 'Virtual 3D Printer for Testing',
      date: new Date().toISOString(),
      hwid: 'EMU-MOCK-5678',
      issues: 'Hardware issues', 
    },
  ])

const issueFixes: Record<Exclude<IssueType, 'No issues'>, string[]> = {
  'Hardware issues': [
    'Check all cable connections.',
    'Restart the printer and try again.',
    'Inspect for any visible hardware damage.',
    'Ensure firmware is up to date.',
    'Consult the printer manual for troubleshooting steps.',
  ],
  'File/Input issues': [
    'Verify the file format is supported (e.g., .gcode).',
    'Check for file corruption or incomplete uploads.',
    'Re-upload the file and try again.',
    "Ensure the file is not too large for the printer's memory.",
    'Check for syntax errors in the input file.',
  ],
};
