<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
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

// Add a mock emulator printer for testing
onMounted(() => {
  if (emulatorPrinters.value.length === 0) {
    emulatorPrinters.value.push({
      id: 'emu-mock-1',
      name: 'Emulator Printer (Mock) 1',
      description: 'Virtual 3D Printer for Testing',
      date: new Date().toISOString(),
      hwid: 'EMU-MOCK-1234',
      issues: 'Hardware issues', // Options: 'No issues', 'Hardware issues', 'File/Input issues'
    });
  }
});

// Combine Fabricator and Emulator printers
const allPrinters = computed(() => [
  ...fabricatorList.value,
  ...emulatorPrinters.value
]);

// Type guard to check if printer has 'issues'
function hasIssues(printer: any): printer is { issues: IssueType } {
  return 'issues' in printer && !!printer.issues;
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
