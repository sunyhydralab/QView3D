<script setup lang="ts">
import { computed } from 'vue';
import BaseStatCard from './base/BaseStatCard.vue';
import BaseBadge from './base/BaseBadge.vue';
import BaseCard from './base/BaseCard.vue';
import BaseEmptyState from './base/BaseEmptyState.vue';
import { useSeverity } from '@/composables/useSeverity';
import { useRelativeTime } from '@/composables/useFormatting';

interface Issue {
  id: number;
  title: string;
  description: string;
  severity: string;
  status: string;
  created_at: string;
  fabricator_id?: number;
  job_id?: number;
}

const props = defineProps<{ issues: Issue[] }>();
defineEmits(['create', 'edit', 'delete', 'resolve']);

const { getSeverityOrder } = useSeverity();

const stats = computed(() => ({
  total: props.issues.length,
  failed: props.issues.filter(i => i.severity === 'critical' && i.status === 'open').length,
  quality: props.issues.filter(i => (i.severity === 'medium' || i.severity === 'high') && i.status === 'open').length,
  resolved: props.issues.filter(i => i.status === 'resolved').length
}));

const sortedIssues = computed(() => {
  return [...props.issues].sort((a, b) => {
    if (a.status !== b.status) return a.status === 'open' ? -1 : 1;
    const severityDiff = getSeverityOrder(a.severity) - getSeverityOrder(b.severity);
    if (severityDiff !== 0) return severityDiff;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
});
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white">Job Issues</h2>
        <p class="mt-1 text-sm text-gray-600 dark:text-gray-400">Print failures and quality problems</p>
      </div>
      <button @click="$emit('create')" class="gradient-button" style="background: linear-gradient(to right, var(--color-accent-secondary-dark), var(--color-accent-secondary));">
        <i class="fas fa-plus"></i>
        <span>New Issue</span>
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <BaseStatCard title="Total" :value="stats.total" icon="fas fa-tasks" gradient="from-purple-500 to-purple-600" />
      <BaseStatCard title="Failed" :value="stats.failed" icon="fas fa-times-circle" gradient="from-red-500 to-red-600" />
      <BaseStatCard title="Quality" :value="stats.quality" icon="fas fa-exclamation-triangle" gradient="from-yellow-500 to-yellow-600" />
      <BaseStatCard title="Resolved" :value="stats.resolved" icon="fas fa-check-circle" gradient="from-green-500 to-green-600" />
    </div>

    <BaseEmptyState
      v-if="issues.length === 0"
      icon="fas fa-clipboard-check"
      title="No job issues!"
      description="All prints completing successfully"
      icon-color="text-teal-500 dark:text-teal-400"
    />

    <div v-else class="space-y-4">
      <TransitionGroup name="list">
        <BaseCard v-for="issue in sortedIssues" :key="issue.id" padding="md">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center space-x-3 mb-2">
                <BaseBadge size="sm">{{ issue.severity || 'low' }}</BaseBadge>
                <BaseBadge v-if="issue.status === 'resolved'" variant="success" size="sm">Resolved</BaseBadge>
                <span class="text-sm text-gray-500 dark:text-gray-400">{{ useRelativeTime(issue.created_at) }}</span>
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">{{ issue.title }}</h3>
              <p class="text-gray-600 dark:text-gray-300 mb-4">{{ issue.description }}</p>
              <div class="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                <div v-if="issue.job_id" class="flex items-center space-x-2">
                  <i class="fas fa-file"></i>
                  <span>Job ID: {{ issue.job_id }}</span>
                </div>
                <div v-if="issue.fabricator_id" class="flex items-center space-x-2">
                  <i class="fas fa-print"></i>
                  <span>Printer ID: {{ issue.fabricator_id }}</span>
                </div>
              </div>
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
</template>
