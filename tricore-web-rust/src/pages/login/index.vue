<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Input, Button, message } from 'ant-design-vue'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const employee_no = ref('')
const password = ref('')
const loading = ref(false)

onMounted(() => {
  if (auth.isLoggedIn) {
    router.replace('/dashboard')
  }
})

async function handleLogin() {
  if (!employee_no.value.trim() || !password.value.trim()) {
    message.warning('请输入工号和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(employee_no.value.trim(), password.value)
    router.push('/dashboard')
  } catch (err: any) {
    message.error(err?.response?.data?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- Background decorations -->
    <div class="bg-orb orb-1" />
    <div class="bg-orb orb-2" />
    <div class="bg-orb orb-3" />
    <div class="bg-orb orb-4" />

    <!-- Login card -->
    <div class="login-card">
      <!-- Brand -->
      <div class="brand-area">
        <div class="brand-icon">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <rect width="40" height="40" rx="12" fill="url(#g1)"/>
            <text x="20" y="27" text-anchor="middle" fill="white" font-size="18" font-weight="700">三</text>
            <defs>
              <linearGradient id="g1" x1="0" y1="0" x2="40" y2="40">
                <stop offset="0%" stop-color="#a78bfa"/>
                <stop offset="100%" stop-color="#6c5ce7"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="brand-title">TriCore</h1>
        <p class="brand-sub">三核管理系统</p>
      </div>

      <!-- Divider -->
      <div class="divider">
        <span class="divider-text">账号登录</span>
      </div>

      <!-- Form -->
      <div class="form-area">
        <div class="input-group">
          <Input
            v-model:value="employee_no"
            size="large"
            placeholder="请输入工号"
            class="login-input"
            @pressEnter="handleLogin"
          >
            <template #prefix>
              <UserOutlined class="input-icon" />
            </template>
          </Input>
        </div>

        <div class="input-group">
          <Input.Password
            v-model:value="password"
            size="large"
            placeholder="请输入密码"
            class="login-input"
            @pressEnter="handleLogin"
          >
            <template #prefix>
              <LockOutlined class="input-icon" />
            </template>
          </Input.Password>
        </div>

        <Button
          class="login-btn"
          size="large"
          block
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </Button>
      </div>

      <!-- Footer -->
      <p class="login-footer">TriCore &copy; 2026</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #f5f3ff 0%, #ede9fe 25%, #f0f9ff 50%, #fdf2f8 75%, #f5f3ff 100%);
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* Background decorative orbs */
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
  pointer-events: none;
}
.orb-1 {
  width: 360px; height: 360px;
  background: rgba(167, 139, 250, 0.25);
  top: -100px; right: -80px;
  animation: float1 12s ease-in-out infinite;
}
.orb-2 {
  width: 280px; height: 280px;
  background: rgba(108, 92, 231, 0.2);
  bottom: -80px; left: -60px;
  animation: float2 14s ease-in-out infinite;
}
.orb-3 {
  width: 200px; height: 200px;
  background: rgba(236, 72, 153, 0.12);
  top: 40%; left: -40px;
  animation: float3 16s ease-in-out infinite;
}
.orb-4 {
  width: 220px; height: 220px;
  background: rgba(56, 189, 248, 0.15);
  bottom: 20%; right: -50px;
  animation: float1 18s ease-in-out infinite reverse;
}

@keyframes float1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}
@keyframes float2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-25px, -20px) scale(1.08); }
  66% { transform: translate(25px, 15px) scale(0.92); }
}
@keyframes float3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(15px, 40px) scale(1.06); }
}

/* Card */
.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  padding: 48px 44px 36px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 24px;
  box-shadow:
    0 4px 24px rgba(108, 92, 231, 0.06),
    0 12px 48px rgba(108, 92, 231, 0.04),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  animation: cardIn 0.6s ease-out;
}

