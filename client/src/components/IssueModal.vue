<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="true"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click.self="$emit('close')"
      >
        <div
          class="relative w-full max-w-2xl bg-white dark:bg-dark-primary-light rounded-2xl shadow-2xl transform transition-all overflow-hidden"
          @click.stop
        >
          <!-- Header -->
          <div class="relative px-8 py-6 bg-gradient-to-r"
               :class="getGradientClass">
            <button
              @click="$emit('close')"
              class="absolute top-4 right-4 p-2 rounded-lg text-white hover:bg-white/20 transition-colors"
            >
              <i class="fas fa-times text-xl"></i>
            </button>
            <h2 class="text-2xl font-bold text-white">
              {{ issue ? 'Edit Issue' : 'Create New Issue' }}
            </h2>
            <p class="text-white/80 mt-1">
              {{ getCategoryLabel }} - {{ issue ? 'Update details below' : 'Fill in the details below' }}
            </p>
          </div>

          <!-- Form -->
          <form @submit.prevent="handleSubmit" class="p-8 space-y-6">
            <!-- Title -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Title *
              </label>
              <input
                v-model="formData.title"
                type="text"
                required
                placeholder="Brief description of the issue"
                class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
              />
            </div>

            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                v-model="formData.description"
                rows="4"
                placeholder="Detailed description of the issue and any relevant information"
                class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20 resize-none"
              />
            </div>

            <!-- Severity -->
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Severity *
              </label>
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <button
                  v-for="sev in severityOptions"
                  :key="sev.value"
                  type="button"
                  @click="formData.severity = sev.value"
                  class="relative px-4 py-3 rounded-xl font-medium transition-all transform hover:scale-105"
                  :class="formData.severity === sev.value
                    ? `${sev.activeClass} shadow-lg`
                    : 'bg-gray-100 dark:bg-dark-primary text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-primary-dark'"
                >
                  <div class="flex flex-col items-center space-y-1">
                    <i :class="sev.icon" class="text-lg"></i>
                    <span class="text-xs">{{ sev.label }}</span>
                  </div>
                </button>
              </div>
            </div>

            <!-- Category-specific fields -->
            <div v-if="category === 'printer'" class="grid grid-cols-1 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Printer ID (Optional)
                </label>
                <input
                  v-model.number="formData.fabricator_id"
                  type="number"
                  placeholder="Enter printer ID if applicable"
                  class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                />
              </div>
            </div>

            <div v-if="category === 'job'" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Job ID (Optional)
                </label>
                <input
                  v-model.number="formData.job_id"
                  type="number"
                  placeholder="Job ID"
                  class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Printer ID (Optional)
                </label>
                <input
                  v-model.number="formData.fabricator_id"
                  type="number"
                  placeholder="Printer ID"
                  class="w-full px-4 py-3 rounded-xl border-2 border-gray-200 dark:border-dark-primary focus:border-accent-primary dark:focus:border-accent-primary-light bg-white dark:bg-dark-primary text-gray-900 dark:text-white placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                />
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200 dark:border-dark-primary">
              <button
                type="button"
                @click="$emit('close')"
                class="px-6 py-3 rounded-xl font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-dark-primary hover:bg-gray-200 dark:hover:bg-dark-primary-dark transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                class="group relative px-6 py-3 rounded-xl font-medium text-white overflow-hidden shadow-lg hover:shadow-xl transition-all transform hover:scale-105"
              >
                <div
                  class="absolute inset-0 transition-all duration-200"
                  :class="getGradientClass"
                ></div>
                <div class="relative flex items-center space-x-2">
                  <i :class="issue ? 'fas fa-save' : 'fas fa-plus'"></i>
                  <span>{{ issue ? 'Update Issue' : 'Create Issue' }}</span>
                </div>
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  issue: {
    type: Object,
    default: null
  },
  category: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['close', 'save']);

const formData = ref({
  title: '',
  description: '',
  severity: 'low',
  fabricator_id: null,
  job_id: null
});

const severityOptions = [
  {
    value: 'low',
    label: 'Low',
    icon: 'fas fa-info-circle',
    activeClass: 'bg-blue-500 text-white'
  },
  {
    value: 'medium',
    label: 'Medium',
    icon: 'fas fa-exclamation-circle',
    activeClass: 'bg-yellow-500 text-white'
  },
  {
    value: 'high',
    label: 'High',
    icon: 'fas fa-exclamation-triangle',
    activeClass: 'bg-orange-500 text-white'
  },
  {
    value: 'critical',
    label: 'Critical',
    icon: 'fas fa-times-circle',
    activeClass: 'bg-red-500 text-white'
  }
];

const getGradientClass = computed(() => {
  switch (props.category) {
    case 'printer':
      return 'from-accent-primary to-accent-primary-light';
    case 'job':
      return 'from-accent-secondary-dark to-accent-secondary';
    case 'software':
      return 'from-purple-600 to-pink-600';
    default:
      return 'from-accent-primary to-accent-primary-light';
  }
});

const getCategoryLabel = computed(() => {
  switch (props.category) {
    case 'printer': return 'Printer Issue';
    case 'job': return 'Job Issue';
    case 'software': return 'Software Issue';
    default: return 'Issue';
  }
});

const handleSubmit = () => {
  emit('save', formData.value);
};

// Initialize form with existing issue data
watch(() => props.issue, (newIssue) => {
  if (newIssue) {
    formData.value = {
      title: newIssue.title || '',
      description: newIssue.description || '',
      severity: newIssue.severity || 'low',
      fabricator_id: newIssue.fabricator_id || null,
      job_id: newIssue.job_id || null
    };
  } else {
    formData.value = {
      title: '',
      description: '',
      severity: 'low',
      fabricator_id: null,
      job_id: null
    };
  }
}, { immediate: true });
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .relative {
  transform: scale(0.9) translateY(-20px);
}

.modal-leave-to .relative {
  transform: scale(0.95) translateY(10px);
}
</style>
