<script setup lang="ts">
import BaseCard from './base/BaseCard.vue';
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
        <a
          href="https://github.com/sunyhydralab/QView3D/issues/new"
          target="_blank"
          rel="noopener noreferrer"
          class="gradient-button"
          style="background: linear-gradient(to right, #9333ea, #ec4899);"
        >
          <i class="fas fa-plus"></i>
          <span>Create Issue on GitHub</span>
          <i class="fas fa-external-link-alt text-sm"></i>
        </a>
      </div>
    </div>

    <BaseCard padding="lg" class="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800">
      <div class="flex items-start space-x-4">
        <i class="fab fa-github text-4xl text-purple-600 dark:text-purple-400"></i>
        <div class="flex-1">
          <h3 class="text-lg font-semibold text-dark-primary dark:text-light-primary-light mb-2">Track software issues on GitHub</h3>
          <p class="text-dark-primary dark:text-light-primary mb-4">
            For software bugs, feature requests, and improvements, we use GitHub Issues for better collaboration and tracking.
          </p>
          <div class="flex flex-wrap gap-3">
            <a
              href="https://github.com/sunyhydralab/QView3D/issues/new"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center space-x-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              <i class="fas fa-plus"></i>
              <span>Create New Issue</span>
              <i class="fas fa-external-link-alt text-sm"></i>
            </a>
            <a
              href="https://github.com/sunyhydralab/QView3D/issues"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-800 text-white rounded-lg font-medium transition-colors"
            >
              <i class="fab fa-github"></i>
              <span>View All Issues</span>
              <i class="fas fa-external-link-alt text-sm"></i>
            </a>
          </div>
        </div>
      </div>
    </BaseCard>
  </div>
</template>
