<script setup>
import { ref, watch } from 'vue'
import DataTable from './components/DataTable.vue'
import TableList from './components/TableList.vue'
import SQLExecutor from './components/SQLExecutor.vue'
import SQLExecutorPage from './components/SQLExecutorPage.vue'

const currentView = ref('dataTable') // 'dataTable', 'tableList' 或 'sqlExecutor'
const selectedDatabase = ref(null)
const sqlQueryFromURL = ref('')

// 从 URL 参数中读取数据库信息
const initFromURL = () => {
  const urlParams = new URLSearchParams(window.location.search)
  const dbName = urlParams.get('db')
  const sqlParam = urlParams.get('sql')
  
  if (dbName) {
    // 这里应该根据实际需要获取数据库详情，简单起见我们用模拟数据
    selectedDatabase.value = {
      name: dbName,
      host: 'localhost',
      port: 3306,
      database: dbName,
      user: 'user'
    }
    
    // 如果有SQL参数，则显示SQL执行页面
    if (sqlParam) {
      sqlQueryFromURL.value = sqlParam
      currentView.value = 'sqlExecutorPage'
    } else {
      currentView.value = 'sqlExecutor'
    }
  }
}

// 初始化视图
initFromURL()

const handleViewTables = (databaseInfo) => {
  selectedDatabase.value = databaseInfo
  currentView.value = 'tableList'
}

const handleExecuteSQL = (databaseInfo) => {
  // 在新窗口中打开执行页面
  const url = new URL(window.location)
  url.searchParams.set('db', databaseInfo.name)
  window.open(url.toString(), '_blank')
}

const handleBack = () => {
  currentView.value = 'dataTable'
  selectedDatabase.value = null
}
</script>

<template>
  <div class="app">
    <DataTable 
      v-if="currentView === 'dataTable'" 
      @view-tables="handleViewTables"
      @execute-sql="handleExecuteSQL"
    />
    <TableList 
      v-else-if="currentView === 'tableList'"
      :database-name="selectedDatabase.name" 
      :connection-info="selectedDatabase"
      @back="handleBack"
    />
    <SQLExecutor 
      v-else-if="currentView === 'sqlExecutor'"
      :connection-info="selectedDatabase"
      @back="handleBack"
    />
    <SQLExecutorPage 
      v-else
      :connection-info="selectedDatabase"
      :sql-query-from-parent="sqlQueryFromURL"
      @back="handleBack"
    />
  </div>
</template>

<style scoped>
.app {
  margin: 20px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}
</style>
