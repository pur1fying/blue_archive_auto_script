<script setup lang="ts">
import { ref, nextTick, watch, onMounted, onUnmounted } from 'vue'
import type { DefaultTheme } from 'vitepress/theme'
import { useRoute } from 'vitepress'

const props = defineProps<{
  headers: DefaultTheme.OutlineItem[]
  root?: boolean
}>()

const route = useRoute()
const collapsedState = ref<Record<string, boolean>>({})

const activeLink = ref<string | null>(null)

onMounted(() => {
  if (props.root) {

    const markerObserver = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        if (mutation.type === 'attributes' &&
          (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
          syncActiveLinkFromDOM()
          updateMarkerIfInCollapsedSection()
        }
      }
    })

    setTimeout(() => {
      const marker = document.querySelector('.VPDocAsideOutline .outline-marker')
      if (marker) {
        markerObserver.observe(marker, {
          attributes: true,
          attributeFilter: ['style', 'class']
        })
      }
    }, 500)
  }

  window.addEventListener('scrollend', handleScrollEnd, { passive: true })
})

onUnmounted(() => {
  if (props.root) {
    window.removeEventListener('scrollend', handleScrollEnd)
  }
})

function syncActiveLinkFromDOM() {
  const activeElement = document.querySelector('.VPDocAsideOutline .outline-link.active')
  if (activeElement && activeElement instanceof HTMLAnchorElement) {
    activeLink.value = activeElement.getAttribute('href')
    setTimeout(() => updateMarkerIfInCollapsedSection(), 0)
  }
}

let scrollEndTimer: number | null = null
function handleScrollEnd() {
  if (scrollEndTimer) return
  scrollEndTimer = window.setTimeout(() => {
    syncActiveLinkFromDOM()
    scrollEndTimer = null
  }, 100)
}

function updateMarkerIfInCollapsedSection() {
  if (!activeLink.value) return

  const parentLink = isActiveLinkInCollapsedSection(activeLink.value)

  if (parentLink) {
    const parentElement = document.querySelector(`a.outline-link[href="${parentLink}"]`)
    if (parentElement && isElementVisible(parentElement)) {
      updateOutlineMarker(parentElement)
      return true
    }
  }
  return false
}

function isActiveLinkInCollapsedSection(link: string): string | null {

  function checkHeadersRecursively(headers: DefaultTheme.OutlineItem[]): string | null {
    for (const header of headers) {

      if (header.children && collapsedState.value[header.link]) {

        if (isLinkInChildren(link, header.children)) {
          return header.link
        }
      }

      if (header.children && !collapsedState.value[header.link]) {
        const nestedResult = checkHeadersRecursively(header.children)
        if (nestedResult) {
          return nestedResult
        }
      }
    }
    return null
  }

  return checkHeadersRecursively(props.headers)
}

function isLinkInChildren(link: string, children: DefaultTheme.OutlineItem[]): boolean {
  for (const child of children) {
    if (child.link === link) return true
    if (child.children && isLinkInChildren(link, child.children)) return true
  }
  return false
}

function updateActiveLink() {
  const hash = route.hash
  if (hash) {
    activeLink.value = hash
    setTimeout(() => {

      syncActiveLinkFromDOM()

      updateMarkerIfInCollapsedSection()
    }, 100)
  }
}

updateActiveLink()

watch(() => route.path + route.hash, updateActiveLink)

function isActiveLinkChildOf(parentLink: string): boolean {
  if (!activeLink.value) return false

  const parentHeader = props.headers.find(h => h.link === parentLink)
  if (!parentHeader || !parentHeader.children) return false

  function checkChildren(children: DefaultTheme.OutlineItem[]): boolean {
    for (const child of children) {
      if (child.link === activeLink.value) return true
      if (child.children && checkChildren(child.children)) return true
    }
    return false
  }

  return checkChildren(parentHeader.children)
}


async function toggleCollapse(link: string, event: MouseEvent) {
  if (event) {
    event.preventDefault()
    event.stopPropagation()
  }

  const scrollPos = window.scrollY
  const willCollapse = !collapsedState.value[link]
  const activeLinkIsChild = willCollapse && isActiveLinkChildOf(link)

  collapsedState.value[link] = !collapsedState.value[link]

  await nextTick()

  window.scrollTo({
    top: scrollPos,
    behavior: 'auto'
  })

  if (activeLinkIsChild) {
    const parentElement = document.querySelector(`a.outline-link[href="${link}"]`)
    if (parentElement) {
      updateOutlineMarker(parentElement)
    }
    else {
      updateMarkerPosition()
    }
  }

  const activeElement = document.querySelector(`.outline-link[href="${decodeURIComponent(activeLink.value + '')}"]`)
  if (activeElement) {
    activeElement.classList.add('active')
    updateOutlineMarker(activeElement)
  }
}

