<script setup lang="ts">
import { ref, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  DashboardOutlined,
  ShoppingCartOutlined,
  TeamOutlined,
  DatabaseOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)

const menuItems = [
  { key: '/dashboard', icon: () => h(DashboardOutlined), label: '工作台' },
  { key: '/sales', icon: () => h(ShoppingCartOutlined), label: '销售管理' },
  { key: '/oa', icon: () => h(TeamOutlined), label: '办公协同' },
  { key: '/inventory', icon: () => h(DatabaseOutlined), label: '库存管理' },
]

function onMenuClick({ key }: { key: string }) {
  router.push(key)
}
</script>

<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible trigger="null">
      <div class="logo">
        {{ collapsed ? '三核' : 'TriCore 三核' }}
      </div>
      <a-menu
        theme="dark"
        mode="inline"
        :selected-keys="[route.path]"
        :items="menuItems"
        @click="onMenuClick"
      />
    </a-layout-sider>
    <a-layout>
      <a-layout-header class="header">
        <menu-unfold-outlined
          v-if="collapsed"
          class="trigger"
          @click="collapsed = false"
        />
        <menu-fold-outlined
          v-else
          class="trigger"
          @click="collapsed = true"
        />
        <span class="title">TriCore 三核管理系统</span>
      </a-layout-header>
      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<style scoped>
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
  transition: font-size 0.2s;
}
.header {
  padding: 0 24px;
  background: #fff;
  display: flex;
  align-items: center;
}
.trigger {
  font-size: 18px;
  cursor: pointer;
}
.title {
  margin-left: 16px;
  font-size: 16px;
  font-weight: 500;
}
.content {
  margin: 24px;
  padding: 24px;
  background: #fff;
  border-radius: 8px;
  overflow: auto;
}
</style>
