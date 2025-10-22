<template>
  <div class="min-h-screen bg-gradient-to-br from-light-primary via-white to-light-primary dark:from-dark-primary-dark dark:via-dark-primary dark:to-dark-primary-light transition-colors duration-300">
    <!-- Header -->
    <div class="pt-6 pb-8 px-4 sm:px-6 lg:px-8">
      <div class="max-w-7xl mx-auto">
        <h1 class="text-4xl font-bold bg-gradient-to-r from-accent-primary via-accent-primary-light to-accent-secondary bg-clip-text text-transparent">
          Issue Tracker
        </h1>
        <p class="mt-2 text-dark-primary dark:text-light-primary">
          Monitor and manage printer, job, and software issues
        </p>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="relative bg-white/80 dark:bg-dark-primary-light/80 backdrop-blur-sm rounded-2xl shadow-xl p-2">
        <div class="flex space-x-2 relative">
          <!-- Sliding indicator -->
          <div
            class="absolute top-2 bottom-2 rounded-xl transition-all duration-300 ease-out bg-gradient-to-r"
            :class="[
              activeTab === 'printer' ? 'from-accent-primary to-accent-primary-light' :
              activeTab === 'job' ? 'from-accent-secondary-dark to-accent-secondary' :
              'from-purple-600 to-pink-600'
            ]"
            :style="{
              left: `${tabIndicatorPosition}px`,
              width: `${tabIndicatorWidth}px`
            }"
          />

          <!-- Tab Buttons -->
          <button
            v-for="tab in tabs"
            :key="tab.id"
            ref="tabButtons"
            @click="switchTab(tab.id)"
            class="flex-1 relative z-10 px-6 py-4 rounded-xl font-medium transition-all duration-200"
            :class="activeTab === tab.id
              ? 'text-white'
              : 'text-dark-primary dark:text-light-primary hover:bg-light-primary dark:hover:bg-dark-primary'"
          >
            <div class="flex items-center justify-center space-x-2">
              <i :class="tab.icon" class="text-lg"/>
              <span>{{ tab.label }}</span>
              <span
                v-if="getCountByCategory(tab.id) > 0"
                class="ml-2 px-2 py-0.5 text-xs rounded-full"
                :class="activeTab === tab.id
                  ? 'bg-white/30 text-white'
                  : 'bg-accent-primary/20 text-accent-primary dark:bg-accent-primary-light/20 dark:text-accent-primary-light'"
              >
                {{ getCountByCategory(tab.id) }}
              </span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Content Area with Swipe Support -->
    <div
      ref="contentArea"
      class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <Transition :name="slideDirection" mode="out-in">
        <component
          :is="activeComponent"
          :key="activeTab"
          :issues="filteredIssues"
          @refresh="loadIssues"
          @create="showCreateModal"
          @edit="showEditModal"
          @delete="deleteIssue"
          @resolve="resolveIssue"
        />
      </Transition>
    </div>

    <!-- Create/Edit Issue Modal -->
    <IssueModal
      v-if="showModal"
      :issue="selectedIssue"
      :category="activeTab"
      @close="closeModal"
      @save="saveIssue"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { api } from '../models/api';
import PrinterIssues from '../components/PrinterIssues.vue';
import JobIssues from '../components/JobIssues.vue';
import SoftwareIssues from '../components/SoftwareIssues.vue';
import IssueModal from '../components/IssueModal.vue';

const activeTab = ref('printer');
const issues = ref([]);
const showModal = ref(false);
const selectedIssue = ref(null);
const slideDirection = ref('slide-left');
const tabButtons = ref([]);
const tabIndicatorPosition = ref(0);
const tabIndicatorWidth = ref(0);

// Touch handling for swipe
const touchStartX = ref(0);
const touchEndX = ref(0);

const tabs = [
  { id: 'printer', label: 'Printer Issues', icon: 'fas fa-print' },
  { id: 'job', label: 'Job Issues', icon: 'fas fa-tasks' },
  { id: 'software', label: 'Software Issues', icon: 'fab fa-github' }
];

