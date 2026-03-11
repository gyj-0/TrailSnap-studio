<template>
  <div class="train-ticket" :class="{ 'ticket-small': size === 'small', 'ticket-large': size === 'large' }">
    <div class="ticket-body" :style="ticketStyle">
      <div class="ticket-stub">
        <span class="train-type">{{ trainType }}</span>
        <span class="train-number">{{ displayNumber }}</span>
      </div>
      <div class="ticket-route">
        <div class="station from">{{ fromStation || '始发' }}</div>
        <div class="arrow">
          <el-icon><Right /></el-icon>
        </div>
        <div class="station to">{{ toStation || '终点' }}</div>
      </div>
      <div v-if="showTime" class="ticket-time">
        <el-icon><Clock /></el-icon>
        <span>{{ departureTime }}</span>
      </div>
    </div>
    <div class="ticket-hole ticket-hole-left"></div>
    <div class="ticket-hole ticket-hole-right"></div>
    <div class="ticket-notch ticket-notch-left"></div>
    <div class="ticket-notch ticket-notch-right"></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Right, Clock } from '@element-plus/icons-vue'

type TrainType = 'G' | 'D' | 'C' | 'Z' | 'T' | 'K' | 'L' | 'Y' | 'S' | 'N'

interface Props {
  trainNumber?: string
  fromStation?: string
  toStation?: string
  departureTime?: string
  showTime?: boolean
  size?: 'small' | 'default' | 'large'
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  trainNumber: '',
  fromStation: '',
  toStation: '',
  departureTime: '',
  showTime: false,
  size: 'default',
  color: ''
})

const trainType = computed<TrainType>(() => {
  const type = props.trainNumber.charAt(0) as TrainType
  const validTypes: TrainType[] = ['G', 'D', 'C', 'Z', 'T', 'K', 'L', 'Y', 'S', 'N']
  return validTypes.includes(type) ? type : 'K'
})

const displayNumber = computed(() => {
  return props.trainNumber || '----'
})

const ticketColor = computed(() => {
  if (props.color) return props.color
  
  const colorMap: Record<TrainType, string> = {
    'G': '#e53935', // 高铁 - 红色
    'D': '#ff9800', // 动车 - 橙色
    'C': '#2196f3', // 城际 - 蓝色
    'Z': '#9c27b0', // 直达 - 紫色
    'T': '#4caf50', // 特快 - 绿色
    'K': '#795548', // 快速 - 棕色
    'L': '#607d8b', // 临客 - 灰蓝
    'Y': '#00bcd4', // 旅游 - 青色
    'S': '#ff5722', // 市郊 - 深橙
    'N': '#8bc34a'  // 管内 - 浅绿
  }
  return colorMap[trainType.value] || '#757575'
})

const ticketStyle = computed(() => ({
  '--ticket-color': ticketColor.value
}))

const typeText = computed(() => {
  const textMap: Record<TrainType, string> = {
    'G': '高速',
    'D': '动车',
    'C': '城际',
    'Z': '直达',
    'T': '特快',
    'K': '快速',
    'L': '临客',
    'Y': '旅游',
    'S': '市郊',
    'N': '管内'
  }
  return textMap[trainType.value] || '普速'
})
</script>

<style scoped>
.train-ticket {
  display: inline-flex;
  position: relative;
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.ticket-body {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  background: linear-gradient(135deg, var(--ticket-color) 0%, 
    color-mix(in srgb, var(--ticket-color) 85%, black) 100%);
  border-radius: 8px;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.ticket-body::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 10px,
    rgba(255, 255, 255, 0.03) 10px,
    rgba(255, 255, 255, 0.03) 20px
  );
}

.ticket-stub {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-right: 16px;
  border-right: 1px dashed rgba(255, 255, 255, 0.3);
}

.train-type {
  font-size: 10px;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.train-number {
  font-size: 20px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 1px;
}

.ticket-route {
  display: flex;
  align-items: center;
  gap: 12px;
}

.station {
  font-size: 14px;
  font-weight: 500;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow {
  opacity: 0.8;
}

.ticket-time {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-left: 16px;
  border-left: 1px dashed rgba(255, 255, 255, 0.3);
  font-size: 13px;
  font-family: 'Roboto Mono', monospace;
}

/* Holes and notches for realistic ticket look */
.ticket-hole {
  position: absolute;
  width: 12px;
  height: 12px;
  background: var(--bg-base);
  border-radius: 50%;
  top: 50%;
  transform: translateY(-50%);
}

.ticket-hole-left {
  left: -6px;
}

.ticket-hole-right {
  right: -6px;
}

.ticket-notch {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--bg-base);
  border-radius: 50%;
  top: 4px;
}

.ticket-notch-left {
  left: 4px;
}

.ticket-notch-right {
  right: 4px;
}

/* Size variants */
.ticket-small .ticket-body {
  padding: 8px 14px;
  gap: 10px;
}

.ticket-small .ticket-stub {
  padding-right: 10px;
}

.ticket-small .train-number {
  font-size: 14px;
}

.ticket-small .station {
  font-size: 12px;
  max-width: 60px;
}

.ticket-small .ticket-time {
  display: none;
}

.ticket-large .ticket-body {
  padding: 16px 28px;
  gap: 24px;
}

.ticket-large .ticket-stub {
  padding-right: 24px;
}

.ticket-large .train-number {
  font-size: 28px;
}

.ticket-large .station {
  font-size: 16px;
  max-width: 120px;
}

/* Animation */
.train-ticket:hover .ticket-body {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.ticket-body {
  transition: transform 0.2s, box-shadow 0.2s;
}
</style>