function updateOutlineMarker(activeElement: Element) {
  const marker = document.querySelector('.VPDocAsideOutline .outline-marker')
  if (marker && marker instanceof HTMLElement) {
    const parentTop = (marker.parentElement as HTMLElement).getBoundingClientRect().top
    const linkTop = activeElement.getBoundingClientRect().top
    const relativeTop = linkTop - parentTop

    marker.style.top = `${relativeTop + 8}px`
    marker.style.opacity = '1'
    marker.style.transition = 'top 0.25s, opacity 0.25s'
  }
}

function onClick({ target: el }: Event) {
  const id = (el as HTMLAnchorElement).href!.split('#')[1]
  const heading = document.getElementById(decodeURIComponent(id))

  activeLink.value = '#' + id

  heading?.focus({ preventScroll: true })

  updateOutlineMarker(el as HTMLElement)
}

function onTransitionEnd() {
  updateMarkerPosition()
}

function findVisibleActiveLink(): Element | null {
  syncActiveLinkFromDOM()

  if (!activeLink.value) return null


  const parentLink = isActiveLinkInCollapsedSection(activeLink.value)
  if (parentLink) {
    const parentElement = document.querySelector(`a.outline-link[href="${parentLink}"]`)
    if (parentElement && isElementVisible(parentElement)) {
      return parentElement
    }
  }

  const directActiveElement = document.querySelector(`.outline-link[href="${decodeURIComponent(activeLink.value + '')}"]`)
  if (directActiveElement && isElementVisible(directActiveElement)) {
    return directActiveElement
  }

  return findVisibleParentOfLink(activeLink.value)
}


function isElementVisible(el: Element): boolean {
  return el instanceof HTMLElement && !!el.offsetParent
}

function updateMarkerPosition() {
  const visibleActiveLink = findVisibleActiveLink()
  if (visibleActiveLink) {
    updateOutlineMarker(visibleActiveLink)
  }
}

function findVisibleParentOfLink(link: string): Element | null {

  let parentLink: string | null = null

  function findParent(headers: DefaultTheme.OutlineItem[], targetLink: string): boolean {
    for (const header of headers) {
      if (header.link === targetLink) return true

      if (header.children) {
        const foundInChildren = findParent(header.children, targetLink)
        if (foundInChildren) {
          parentLink = header.link
          return true
        }
      }
    }
    return false
  }

  findParent(props.headers, link)
  if (parentLink) {
    const parentElement = document.querySelector(`.outline-link[href="${parentLink}"]`)
    if (parentElement && isElementVisible(parentElement)) {
      return parentElement
    }

    return findVisibleParentOfLink(parentLink)
  }

  return null
}
</script>

<template>
  <ul class="VPDocOutlineItem" :class="root ? 'root' : 'nested'">
    <li v-for="{ children, link, title } in headers">
      <div class="outline-item-wrapper">
        <a class="outline-link" :class="{ 'active': activeLink === link }" :href="link" @click="onClick" :title="title">
          {{ title }}
        </a>
        <div v-if="children?.length" class="collapse-control" @click="toggleCollapse(link, $event)">
          <span class="vpi-chevron-right" :class="{ 'chevron-rotate': !collapsedState[link] }" />
        </div>
      </div>

      <transition name="outline-expand" @after-enter="onTransitionEnd" @after-leave="onTransitionEnd">
        <div v-if="children?.length" class="nested-container" :class="{ 'collapsed': collapsedState[link] }">
          <VPDocOutlineItem :headers="children" />
        </div>
      </transition>
    </li>
  </ul>
</template>

<style scoped>
.root {
  position: relative;
  z-index: 1;
}

.collapsed {
  display: none;
}

.nested {
  padding-right: 16px;
  padding-left: 16px;
}

.outline-item-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.outline-link {
  display: block;
  line-height: 32px;
  font-size: 14px;
  font-weight: 400;
  color: var(--vp-c-text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.5s;
  flex: 1;
}

.outline-link:hover,
.outline-link.active {
  color: var(--vp-c-text-1);
  transition: color 0.25s;
}

.outline-link.nested {
  padding-left: 13px;
}

.collapse-control {
  font-size: 18px;
  cursor: pointer;
  user-select: none;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: -7px;
  width: 32px;
  height: 32px;
  color: var(--vp-c-text-3);
  transition: color 0.25s;
  flex-shrink: 0;
}

.collapse-control:hover {
  color: var(--vp-c-text-1);
}

.chevron-rotate {
  transform: rotate(90deg);
}

.vpi-chevron-right {
  transition: transform 0.25s;
}


.outline-expand-enter-active,
.outline-expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.outline-expand-enter-from,
.outline-expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.outline-expand-enter-to,
.outline-expand-leave-from {
  opacity: 1;
  max-height: 1000px;
}

.nested-container {
  overflow: hidden;
}
</style>
