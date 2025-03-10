<script setup lang="ts">
import { ref, computed, watch } from "vue";
import AnsiToHtml from "ansi-to-html";

// Props
const props = defineProps({lines: Array<string>})

const lines = ref(props.lines);

watch(() => props.lines, (newLines) => {
  lines.value = newLines;
});

// Ref for the terminal container to enable automatic scrolling
const terminalOutput = ref<HTMLDivElement | null>(null);

// Instance of ANSI-to-HTML converter
const ansiConverter = new AnsiToHtml();

// Convert the lines into HTML using the ANSI-to-HTML converter
const processedLines = computed(() =>
  lines.value!.map((line) => ansiConverter.toHtml(line))
);

// Watch for changes in the lines prop and trigger scrolling
watch(processedLines, () => {scrollToBottom();});

// Scroll to the bottom whenever lines update
const scrollToBottom = () => {
  requestAnimationFrame(() => {
    if (terminalOutput.value) {
      terminalOutput.value.scrollTop = terminalOutput.value.scrollHeight;
    }
  });
};
</script>

<template>
  <div class="terminal-container">
    <div class="terminal-output" ref="terminalOutput">
      <div
        v-for="(line, index) in processedLines"
        :key="index"
        v-html="line"
        class="terminal-line"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.terminal-container {
  width: 100%;
  height: 400px; /* Constrain height, but allow dynamic resizing */
  overflow-y: auto; /* Allow scrolling for overflowing content */
  background-color: #1e1e1e;
  color: #ffffff;
  font-size: 11px;
  border: 1px solid #333;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
}

.terminal-output {
  flex: 1; /* Let it grow or shrink with the container */
  overflow-y: auto;
  padding: 10px;
}

.terminal-line {
  white-space: pre-wrap;
  text-align: left;
}

</style>