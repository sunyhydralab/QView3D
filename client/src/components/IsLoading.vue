<script setup lang="ts">
</script>

<template>
    <transition name="fade">
        <div class="modal fade show d-block" id="loadingModal" tabindex="-1"
             aria-labelledby="loadingModalLabel" aria-hidden="true"
             style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); overflow-y: hidden;">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-body d-flex justify-content-center align-items-center"
                     style="user-select: none; position: relative;">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                </div>
            </div>
        </div>
    </transition>
</template>

<style scoped>
</style>