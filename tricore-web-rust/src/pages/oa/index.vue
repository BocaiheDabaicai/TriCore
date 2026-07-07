<script setup lang="ts">
const columns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '部门', dataIndex: 'department', key: 'department' },
  { title: '职位', dataIndex: 'position', key: 'position' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '状态', dataIndex: 'status', key: 'status' },
]
</script>

<template>
  <div>
    <h2 style="margin-bottom: 24px">办公协同</h2>
    <a-card title="员工列表">
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
