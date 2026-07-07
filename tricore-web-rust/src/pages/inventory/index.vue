<script setup lang="ts">
const columns = [
  { title: 'SKU', dataIndex: 'sku', key: 'sku' },
  { title: '商品名称', dataIndex: 'name', key: 'name' },
  { title: '库存数量', dataIndex: 'quantity', key: 'quantity' },
  { title: '单价', dataIndex: 'price', key: 'price' },
  { title: '状态', dataIndex: 'quantity', key: 'status' },
]
</script>

<template>
  <div>
    <h2 style="margin-bottom: 24px">库存管理</h2>
    <a-card title="商品列表">
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
