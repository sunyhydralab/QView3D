<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { fabricatorList } from '@/models/fabricator';
import { emulatorPrinters, type IssueType } from '@/models/emulatorPrinters';

// Issue fixes (generic)
const issueFixes: Record<IssueType, string[]> = {
  'No issues': [],
  'Hardware issues': [
    'Check power supply',
    'Inspect cables and connections',
    'Ensure printer is turned on'
  ],
  'File/Input issues': [
    'Check file format',
    'Ensure correct slicer settings',
    'Verify file integrity'
  ]
};

// --- User-defined hardware issues ---
const STORAGE_KEY = 'userHardwareIssues';
const userHardwareIssues = ref<string[]>([]);
const newIssueText = ref('');

// Load saved issues from localStorage
onMounted(() => {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      userHardwareIssues.value = JSON.parse(saved);
    } catch (e) {
      console.warn('Error parsing saved hardware issues:', e);
      userHardwareIssues.value = [];
    }
  }

  // Add mock emulator printer if none exists
  if (emulatorPrinters.value.length === 0) {
    emulatorPrinters.value.push({
      id: 'emu-mock-1',
      name: 'Emulator Printer (Mock) 1',
      description: 'Virtual 3D Printer for Testing',
      date: new Date().toISOString(),
      hwid: 'EMU-MOCK-1234',
      issues: 'Hardware issues',
    });
  }
});

// Persist user-defined issues in localStorage whenever they change
watch(userHardwareIssues, (newVal) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newVal));
}, { deep: true });

// Combine Fabricator and Emulator printers
const allPrinters = computed(() => [
  ...fabricatorList.value,
  ...emulatorPrinters.value
]);

// Type guard
function hasIssues(printer: any): printer is { issues: IssueType } {
  return 'issues' in printer && !!printer.issues;
}

// Add a new user-defined issue
function addUserHardwareIssue() {
  const trimmed = newIssueText.value.trim();
  if (!trimmed) return;

  if (userHardwareIssues.value.includes(trimmed)) {
    alert('This issue is already added.');
    return;
  }

  userHardwareIssues.value.push(trimmed);
  newIssueText.value = '';
}

// Delete a user-defined issue (with confirmation)
function deleteUserHardwareIssue(issue: string) {
  if (confirm(`Are you sure you want to delete "${issue}"?`)) {
    userHardwareIssues.value = userHardwareIssues.value.filter(i => i !== issue);
  }
}
</script>

<template>
  <transition name="slide-down" appear>
    <div class="container mx-auto pt-12 px-4">
      <h1 class="text-3xl font-bold mb-6 text-center text-gray-800 dark:text-light-primary">
        Issues Page
      </h1>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Registered Printers Panel -->
        <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow-lg p-6 transition-all duration-300 hover:shadow-xl transform hover:-translate-y-1">
          <h2 class="text-xl font-semibold mb-4 dark:text-light-primary">Registered Printers</h2>
          <ul>
            <li v-for="printer in allPrinters" :key="printer.id" class="mb-2">
              <div class="font-medium text-dark-primary dark:text-light-primary">
                {{ printer.name || 'Unnamed Printer' }}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-300">
                Model: {{ printer.description }}<br>
                Registered: {{ printer.date || 'N/A' }}
              </div>
            </li>
          </ul>
        </div>

        <!-- Issues Status Panel -->
        <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow-lg p-6 transition-all duration-300 hover:shadow-xl transform hover:-translate-y-1">
          <h2 class="text-xl font-semibold mb-4 dark:text-light-primary">Issues Status</h2>
          <ul>
            <li v-for="printer in allPrinters" :key="printer.id + '-status'" class="mb-2">
              <div class="font-medium text-dark-primary dark:text-light-primary">
                {{ printer.name || 'Unnamed Printer' }}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-300">
                Status:
                <span class="px-2 py-1 rounded-full text-sm" :class="{
                  'bg-green-100 text-green-800': hasIssues(printer) && printer.issues === 'No issues',
                  'bg-red-100 text-red-800': hasIssues(printer) && printer.issues === 'Hardware issues',
                  'bg-yellow-100 text-yellow-800': hasIssues(printer) && printer.issues === 'File/Input issues',
                  'bg-gray-100 text-gray-800': !hasIssues(printer)
                }">
                  {{ hasIssues(printer) ? printer.issues : 'No issues' }}
                </span>
              </div>
            </li>
          </ul>
        </div>

        <!-- Issue Fixes Panel -->
        <div class="bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow-lg p-6 transition-all duration-300 hover:shadow-xl transform hover:-translate-y-1">
          <h2 class="text-xl font-semibold mb-4 dark:text-light-primary">Issue Fixes</h2>
          <div v-if="Object.keys(issueFixes).length">
            <div v-for="(fixList, issue) in issueFixes" :key="issue" class="mb-4">
              <div class="font-medium text-dark-primary dark:text-light-primary">{{ issue }}</div>
              <ul v-if="fixList.length" class="list-disc ml-5 text-sm text-gray-600 dark:text-gray-300">
                <li v-for="fix in fixList" :key="fix">{{ fix }}</li>
              </ul>
              <div v-else class="text-sm text-gray-500 dark:text-gray-400">
                No fixes needed.
              </div>
            </div>
          </div>
          <div v-else class="text-gray-500 dark:text-gray-400">
            No issue fixes defined.
          </div>
        </div>
      </div>

      <!-- User-Defined Hardware Issues Panel -->
      <div class="mt-8 bg-light-primary-light dark:bg-dark-primary-light rounded-lg shadow-lg p-6 hover:shadow-xl transform hover:-translate-y-1">
        <h2 class="text-xl font-semibold mb-4 dark:text-light-primary">User-Defined Hardware Issues</h2>

        <div class="flex gap-2 mb-3">
          <input
            v-model="newIssueText"
            placeholder="Enter hardware issue..."
            class="flex-1 border border-gray-400 rounded-lg p-2 text-sm dark:bg-gray-800 dark:text-white"
          />
          <button
            @click="addUserHardwareIssue"
            class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg text-sm transition-all">
            Add
          </button>
        </div>

        <ul v-if="userHardwareIssues.length" class="space-y-2 text-sm text-gray-600 dark:text-gray-300">
          <li
            v-for="issue in userHardwareIssues"
            :key="issue"
            class="flex items-center justify-between bg-gray-100 dark:bg-gray-800 p-2 rounded-lg">
            <span>{{ issue }}</span>
            <button
              @click="deleteUserHardwareIssue(issue)"
              class="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 text-xs font-medium transition-all">
              🗑 Remove
            </button>
          </li>
        </ul>

        <div v-else class="text-sm text-gray-500 dark:text-gray-400">
          No user-defined issues yet.
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Animation */
.slide-down-enter-active {
  transition: all 0.5s ease;
}
.slide-down-enter-from {
  transform: translateY(-20px);
  opacity: 0;
}
.slide-down-enter-to {
  transform: translateY(0);
  opacity: 1;
}
</style>