const activeComponent = computed(() => {
  switch (activeTab.value) {
    case 'printer': return PrinterIssues;
    case 'job': return JobIssues;
    case 'software': return SoftwareIssues;
    default: return PrinterIssues;
  }
});

const filteredIssues = computed(() => {
  if (!issues.value || !Array.isArray(issues.value)) {
    return [];
  }
  return issues.value.filter(issue => issue.category === activeTab.value);
});

const getCountByCategory = (category) => {
  // Defensive check to prevent errors if issues.value is undefined
  if (!issues.value || !Array.isArray(issues.value)) {
    return 0;
  }
  return issues.value.filter(issue =>
    issue.category === category && issue.status === 'open'
  ).length;
};

const switchTab = (tabId) => {
  const currentIndex = tabs.findIndex(t => t.id === activeTab.value);
  const newIndex = tabs.findIndex(t => t.id === tabId);

  slideDirection.value = newIndex > currentIndex ? 'slide-left' : 'slide-right';
  activeTab.value = tabId;
};

const updateIndicatorPosition = async () => {
  await nextTick();
  const currentTabIndex = tabs.findIndex(t => t.id === activeTab.value);
  const button = tabButtons.value[currentTabIndex];

  if (button) {
    tabIndicatorPosition.value = button.offsetLeft;
    tabIndicatorWidth.value = button.offsetWidth;
  }
};

watch(activeTab, updateIndicatorPosition);

const handleTouchStart = (e) => {
  touchStartX.value = e.changedTouches[0].screenX;
};

const handleTouchMove = (e) => {
  touchEndX.value = e.changedTouches[0].screenX;
};

const handleTouchEnd = () => {
  const threshold = 50;
  const diff = touchStartX.value - touchEndX.value;

  if (Math.abs(diff) > threshold) {
    const currentIndex = tabs.findIndex(t => t.id === activeTab.value);

    if (diff > 0 && currentIndex < tabs.length - 1) {
      // Swipe left - next tab
      switchTab(tabs[currentIndex + 1].id);
    } else if (diff < 0 && currentIndex > 0) {
      // Swipe right - previous tab
      switchTab(tabs[currentIndex - 1].id);
    }
  }
};

const loadIssues = async () => {
  try {
    const response = await api('getissues', undefined, 'GET');
    // Ensure we always have an array, even if the API returns unexpected data
    issues.value = response?.issues || [];
  } catch (error) {
    console.error('Failed to load issues:', error);
    // Keep issues as empty array on error to prevent filter errors
    issues.value = [];
  }
};

const showCreateModal = () => {
  // Redirect to GitHub for software issues instead of showing modal
  if (activeTab.value === 'software') {
    window.open('https://github.com/sunyhydralab/QView3D/issues/new', '_blank');
    return;
  }
  selectedIssue.value = null;
  showModal.value = true;
};

const showEditModal = (issue) => {
  selectedIssue.value = issue;
  showModal.value = true;
};

const closeModal = () => {
  showModal.value = false;
  selectedIssue.value = null;
};

const saveIssue = async (issueData) => {
  try {
    if (selectedIssue.value) {
      await api('updateissue', { ...issueData, id: selectedIssue.value.id }, 'POST');
    } else {
      await api('createissue', { ...issueData, category: activeTab.value }, 'POST');
    }
    await loadIssues();
    closeModal();
  } catch (error) {
    console.error('Failed to save issue:', error);
  }
};

const deleteIssue = async (issueId) => {
  if (!confirm('Are you sure you want to delete this issue?')) return;

  try {
    await api('deleteissue', { id: issueId }, 'POST');
    await loadIssues();
  } catch (error) {
    console.error('Failed to delete issue:', error);
  }
};

const resolveIssue = async (issueId) => {
  try {
    await api('resolveissue', { id: issueId }, 'POST');
    await loadIssues();
  } catch (error) {
    console.error('Failed to resolve issue:', error);
  }
};

onMounted(async () => {
  await loadIssues();
  await updateIndicatorPosition();
});
</script>

<style scoped>
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.slide-right-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
