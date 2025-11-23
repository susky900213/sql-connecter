<template>
  <div class="sql-executor-page">
    <!-- 顶部提示信息 -->
    <el-alert
      v-if="notification.message"
      :title="notification.message"
      :type="notification.type"
      show-icon
      closable
      @close="clearNotification"
      style="margin-bottom: 20px;"
    ></el-alert>

    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>SQL 执行器 - 新页面</span>
          <el-button type="primary" size="small" @click="handleBack">返回</el-button>
        </div>
      </template>
      
      <!-- 数据库信息显示 -->
      <div v-if="connectionInfo" style="margin-bottom: 15px;">
        <el-row :gutter="10">
          <el-col :span="23"><strong class="black">正在连接数据库: {{ connectionInfo.name }}</strong></el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 主要内容区域 -->
    <el-card style="height: calc(100vh - 250px);">
      <template #header>
        <div class="card-header">SQL 执行</div>
      </template>
      
      <el-form label-position="top" size="small">
        <el-form-item label="SQL语句">
          <el-input
            v-model="sqlQuery"
            type="textarea"
            :rows="8"
            @select="onTextSelect"
            placeholder="请输入要执行的 SQL 语句..."
          />
        </el-form-item>
        
        <div class="button-group">
          <el-button 
            type="primary" 
            @click="executeSQL" 
            :loading="isExecuting"
            style="margin-right: 10px;"
          >
            执行
          </el-button>

          <el-button
            v-if="selectedSQL"
            type="success"
            @click="executeSelectedSQL"
            :loading="isExecuting"
            style="margin-right: 10px;"
          >
            执行选中
          </el-button>
          
          <el-button 
            type="warning" 
            @click="clearResults"
          >
            清空结果
          </el-button>
        </div>
      </el-form>

      <!-- 查询结果显示区域 -->
      <div v-if="showResult" style="margin-top: 20px;">
        <el-alert
          v-if="error"
          title="执行错误"
          :description="error"
          type="error"
          show-icon
          style="margin-bottom: 15px;"
        ></el-alert>
        
        <div v-else-if="resultData && resultData.length > 0">
          <el-table 
            :data="resultData" 
            border 
            style="width: 100%"
            max-height="400"
            @cell-click="copyToClipboard"
          >
            <el-table-column
              v-for="(header, index) in resultHeaders" 
              :key="index"
              :prop="header"
              :label="header"
              show-overflow-tooltip
            >
            </el-table-column>
          </el-table>
        </div>
        
        <div v-else-if="resultData || resultData.length == 0">
          <p style="text-align: center; padding: 20px;">无数据</p>
        </div>
      </div>
    </el-card>
  </div>
  
  <!-- 导出对话框 -->
  <el-dialog
    v-model="exportDialogVisible"
    title="导出SQL"
    width="400px"
  >
    <el-form label-position="top" size="small">
      <el-form-item label="选择导出格式">
        <el-select
          v-model="selectedExportFormatForDialog"
          placeholder="请选择导出格式"
          style="width: 100%"
        >
          <el-option
            v-for="format in exportFormats"
            :key="format.value"
            :label="format.label"
            :value="format.value"
          />
        </el-select>
      </el-form-item>
      
      <!-- 当选择Insert SQL时显示表名输入框 -->
      <el-form-item 
        v-if="selectedExportFormatForDialog === 'insert_sql'" 
        label="表名称（可选）"
      >
        <el-input 
          v-model="exportTableName" 
          placeholder="请输入要导出到的表名（可选）"
          style="width: 100%"
        />
      </el-form-item>
      
      <el-form-item label="文件名">
        <el-input 
          v-model="exportFileName" 
          placeholder="请输入导出的文件名（可选）"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="exportDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmExport">导出</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import { ElAlert, ElButton, ElCard, ElRow, ElCol, ElForm, ElFormItem, ElInput, ElTable, ElTableColumn } from 'element-plus'