@keyframes cardIn {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Brand */
.brand-area {
  text-align: center;
  margin-bottom: 28px;
}
.brand-icon {
  display: inline-flex;
  margin-bottom: 14px;
  filter: drop-shadow(0 4px 8px rgba(108, 92, 231, 0.2));
}
.brand-title {
  font-size: 26px;
  font-weight: 700;
  color: #1e1b4b;
  letter-spacing: -0.5px;
  margin: 0 0 4px 0;
  background: linear-gradient(135deg, #6c5ce7, #a78bfa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.brand-sub {
  font-size: 13px;
  color: #8b8bab;
  margin: 0;
  letter-spacing: 2px;
}

/* Divider */
.divider {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}
.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, #e2e0f0, transparent);
}
.divider-text {
  padding: 0 16px;
  font-size: 12px;
  color: #a5a3c0;
  letter-spacing: 1px;
}

/* Form */
.form-area {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.input-group :deep(.login-input) {
  border-radius: 12px;
  border-color: #e8e6f5;
  transition: all 0.25s ease;
  background: rgba(248, 247, 255, 0.6);
}
.input-group :deep(.login-input:hover) {
  border-color: #c4b5fd;
}
.input-group :deep(.login-input:focus),
.input-group :deep(.login-input.ant-input-affix-wrapper-focused) {
  border-color: #a78bfa;
  box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.1);
  background: rgba(255, 255, 255, 0.9);
}
.input-group :deep(.ant-input) {
  background: transparent;
  font-size: 14px;
}
.input-group :deep(.ant-input-prefix) {
  margin-right: 10px;
}
.input-icon {
  color: #b8b5d0;
  font-size: 16px;
}

.login-btn {
  height: 46px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 4px;
  border: none;
  background: linear-gradient(135deg, #a78bfa 0%, #6c5ce7 100%);
  box-shadow: 0 4px 16px rgba(108, 92, 231, 0.25);
  transition: all 0.3s ease;
  margin-top: 4px;
}
.login-btn:hover {
  background: linear-gradient(135deg, #b49ffc 0%, #7c6ff0 100%);
  box-shadow: 0 6px 24px rgba(108, 92, 231, 0.35);
  transform: translateY(-1px);
}
.login-btn:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(108, 92, 231, 0.2);
}

/* Footer */
.login-footer {
  text-align: center;
  font-size: 12px;
  color: #c0bed8;
  margin: 24px 0 0 0;
  letter-spacing: 0.5px;
}

/* Dark mode */
:global([data-theme="dark"]) .login-page {
  background: linear-gradient(160deg, #0f0b1a 0%, #13102a 25%, #0c1422 50%, #1a1022 75%, #0f0b1a 100%);
}
:global([data-theme="dark"]) .orb-1 {
  background: rgba(108, 92, 231, 0.15);
}
:global([data-theme="dark"]) .orb-2 {
  background: rgba(167, 139, 250, 0.1);
}
:global([data-theme="dark"]) .orb-3 {
  background: rgba(236, 72, 153, 0.07);
}
:global([data-theme="dark"]) .orb-4 {
  background: rgba(56, 189, 248, 0.08);
}
:global([data-theme="dark"]) .login-card {
  background: rgba(22, 20, 44, 0.7);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(108, 92, 231, 0.08) inset;
}
:global([data-theme="dark"]) .brand-title {
  background: linear-gradient(135deg, #a78bfa, #c4b5fd);
  -webkit-background-clip: text;
  background-clip: text;
}
:global([data-theme="dark"]) .brand-sub {
  color: #6b6a8a;
}
:global([data-theme="dark"]) .divider::before,
:global([data-theme="dark"]) .divider::after {
  background: linear-gradient(90deg, transparent, #2a2748, transparent);
}
:global([data-theme="dark"]) .divider-text {
  color: #6b6a8a;
}
:global([data-theme="dark"]) .input-group :deep(.login-input) {
  border-color: #2a2748;
  background: rgba(18, 16, 34, 0.5);
}
:global([data-theme="dark"]) .input-group :deep(.login-input:hover) {
  border-color: #4a3780;
}
:global([data-theme="dark"]) .input-group :deep(.login-input:focus),
:global([data-theme="dark"]) .input-group :deep(.login-input.ant-input-affix-wrapper-focused) {
  border-color: #7c6ff0;
  box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.15);
  background: rgba(22, 20, 44, 0.8);
}
:global([data-theme="dark"]) .input-group :deep(.ant-input) {
  color: #e2e0f0;
}
:global([data-theme="dark"]) .login-footer {
  color: #4a4868;
}
</style>
