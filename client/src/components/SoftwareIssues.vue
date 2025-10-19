<script setup lang="ts">
import { computed } from 'vue';
import BaseStatCard from './base/BaseStatCard.vue';
import BaseBadge from './base/BaseBadge.vue';
import BaseCard from './base/BaseCard.vue';
import BaseEmptyState from './base/BaseEmptyState.vue';
import { useRelativeTime } from '@/composables/useFormatting';

interface Issue {
  id: number;
  title: string;
  description: string;
  severity: string;
  status: string;
  created_at: string;
}

const props = defineProps<{ issues: Issue[] }>();
defineEmits(['create', 'edit', 'delete', 'resolve']);

const stats = computed(() => ({
  logged: props.issues.length,
  open: props.issues.filter(i => i.status === 'open').length,
  resolved: props.issues.filter(i => i.status === 'resolved').length
}));
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-semibold text-dark-primary dark:text-light-primary-light">Software Issues</h2>
        <p class="mt-1 text-sm text-dark-primary dark:text-light-primary">Bugs, feature requests, and improvements</p>
      </div>
      <div class="flex space-x-3">
        <a
          href="https://github.com/sunyhydralab/QView3D/issues"
          target="_blank"
          rel="noopener noreferrer"
          class="gradient-button"
          style="background: linear-gradient(to right, #1f2937, #111827);"
        >
          <i class="fab fa-github"></i>
          <span>View on GitHub</span>
          <i class="fas fa-external-link-alt text-sm"></i>
        </a>
        <button @click="$emit('create')" class="gradient-button" style="background: linear-gradient(to right, #9333ea, #ec4899);">
          <i class="fas fa-plus"></i>
          <span>Log Issue</span>
        </button>
      </div>
    </div>

    <BaseCard padding="lg" class="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800">
      <div class="flex items-start space-x-4">
        <i class="fab fa-github text-4xl text-purple-600 dark:text-purple-400"></i>
        <div>
          <h3 class="text-lg font-semibold text-dark-primary dark:text-light-primary-light mb-2">Track software issues on GitHub</h3>
          <p class="text-dark-primary dark:text-light-primary mb-4">
            For software bugs, feature requests, and improvements, we use GitHub Issues for better collaboration.
          </p>
          <a
            href="https://github.com/sunyhydralab/QView3D/issues/new"
            target="_blank"
            class="inline-flex items-center space-x-2 text-purple-600 dark:text-purple-400 hover:text-purple-700 font-medium"
          >
            <span>Create a new issue on GitHub</span>
            <i class="fas fa-arrow-right"></i>
          </a>
        </div>
      </div>
    </BaseCard>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <BaseStatCard title="Logged" :value="stats.logged" icon="fas fa-bug" gradient="from-purple-500 to-purple-600" />
      <BaseStatCard title="Open" :value="stats.open" icon="fas fa-folder-open" gradient="from-pink-500 to-pink-600" />
      <BaseStatCard title="Resolved" :value="stats.resolved" icon="fas fa-check-circle" gradient="from-green-500 to-green-600" />
    </div>

    <div>
      <h3 class="text-xl font-semibold text-dark-primary dark:text-light-primary-light mb-4">Locally Logged Issues</h3>

      <BaseEmptyState
        v-if="issues.length === 0"
        icon="fas fa-code-branch"
        title="No local software issues"
        description="All issues are tracked on GitHub"
        icon-color="text-purple-500 dark:text-purple-400"
      />

      <div v-else class="space-y-4">
        <TransitionGroup name="list">
          <BaseCard v-for="issue in issues" :key="issue.id" padding="md">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <div class="flex items-center space-x-3 mb-2">
                  <BaseBadge size="sm">{{ issue.severity || 'low' }}</BaseBadge>
                  <BaseBadge v-if="issue.status === 'resolved'" variant="success" size="sm">Resolved</BaseBadge>
                  <span class="text-sm text-dark-primary dark:text-light-primary">{{ useRelativeTime(issue.created_at) }}</span>
                </div>
                <h3 class="text-lg font-semibold text-dark-primary dark:text-light-primary-light mb-2">{{ issue.title }}</h3>
                <p class="text-dark-primary dark:text-light-primary">{{ issue.description }}</p>
              </div>
              <div class="flex flex-col space-y-2 ml-4">
                <button v-if="issue.status === 'open'" @click="$emit('resolve', issue.id)" class="action-button success">
                  <i class="fas fa-check mr-1"></i> Resolve
                </button>
                <button @click="$emit('edit', issue)" class="action-button primary">
                  <i class="fas fa-edit mr-1"></i> Edit
                </button>
                <button @click="$emit('delete', issue.id)" class="action-button danger">
                  <i class="fas fa-trash mr-1"></i> Delete
                </button>
              </div>
            </div>
          </BaseCard>
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>
