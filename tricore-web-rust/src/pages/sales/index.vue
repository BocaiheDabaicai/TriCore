<script setup lang="ts">
const columns = [
  { title: '订单编号', dataIndex: 'orderNo', key: 'orderNo' },
  { title: '客户名称', dataIndex: 'customer', key: 'customer' },
  { title: '金额', dataIndex: 'amount', key: 'amount' },
  { title: '状态', dataIndex: 'status', key: 'status' },
]
</script>

<template>
  <div>
    <h2 style="margin-bottom: 24px">销售管理</h2>
    <a-card title="订单列表">
      <a-table
        :columns="columns"
        :data-source="[]"
        row-key="id"
        :pagination="false"
      >
        <template #emptyText>
          暂无数据，请先连接数据库
        </template>
      </a-table>
    </a-card>
  </div>
</template>
