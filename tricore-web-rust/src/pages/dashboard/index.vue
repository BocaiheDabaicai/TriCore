<script setup lang="ts">
import {
  ShoppingCartOutlined,
  TeamOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue'

const stats = [
  { title: '销售订单', value: 0, icon: ShoppingCartOutlined, color: '#1677ff' },
  { title: '员工数量', value: 0, icon: TeamOutlined, color: '#52c41a' },
  { title: '商品种类', value: 0, icon: DatabaseOutlined, color: '#fa8c16' },
  { title: '本月完成', value: 0, icon: CheckCircleOutlined, color: '#722ed1' },
]
</script>

<template>
  <div>
    <h2 style="margin-bottom: 24px">工作台</h2>
    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :sm="12" :lg="6" v-for="item in stats" :key="item.title">
        <a-card>
          <a-statistic
            :title="item.title"
            :value="item.value"
            :value-style="{ color: item.color }"
          >
            <template #prefix>
              <component :is="item.icon" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>
    <a-card style="margin-top: 24px">
      <h3>欢迎使用 TriCore 三核管理系统</h3>
      <p>
        集成 <strong>销售管理</strong>、<strong>办公协同</strong>、<strong>库存管理</strong>
        三大核心业务模块，助力企业高效运营。
      </p>
    </a-card>
  </div>
</template>
