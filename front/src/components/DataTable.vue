<template>
  <div class="data-table">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据库连接列表</span>
          <el-button type="primary" @click="openAddModal">添加数据库</el-button>
        </div>
      </template>

      <!-- 模态框 -->
      <el-dialog
        :model-value="showModal"
        title="添加数据库"
        width="40%"
        @close="closeAddModal"
      >
        <el-form 
          :model="newItem" 
          label-position="top"
          size="small"
          ref="addFormRef"
        >
          <el-form-item label="连接名称" prop="name">
            <el-input v-model="newItem.name" />
          </el-form-item>
          
          <el-form-item label="主机地址" prop="host">
            <el-input v-model="newItem.host" />
          </el-form-item>
          
          <el-form-item label="端口" prop="port">
            <el-input-number v-model="newItem.port" :min="1" :max="65535" />
          </el-form-item>
          
          <el-form-item label="数据库名" prop="database">
            <el-input v-model="newItem.database" />
          </el-form-item>
          
          <el-form-item label="用户名" prop="user">
            <el-input v-model="newItem.user" />
          </el-form-item>
          
          <el-form-item label="密码" prop="password">
            <el-input v-model="newItem.password" type="password" />
          </el-form-item>
        </el-form>
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="closeAddModal">取消</el-button>
            <el-button 
              type="primary" 
              @click="confirmAdd"
              :loading="loading"
            >
              确定
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 详情模态框 -->
      <el-dialog
        :model-value="showDetailModal"
        title="数据库连接详情"
        width="40%"
        @close="closeDetailModal"
      >
        <div v-if="selectedItem">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="连接名称">{{ selectedItem.name }}</el-descriptions-item>
            <el-descriptions-item label="主机地址">{{ selectedItem.host }}</el-descriptions-item>
            <el-descriptions-item label="端口">{{ selectedItem.port }}</el-descriptions-item>
            <el-descriptions-item label="数据库名">{{ selectedItem.database }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ selectedItem.user }}</el-descriptions-item>
            <el-descriptions-item label="密码">{{ selectedItem.password }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-dialog>

      <el-table 
        v-if="items.length > 0"
        :data="items" 
        border
        style="width: 100%"
        size="small"
      >
        <el-table-column prop="name" label="连接名称" />
        <el-table-column prop="host" label="主机地址" />
        <el-table-column prop="port" label="端口" />
        <el-table-column prop="database" label="数据库名" />
        <el-table-column prop="user" label="用户名" />
        <el-table-column label="操作" width="250">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small"
              @click="viewDetails(scope.row)"
            >
              查看详情
            </el-button>
            <el-button 
              type="success" 
              size="small"
              @click="viewTables(scope.row)"
            >
              查看表
            </el-button>
            <el-button 
              type="warning" 
              size="small"
              @click="executeSQL(scope.row)"
            >
              执行
            </el-button>
            <el-popconfirm
              title="确定要删除这个数据库连接吗？"
              @confirm="deleteItem(scope.row)"
            >
              <template #reference>
                <el-button type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
      
      <p v-else style="text-align: center; padding: 20px;">暂无数据库连接配置</p>
    </el-card>
  </div>
</template>

<script>
import { ElCard, ElButton, ElDialog, ElForm, ElFormItem, ElInput, ElInputNumber, ElTable, ElTableColumn, ElDescriptions, ElDescriptionsItem, ElPopconfirm } from 'element-plus'
import ModalDialog from './ModalDialog.vue'

export default {
  name: 'DataTable',
  components: {
    ModalDialog,
    ElCard,
    ElButton,
    ElDialog,
    ElForm,
    ElFormItem,
    ElInput,
    ElInputNumber,
    ElTable,
    ElTableColumn,
    ElDescriptions,
    ElDescriptionsItem,
    ElPopconfirm
  },
  data() {
    return {
      items: [],
      showModal: false,
      newItem: {
        name: '',
        host: '',
        port: 3306,
        database: '',
        user: '',
        password: ''
      },
      showDetailModal: false,
      selectedItem: null,
      loading: false
    }
  },
  mounted() {
    this.fetchData()
  },
  methods: {
    async fetchData() {
      try {
        const response = await fetch('http://localhost:5000/api/databases')
        if (response.ok) {
          const data = await response.json()
          // 根据API文档中的返回格式处理数据
          this.items = data.data || []
        } else {
          console.error('获取数据库列表失败:', response.status)
          // 如果API调用失败，使用模拟数据
          this.useMockData()
        }
      } catch (error) {
        console.error('获取数据库列表时发生错误:', error)
        // 如果API调用失败，使用模拟数据
        this.useMockData()
      }
    },
    
    useMockData() {
      this.items = [
        { 
          name: 'test_xxcrypto_rw',
          host: 'pc-3ns1a723w6903b975.rwlb.rds.aliyuncs.com',
          port: 3306,
          database: 'xxcrypto',
          user: 'test_xxcrypto_rw'
        }
      ]
    },
    
    openAddModal() {
      this.showModal = true;
      this.newItem = {
        name: '',
        host: '',
        port: 3306,
        database: '',
        user: '',
        password: ''
      };
    },
    
    closeAddModal() {
      this.showModal = false;
    },
    
    async confirmAdd() {
      // 验证必填字段
      if (!this.newItem.name || !this.newItem.host || !this.newItem.database || 
          !this.newItem.user || !this.newItem.password) {
        this.$message.warning('请填写所有必填字段')
        return
      }
      
      await this.addItem()
    },
    
    async addItem() {
      this.loading = true
      try {
        const response = await fetch('http://localhost:5000/api/databases', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name: this.newItem.name,
            host: this.newItem.host,
            port: parseInt(this.newItem.port),
            database: this.newItem.database,
            user: this.newItem.user,
            password: this.newItem.password
          })
        })
        
        if (response.ok) {
          const result = await response.json()
          
          // 显示成功消息
          this.$message.success('数据库连接添加成功')
          
          // 重新获取数据以更新列表
          await this.fetchData()
          
          // 关闭模态框并重置表单
          this.showModal = false
          this.newItem = {
            name: '',
            host: '',
            port: 3306,
            database: '',
            user: '',
            password: ''
          }
        } else {
          const errorData = await response.json()
          this.$message.error('添加失败: ' + (errorData.error || '未知错误'))
        }
      } catch (error) {
        console.error('添加数据库连接时发生错误:', error)
        this.$message.error('网络错误，请稍后重试')
      } finally {
        this.loading = false
      }
    },
    
    formatDate(date) {
      if (!date) return ''
      const d = new Date(date)
      return d.toLocaleDateString('zh-CN')
    },
    
    async testConnection() {
      // 验证必填字段
      if (!this.newItem.name || !this.newItem.host || !this.newItem.database || 
          !this.newItem.user || !this.newItem.password) {
        this.$message.warning('请填写所有必填字段')
        return
      }
      
      this.loading = true
      try {
        const response = await fetch('http://localhost:5000/api/databases/test', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name: this.newItem.name,
            host: this.newItem.host,
            port: parseInt(this.newItem.port),
            database: this.newItem.database,
            user: this.newItem.user,
            password: this.newItem.password
          })
        })
        
        if (response.ok) {
          const result = await response.json()
          this.$message.success('数据库连接测试成功！')
        } else {
          const errorData = await response.json()
          this.$message.error('数据库连接测试失败: ' + (errorData.error || '未知错误'))
        }
      } catch (error) {
        console.error('测试数据库连接时发生错误:', error)
        this.$message.error('网络错误，请稍后重试')
      } finally {
        this.loading = false
      }
    },
    
    async deleteItem(item) {
      try {
        const response = await fetch(`http://localhost:5000/api/databases/${item.name}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        if (response.ok) {
          // 从列表中移除被删除的项
          this.items = this.items.filter(i => i.name !== item.name)
          this.$message.success('数据库连接删除成功')
        } else {
          const errorData = await response.json()
          this.$message.error('删除失败: ' + (errorData.error || '未知错误'))
        }
      } catch (error) {
        console.error('删除数据库连接时发生错误:', error)
        this.$message.error('网络错误，请稍后重试')
      }
    },
    
    viewDetails(item) {
      this.selectedItem = item;
      this.showDetailModal = true;
    },
    
    closeDetailModal() {
      this.showDetailModal = false;
      this.selectedItem = null;
    },
    
    viewTables(item) {
      // 触发自定义事件，通知父组件查看表
      this.$emit('view-tables', item);
    },
    
    executeSQL(item) {
      // 触发自定义事件，通知父组件执行 SQL
      this.$emit('execute-sql', item);
    }
  }
}
</script>

<style scoped>
.data-table {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
