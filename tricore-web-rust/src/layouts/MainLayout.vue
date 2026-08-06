<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Popover, Tag, Button } from 'ant-design-vue'
import {
  DashboardOutlined,
  ShoppingCartOutlined,
  AuditOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  MailOutlined,
  PhoneOutlined,
  IdcardOutlined,
  TeamOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  RobotOutlined,
  HistoryOutlined,
  LogoutOutlined,
} from '@ant-design/icons-vue'
import AiFloatingChat from '@/components/AiFloatingChat.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const collapsed = ref(false)
const isDark = ref(true)
const auth = useAuthStore()
const userHovered = ref(false)

onMounted(async () => {
  const saved = localStorage.getItem('theme')
  isDark.value = saved ? saved === 'dark' : true
  applyTheme()
  if (auth.token && !auth.user) {
    await auth.fetchCurrentUser()
  }
})

function applyTheme() {
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

function toggleTheme() {
  isDark.value = !isDark.value
  applyTheme()
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}

const menuItems = [
  { key: '/dashboard', icon: () => h(DashboardOutlined), label: '工作台' },
  { key: '/sales',     icon: () => h(ShoppingCartOutlined), label: '销售管理' },
  { key: '/oa',       icon: () => h(AuditOutlined), label: '办公协同' },
  { key: '/inventory', icon: () => h(DatabaseOutlined), label: '库存管理' },
  { key: '/regulations', icon: () => h(FileTextOutlined), label: '规章制度' },
  { key: '/data-snapshots', icon: () => h(HistoryOutlined), label: '数据快照' },
  {
    key: 'ai', icon: () => h(RobotOutlined), label: 'AI管理',
    children: [
      { key: '/ai/config', label: 'AI 配置' },
      { key: '/ai/mcp', label: 'MCP 服务' },
    ],
  },
  {
    key: 'master-data', icon: () => h(SettingOutlined), label: '基础数据',
    children: [
      { key: '/master-data/customers', label: '客户管理' },
      { key: '/master-data/departments', label: '部门管理' },
      { key: '/master-data/positions', label: '职位管理' },
      { key: '/master-data/vehicles', label: '车辆管理' },
      { key: '/master-data/users', label: '用户管理' },
      { key: '/master-data/warehouses', label: '仓库管理' },
    ],
  },
]

const openKeys = ref<string[]>([])
const updateOpenKeys = () => {
  if (route.path.startsWith('/master-data')) openKeys.value = ['master-data']
  if (route.path.startsWith('/ai')) openKeys.value = ['ai']
}
updateOpenKeys()

const currentLabel = () => {
  const found = menuItems.find(m => m.key === route.path)
  if (found) return found.label
  for (const m of menuItems) {
    if (m.children) {
      const child = m.children.find((c: any) => c.key === route.path)
      if (child) return child.label
    }
  }
  return 'TriCore'
}

function onMenuClick({ key }: { key: string }) { router.push(key) }
</script>

<template>
  <a-layout has-sider :style="{ background: 'var(--bg-primary)', minHeight: '100vh' }">
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      :width="230"
      :collapsed-width="60"
      :trigger="null"
      :style="{ background: 'var(--sidebar-bg)' }"
    >
      <!-- Logo area -->
      <div
        class="h-16 flex items-center justify-center gap-2 cursor-pointer select-none"
        @click="router.push('/dashboard')"
        :style="{ borderBottom: '1px solid var(--border-subtle)' }"
      >
        <span v-if="collapsed" class="text-xl font-bold gradient-text">三</span>
        <template v-else>
          <span class="text-xl font-bold gradient-text tracking-tight">TriCore</span>
          <span class="text-xs font-medium px-1.5 py-0.5 rounded-md" :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">三核</span>
        </template>
      </div>

      <!-- Menu -->
      <a-menu
        theme="dark"
        mode="inline"
        :selected-keys="[route.path]"
        :open-keys="openKeys"
        :items="menuItems"
        @click="onMenuClick"
        @update:openKeys="(keys: string[]) => openKeys = keys"
        :style="{ background: 'transparent', borderInlineEnd: 'none', padding: '8px' }"
      />

      <!-- Collapse toggle -->
      <div class="absolute bottom-4 left-0 right-0 flex justify-center">
        <button
          class="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200"
          :style="{ color: 'var(--text-muted)', border: 'none', background: 'transparent', cursor: 'pointer' }"
          @click="collapsed = !collapsed"
        >
          <MenuUnfoldOutlined v-if="collapsed" />
          <MenuFoldOutlined v-else />
        </button>
      </div>
    </a-layout-sider>

    <a-layout :style="{ background: 'transparent' }">
      <!-- Header -->
      <div
        class="h-16 flex items-center justify-between px-8 sticky top-0 z-10"
        :style="{
          background: 'var(--bg-card)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid var(--border-subtle)',
        }"
      >
        <div class="flex items-center gap-3">
          <span class="text-sm font-semibold tracking-wide" :style="{ color: 'var(--text-primary)' }">{{ currentLabel() }}</span>
          <span class="text-xs px-2 py-0.5 rounded-full" :style="{ background: 'var(--accent-soft)', color: 'var(--accent)' }">TriCore</span>
        </div>

        <div class="flex items-center gap-3">
          <!-- User Profile -->
          <Popover
            v-if="auth.currentUser"
            trigger="hover"
            placement="bottomRight"
            :overlayStyle="{ maxWidth: '300px' }"
          >
            <template #content>
              <div class="min-w-56">
                <div class="flex items-center gap-3 mb-3 pb-3 border-b" :style="{ borderColor: 'var(--border-subtle)' }">
                  <div class="w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold text-white flex-shrink-0"
                    style="background: linear-gradient(135deg, #6c5ce7, #a78bfa)">
                    {{ auth.currentUser.name?.charAt(0) }}
                  </div>
                  <div>
                    <p class="font-semibold text-sm" :style="{ color: 'var(--text-primary)' }">{{ auth.currentUser.name }}</p>
                    <p class="text-xs" :style="{ color: 'var(--text-muted)' }">{{ auth.currentUser.position }}</p>
                  </div>
                </div>
                <div class="space-y-2 text-xs">
                  <div class="flex items-center gap-2" :style="{ color: 'var(--text-secondary)' }">
                    <IdcardOutlined :style="{ color: 'var(--accent)' }" />
                    <span :style="{ color: 'var(--text-muted)' }">工号</span>
                    <span :style="{ color: 'var(--text-primary)', fontFamily: 'ui-monospace, monospace' }">{{ auth.currentUser.employee_no }}</span>
                  </div>
                  <div class="flex items-center gap-2" :style="{ color: 'var(--text-secondary)' }">
                    <TeamOutlined :style="{ color: 'var(--accent)' }" />
                    <span :style="{ color: 'var(--text-muted)' }">部门</span>
                    <Tag>{{ auth.currentUser.department }}</Tag>
                  </div>
                  <div class="flex items-center gap-2" :style="{ color: 'var(--text-secondary)' }">
                    <MailOutlined :style="{ color: 'var(--accent)' }" />
                    <span :style="{ color: 'var(--text-muted)' }">邮箱</span>
                    <span :style="{ color: 'var(--text-primary)' }">{{ auth.currentUser.email }}</span>
                  </div>
                  <div v-if="auth.currentUser.phone" class="flex items-center gap-2" :style="{ color: 'var(--text-secondary)' }">
                    <PhoneOutlined :style="{ color: 'var(--accent)' }" />
                    <span :style="{ color: 'var(--text-muted)' }">电话</span>
                    <span :style="{ color: 'var(--text-primary)' }">{{ auth.currentUser.phone }}</span>
                  </div>
                  <div class="flex items-center gap-2" :style="{ color: 'var(--text-secondary)' }">
                    <SafetyCertificateOutlined :style="{ color: 'var(--success)' }" />
                    <span :style="{ color: 'var(--text-muted)' }">状态</span>
                    <Tag color="green">在职</Tag>
                  </div>
                </div>
                <div class="mt-3 pt-2 border-t" :style="{ borderColor: 'var(--border-subtle)' }">
                  <Button type="link" size="small" danger block @click="handleLogout">
                    <LogoutOutlined /> 退出登录
                  </Button>
                </div>
              </div>
            </template>
            <div
              class="flex items-center gap-2 cursor-pointer rounded-lg px-2 py-1.5 transition-all duration-200 select-none"
              :style="{
                border: `1px solid ${userHovered ? 'var(--border-subtle)' : 'transparent'}`,
                background: userHovered ? 'var(--input-bg)' : 'transparent',
              }"
              @mouseenter="userHovered = true"
              @mouseleave="userHovered = false"
            >
              <div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                style="background: linear-gradient(135deg, #6c5ce7, #a78bfa)">
                {{ auth.currentUser.name?.charAt(0) }}
              </div>
              <div class="text-left leading-tight hidden sm:block">
                <p class="text-xs font-semibold" :style="{ color: 'var(--text-primary)' }">{{ auth.currentUser.name }}</p>
                <p class="text-xs" :style="{ color: 'var(--text-muted)' }">{{ auth.currentUser.department }}</p>
              </div>
            </div>
          </Popover>

          <!-- No user fallback -->
          <div
            v-else
            class="w-8 h-8 rounded-full flex items-center justify-center"
            :style="{ background: 'var(--input-bg)', color: 'var(--text-muted)' }"
          >
            <UserOutlined />
          </div>

          <button class="theme-toggle-btn" @click="toggleTheme" :title="isDark ? '切换亮色模式' : '切换暗色模式'">
            {{ isDark ? '☀️' : '🌙' }}
          </button>
        </div>
      </div>

      <!-- Content -->
      <a-layout-content :style="{ background: 'transparent' }">
        <div class="px-8 py-6">
          <router-view />
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>

  <!-- AI Floating Chat -->
  <AiFloatingChat />
</template>
