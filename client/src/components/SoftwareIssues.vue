<template>
  <div class="space-y-6">
    <!-- Header with GitHub Link -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white">Software Issues</h2>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">
          Bugs, feature requests, and improvements
        </p>
      </div>
      <div class="flex space-x-3">
        <a
          href="https://github.com/sunyhydralab/QView3D/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="group relative px-6 py-3 rounded-xl font-medium text-white overflow-hidden shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-gray-800 to-gray-900 group-hover:from-gray-700 group-hover:to-gray-800 transition-all duration-200"></div>
          <div class="relative flex items-center space-x-2">
            <i class="fab fa-github text-xl"></i>
            <span>View on GitHub</span>
            <i class="fas fa-external-link-alt text-sm"></i>
          </div>
        </a>
        <button
          @click="$emit('create')"
          class="group relative px-6 py-3 rounded-xl font-medium text-white overflow-hidden shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 group-hover:from-purple-500 group-hover:to-pink-500 transition-all duration-200"></div>
          <div class="relative flex items-center space-x-2">
            <i class="fas fa-plus"></i>
            <span>Log Issue</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Info Card -->
    <div class="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800 rounded-xl p-6">
      <div class="flex items-start space-x-4">
        <div class="flex-shrink-0">
          <i class="fab fa-github text-4xl text-purple-600 dark:text-purple-400"></i>
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Track software issues on GitHub
          </h3>
          <p class="text-gray-700 dark:text-gray-300 mb-4">
            For software bugs, feature requests, and improvements, we use GitHub Issues.
            This allows for better collaboration, code linking, and issue tracking.
          </p>
          <a
            href="https://github.com/sunyhydralab/QView3D/issues/new"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center space-x-2 text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium transition-colors"
          >
            <span>Create a new issue on GitHub</span>
            <i class="fas fa-arrow-right"></i>
          </a>
        </div>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-purple-100 text-sm">Logged</p>
            <p class="text-3xl font-bold mt-1">{{ issues.length }}</p>
          </div>
          <i class="fas fa-bug text-4xl text-purple-200"></i>
        </div>
      </div>
      <div class="bg-gradient-to-br from-pink-500 to-pink-600 rounded-xl p-6 text-white shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-pink-100 text-sm">Open</p>
            <p class="text-3xl font-bold mt-1">{{ stats.open }}</p>
          </div>
          <i class="fas fa-folder-open text-4xl text-pink-200"></i>
        </div>
      </div>
      <div class="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-green-100 text-sm">Resolved</p>
            <p class="text-3xl font-bold mt-1">{{ stats.resolved }}</p>
          </div>
          <i class="fas fa-check-circle text-4xl text-green-200"></i>
        </div>
      </div>
    </div>

    <!-- Local Issues List -->
    <div>
      <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        Locally Logged Issues
      </h3>

      <div v-if="issues.length === 0" class="text-center py-16">
        <i class="fab fa-github text-6xl text-gray-400 dark:text-gray-600 mb-4"></i>
        <p class="text-xl font-medium text-gray-700 dark:text-gray-300">No local software issues</p>
        <p class="text-gray-500 dark:text-gray-400 mt-2">Log issues here before creating GitHub tickets</p>
      </div>

      <div v-else class="space-y-4">
        <TransitionGroup name="list">
          <div
            v-for="issue in sortedIssues"
            :key="issue.id"
            class="group bg-white dark:bg-dark-primary-light rounded-xl shadow-md hover:shadow-xl transition-all duration-200 overflow-hidden border-l-4 border-purple-500"
          >
            <div class="p-6">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center space-x-3 mb-2">
                    <span
                      class="px-3 py-1 rounded-full text-xs font-semibold"
                      :class="getSeverityBadgeClass(issue.severity)"
                    >
                      {{ issue.severity || 'low' }}
                    </span>
                    <span
                      v-if="issue.status === 'resolved'"
                      class="px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                    >
                      Resolved
                    </span>
                    <span class="text-sm text-gray-500 dark:text-gray-400">
                      {{ formatDate(issue.created_at) }}
                    </span>
                  </div>

                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {{ issue.title }}
                  </h3>

                  <p class="text-gray-600 dark:text-gray-300 mb-4">
                    {{ issue.description }}
                  </p>

                  <div class="flex items-center space-x-2">
                    <a
                      href="https://github.com/sunyhydralab/QView3D/issues"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium transition-colors"
                    >
                      <i class="fab fa-github mr-1"></i>
                      Report this on GitHub
                    </a>
                  </div>
                </div>

                <div class="flex flex-col space-y-2 ml-4">
                  <button
                    v-if="issue.status === 'open'"
                    @click="$emit('resolve', issue.id)"
                    class="px-4 py-2 rounded-lg text-sm font-medium bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800 transition-colors"
                    title="Mark as resolved"
                  >
                    <i class="fas fa-check mr-1"></i> Resolve
                  </button>
                  <button
                    @click="$emit('edit', issue)"
                    class="px-4 py-2 rounded-lg text-sm font-medium bg-purple-100 text-purple-700 hover:bg-purple-200 dark:bg-purple-900 dark:text-purple-200 dark:hover:bg-purple-800 transition-colors"
                    title="Edit issue"
                  >
                    <i class="fas fa-edit mr-1"></i> Edit
                  </button>
                  <button
                    @click="$emit('delete', issue.id)"
                    class="px-4 py-2 rounded-lg text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800 transition-colors"
                    title="Delete issue"
                  >
                    <i class="fas fa-trash mr-1"></i> Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  issues: {
    type: Array,
    required: true
  }
});

defineEmits(['refresh', 'create', 'edit', 'delete', 'resolve']);

const stats = computed(() => ({
  open: props.issues.filter(i => i.status === 'open').length,
  resolved: props.issues.filter(i => i.status === 'resolved').length
}));

const sortedIssues = computed(() => {
  return [...props.issues].sort((a, b) => {
    if (a.status !== b.status) {
      return a.status === 'open' ? -1 : 1;
    }
    return new Date(b.created_at) - new Date(a.created_at);
  });
});

const getSeverityBadgeClass = (severity) => {
  switch (severity) {
    case 'critical': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
    case 'high': return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
    case 'medium': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
    default: return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
  }
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
};
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.list-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.list-move {
  transition: transform 0.3s ease;
}
</style>
