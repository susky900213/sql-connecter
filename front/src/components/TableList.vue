<template>
  <div class="table-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据库表列表 - {{ databaseName }}</span>
          <el-input 
            v-model="searchQuery" 
            placeholder="模糊查询表名..."
            style="width: 200px; margin-right: 10px;"
          />
          <el-button type="primary" size="small" @click="goBack">返回</el-button>
        </div>
      </template>
      
      <div v-if="loading" style="text-align: center; padding: 20px;">
        <el-skeleton :rows="5" animated />
      </div>
      
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      
      <el-table 
        v-else-if="filteredTables.length > 0"
        :data="filteredTables" 
        border
        style="width: 100%"
        size="small"
      >
        <el-table-column prop="name" label="表名" />
        <el-table-column prop="engine" label="引擎" />
        <el-table-column label="操作" width="400">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small"
              @click="showTableStructure(scope.row.name)"
            >
              查看表结构
            </el-button>
            <el-button 
              type="success" 
              size="small"
              style="margin-left: 5px;"
              @click="importCSV(scope.row.name)"
            >
              导入CSV
            </el-button>
            <el-button 
              type="warning" 
              size="small"
              style="margin-left: 5px;"
              @click="importSQL(scope.row.name)"
            >
              导入SQL
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <p v-else style="text-align: center; padding: 20px;">当前数据库中没有表</p>
    </el-card>

    <!-- 表结构模态框 -->
    <el-dialog
      :model-value="showStructureModal"
      :title="structureDialogTitle"
      width="70%"
      @close="closeStructureModal"
    >
      <div v-if="currentTableStructure">
        <h3>建表语句</h3>
        <el-input 
          type="textarea" 
          :rows="20" 
          :value="currentTableStructure.createStatement"
          readonly
        />
      </div>
    </el-dialog>
    
    <!-- CSV导入模态框 -->
    <CSVImportModal
      v-model:visible="showCSVImportDialog"
      :database-name="databaseName"
      :table-name="importTargetTableName"
      @import-success="$emit('refresh-tables')"
    />
    
    <!-- SQL导入模态框 -->
    <SQLImportModal
      v-model:visible="showSQLImportDialog"
      :database-name="databaseName"
      :table-name="importTargetTableName"
      @import-success="$emit('refresh-tables')"
    />
  </div>
</template>

<script>
import { ElCard, ElButton, ElSkeleton, ElTable, ElTableColumn, ElDialog, ElInput, ElMessage } from 'element-plus'
import ModalDialog from './ModalDialog.vue'
import CSVImportModal from './CSVImportModal.vue'
import SQLImportModal from './SQLImportModal.vue'

export default {
  name: 'TableList',
  components: {
    ModalDialog,
    CSVImportModal,
    SQLImportModal,
    ElCard,
    ElButton,
    ElSkeleton,
    ElTable,
    ElTableColumn,
    ElDialog,
    ElInput
  },
  props: {
    databaseName: {
      type: String,
      required: true
    },
    connectionInfo: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      tables: [],
      loading: false,
      error: null,
      showStructureModal: false,
      currentTableStructure: null,
      structureDialogTitle: '',
      // 导入相关的数据
      showCSVImportDialog: false,
      showSQLImportDialog: false,
      importTargetTableName: '',
      searchQuery: ''
    }
  },
  computed: {
    filteredTables() {
      if (!this.searchQuery) {
        return this.tables;
      }
      const query = this.searchQuery.toLowerCase();
      return this.tables.filter(table => 
        table.name.toLowerCase().includes(query)
      );
    }
  },
  mounted() {
    this.fetchTables()
  },
  methods: {
    async fetchTables() {
      this.loading = true
      this.error = null
      
      try {
        // 调用API获取数据库中的所有表信息
        const response = await fetch(`http://localhost:5050/api/databases/${this.databaseName}/tables`)
        
        if (response.ok) {
          const result = await response.json()
          
          if (result.success && result.data) {
            // 格式化返回的数据以适配显示
            this.tables = result.data.map(table => ({
              name: table,
              engine: 'InnoDB', // 由于API没有提供引擎信息，使用默认值
              rowCount: 0,      // 由于API没有提供行数信息，使用默认值
              createTime: ''    // 由于API没有提供创建时间，使用空字符串
            }))
          } else {
            this.error = result.error || '获取表列表失败'
          }
        } else {
          const errorData = await response.json()
          this.error = errorData.error || `HTTP错误: ${response.status}`
        }
      } catch (error) {
        console.error('获取表列表失败:', error)
        this.error = '无法获取数据库中的表信息，请检查网络连接或后端服务'
      } finally {
        this.loading = false
      }
    },
    
    formatDate(date) {
      if (!date) return ''
      const d = new Date(date)
      return d.toLocaleDateString('zh-CN')
    },
    
    goBack() {
      // 返回到之前的页面，这里可以使用路由或简单的返回逻辑
      this.$emit('back')
    },
    
    async showTableStructure(tableName) {
      this.structureDialogTitle = `表 "${tableName}" 的结构`;
      this.loading = true;
      
      try {
        // 调用API获取指定表的结构信息
        const response = await fetch(`http://localhost:5050/api/databases/${this.databaseName}/tables/${tableName}/structure`);
        
        if (response.ok) {
          const result = await response.json();
          
          if (result.success && result.data) {
            // 根据API文档格式调整数据结构
            this.currentTableStructure = {
              createStatement: result.data.create_table_sql || '',
              indexes: result.data.indexes || []
            };
            this.showStructureModal = true;
          } else {
            this.error = result.error || '获取表结构失败';
          }
        } else {
          const errorData = await response.json();
          this.error = errorData.error || `HTTP错误: ${response.status}`;
        }
      } catch (error) {
        console.error('获取表结构失败:', error);
        this.error = '无法获取表结构信息，请检查网络连接或后端服务';
      } finally {
        this.loading = false;
      }
    },
    
    closeStructureModal() {
      this.showStructureModal = false;
      this.currentTableStructure = null;
    },
    
    // 导入CSV方法
    importCSV(tableName) {
      this.importTargetTableName = tableName;
      this.showCSVImportDialog = true;
    },
    
    // 导入SQL方法
    importSQL(tableName) {
      this.importTargetTableName = tableName;
      this.showSQLImportDialog = true;
    }
  }
}
</script>

<style scoped>
.table-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error {
  color: #f44336;
  text-align: center;
  padding: 20px;
}

.index-item {
  margin-bottom: 15px;
}
</style>