export default {
  name: 'SQLExecutorPage',
  components: {
    ElAlert,
    ElButton,
    ElCard,
    ElRow,
    ElCol,
    ElForm,
    ElFormItem,
    ElInput,
    ElTable,
    ElTableColumn
  },
  props: {
    connectionInfo: {
      type: Object,
      default: null
    },
    sqlQueryFromParent: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      sqlQuery: this.sqlQueryFromParent || '',
      isExecuting: false,
      showResult: false,
      selectedSQL: '',
      error: null,
      resultHeaders: [],
      resultData: null,
      notification: {
        message: '',
        type: '' // 'success', 'error', 'warning'
      },
      // 导出格式相关属性
      selectedExportFormat: 'insert_sql', // 默认导出格式
      exportFormats: [
        { label: 'Insert SQL', value: 'insert_sql' },
        { label: 'CSV', value: 'csv' }
      ],
      // 导出对话框相关属性
      exportDialogVisible: false,
      exportSQL: '',
      exportFileName: '',
      selectedExportFormatForDialog: 'insert_sql',
      exportTableName: ''
    }
  },
  mounted() {
    // 如果传入了SQL语句，自动执行
    if (this.sqlQueryFromParent) {
      this.executeSQL();
    }
  },
  methods: {
    handleBack() {
      window.close();
    },
    
    async executeSelectedSQL() {
      if (!this.selectedSQL.trim()) {
        this.showNotification('请先选中要执行的 SQL 语句', 'error');
        return;
      }

      // 检查是否已连接数据库
      if (!this.connectionInfo) {
        this.showNotification('未选择数据库连接', 'error');
        return;
      }

      this.isExecuting = true;
      this.showResult = false;
      this.error = null;

      try {
        // 去掉SQL中的注释
        const cleanSQL = this.removeComments(this.selectedSQL.trim());
        
        // 调用实际的 API 来执行选中的 SQL
        const response = await fetch(`http://localhost:5000/api/databases/${this.connectionInfo.name}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            sql: cleanSQL
          })
        })

        if (response.ok) {
          const result = await response.json();
          
          // 处理返回的结果（根据API文档格式调整）
          if (result.success && result.data) {
            if (result.data.type === 'SELECT') {
              // 如果是查询结果，提取表头和数据
              if (result.data.results && result.data.results.length > 0) {
                this.resultHeaders = result.data.columns;
                this.resultData = result.data.results.map(row => {
                  const obj = {};
                  result.data.columns.forEach((col, index) => {
                    obj[col] = row[index];
                  });
                  return obj;
                });
              } else {
                // 空结果集
                this.resultHeaders = result.data.columns || [];
                this.resultData = [];
              }
            } else {
              // 非查询操作（如 INSERT, UPDATE, DELETE）的结果
              this.resultHeaders = ['状态'];
              if (result.data.type === 'INSERT' || result.data.type === 'UPDATE' || result.data.type === 'DELETE') {
                this.resultData = [{ 状态: `执行成功，影响行数: ${result.data.affected_rows}` }];
              } else {
                this.resultData = [{ 状态: result.message || '执行成功' }];
              }
            }

            this.showResult = true;
            this.showNotification('选中SQL执行成功', 'success');
          } else {
            this.error = result.error || '选中SQL执行失败';
            this.showNotification(result.error || '选中SQL执行失败', 'error');
          }
        } else {
          const errorData = await response.json();
          this.error = errorData.error || '选中SQL执行失败';
          this.showNotification(errorData.error || '选中SQL执行失败', 'error');
        }
      } catch (error) {
        console.error('执行选中的 SQL 时发生错误:', error);
        this.error = '网络错误，请稍后重试';
        this.showNotification('网络错误，请稍后重试', 'error');
      } finally {
        this.isExecuting = false;
      }
    },
    
    onTextSelect(event) {
      const textarea = event.target;
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      
      // 获取选中的文本
      if (start !== end) {
        this.selectedSQL = this.sqlQuery.substring(start, end);
      } else {
        this.selectedSQL = '';
      }
    },
    
    showNotification(message, type = 'success') {
      this.notification.message = message;
      this.notification.type = type;
      
      // 3秒后自动清除通知
      setTimeout(() => {
        this.clearNotification();
      }, 3000);
    },
    
    clearNotification() {
      this.notification.message = '';
      this.notification.type = '';
    },
    
    async executeSQL() {
      if (!this.sqlQuery.trim()) {
        this.showNotification('请输入 SQL 语句', 'error');
        return;
      }

      // 检查是否已连接数据库
      if (!this.connectionInfo) {
        this.showNotification('未选择数据库连接', 'error');
        return;
      }

      this.isExecuting = true;
      this.showResult = false;
      this.error = null;

      try {
        // 去掉SQL中的注释
        const cleanSQL = this.removeComments(this.sqlQuery.trim());
        
        // 调用实际的 API 来执行 SQL（根据API文档调整）
        const response = await fetch(`http://localhost:5000/api/databases/${this.connectionInfo.name}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            sql: cleanSQL
          })
        })

        if (response.ok) {
          const result = await response.json();
          
          // 处理返回的结果（根据API文档格式调整）
          if (result.success && result.data) {
            if (result.data.type === 'SELECT') {
              // 如果是查询结果，提取表头和数据
              if (result.data.results && result.data.results.length > 0) {
                this.resultHeaders = result.data.columns;
                this.resultData = result.data.results.map(row => {
                  const obj = {};
                  result.data.columns.forEach((col, index) => {
                    obj[col] = row[index];
                  });
                  return obj;
                });
              } else {
                // 空结果集
                this.resultHeaders = result.data.columns || [];
                this.resultData = [];
              }
            } else {
              // 非查询操作（如 INSERT, UPDATE, DELETE）的结果
              this.resultHeaders = ['状态'];
              if (result.data.type === 'INSERT' || result.data.type === 'UPDATE' || result.data.type === 'DELETE') {
                this.resultData = [{ 状态: `执行成功，影响行数: ${result.data.affected_rows}` }];
              } else {
                this.resultData = [{ 状态: result.message || '执行成功' }];
              }
            }

            this.showResult = true;
            this.showNotification('SQL 执行成功', 'success');
          } else {
            this.error = result.error || 'SQL 执行失败';
            this.showNotification(result.error || 'SQL 执行失败', 'error');
          }
        } else {
          const errorData = await response.json();
          this.error = errorData.error || 'SQL 执行失败';
          this.showNotification(errorData.error || 'SQL 执行失败', 'error');
        }
      } catch (error) {
        console.error('执行 SQL 时发生错误:', error);
        this.error = '网络错误，请稍后重试';
        this.showNotification('网络错误，请稍后重试', 'error');
      } finally {
        this.isExecuting = false;
      }
    },
    
    clearResults() {
      this.showResult = false;
      this.error = null;
      this.resultHeaders = [];
      this.resultData = null;
      this.clearNotification();
    },
    
    // 复制文本到剪贴板
    copyToClipboard(row, column, cell, event) {
      const text = row[column.property]
      if (!text) return;
      
      navigator.clipboard.writeText(String(text))
        .then(() => {
          this.showNotification('已复制到剪贴板', 'success');
        })
        .catch(err => {
          console.error('复制失败:', err);
          this.showNotification('复制失败', 'error');
        });
    },
    
    // 去掉SQL中的注释
    removeComments(sql) {
      return sql;
    }
  }
}
</script>

<style scoped>
.sql-executor-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.main-content {
  margin-top: 20px;
}

.button-group {
  margin-top: 20px;
}

/* 覆盖Element Plus的样式 */
.el-card__header {
  padding: 12px 15px !important;
}

.el-form-item__label {
  font-weight: bold;
}
</style>
