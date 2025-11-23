<template>
  <div class="sql-executor">
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
          <span>SQL 执行器</span>
          <el-button v-if="connectionInfo" type="primary" size="small" @click="handleBack">返回</el-button>
          
        </div>
      </template>
      
      <!-- 数据库信息显示 -->
      <div v-if="connectionInfo" style="margin-bottom: 15px;">
        <el-row :gutter="10" class="main-content">
        <el-col :span="23"><strong class="black">正在连接数据库: {{ connectionInfo.name }}</strong></el-col>
        <el-col :span="1">
        <el-button 
          size="small"
          @click="toggleAIAssistant"
          :type="showAIAssistant ? 'primary' : 'info'"
        >
          {{ showAIAssistant ? '隐藏助手' : '显示助手' }}
        </el-button></el-col>
        </el-row>
      </div>
      
    </el-card>

    <!-- 左中右三栏布局 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左侧：数据库表 -->
      <el-col :span="4">
        <el-card style="height: calc(100vh - 250px);">
          <template #header>
            <div class="card-header">
              数据库表
              <el-button
                type="primary"
                size="small"
                @click="refreshTables"
              >刷新</el-button>
            </div>
          </template>
          <el-scrollbar height="calc(100% - 40px)">
            <div class="table-list">
              <div 
                v-for="table in tables" 
                :key="table.name"
                @click="insertTableName(table.name)"
                style="cursor: pointer; padding: 8px 12px; border-bottom: 1px solid #eee;"
              >
                {{ table.name }}
              </div>
            </div>
          </el-scrollbar>
        </el-card>
      </el-col>

      <!-- 中间：SQL执行区域和结果展示 -->
      <el-col :span="showAIAssistant ? 16 : 20">
        <el-card style="height: calc(100vh - 250px);">
          <template #header>
            <div class="card-header">SQL 执行</div>
          </template>
          
          <!-- 新增：SQL显示区域 -->
          <el-row :gutter="10">
            <el-col :span="14">
              <div class="sql-display-area" style="height: 250px; border: 1px solid #ddd; padding: 10px; overflow-y: auto; background-color: #f9f9f9;">
                <div 
                  v-for="(displayedSQL, index) in displayedSQLs" 
                  :key="index" 
                  class="displayed-sql-item"
                  style="cursor: pointer; padding: 10px; border-bottom: 1px solid #eee; user-select: text;"
                >
                  <pre class="sql-content" @mouseup="handleTextSelect">{{ displayedSQL }}</pre>
                  <div style="margin-top: 10px; display: flex; gap: 10px;">
                    <el-button 
                      type="success"
                      size="small"
                      @click.stop="executeSpecificSQL(displayedSQL)"
                    >
                      执行
                    </el-button>
                    <el-button 
                      type="primary" 
                      size="small" 
                      @click.stop="exportSpecificSQL(displayedSQL)"
                    >
                      导出
                    </el-button>
                    <el-button 
                      type="warning"
                      size="small"
                      @click.stop="copySpecificSQL(displayedSQL)"
                    >
                      复制
                    </el-button>
                    <el-button 
                      type="info" 
                      size="small" 
                      @click="executeAIGeneratedSQLInNewWindow(displayedSQL)"
                    >
                      执行PAGE
                    </el-button>
                    <el-button 
                      type="danger"
                      size="small"
                      @click.stop="removeSQL(index)"
                    >
                      删除
                    </el-button>
                  </div>
                </div>
              </div>
            </el-col>
            
            <!-- SQL编辑区域 -->
            <el-col :span="10">
              <el-form label-position="top" size="small">
                <el-form-item label="SQL语句">
                  <el-input
                    v-model="sqlQuery"
                    type="textarea"
                    :rows="10"
                    placeholder="请输入要执行的 SQL 语句..."
                    @select="onTextSelect"
                  />
                </el-form-item>
                
                <div class="button-group">
                  <el-button 
                    type="primary" 
                    @click="showSQL" 
                    style="margin-right: 10px;"
                  >
                    显示
                  </el-button>

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
                    v-if="selectedSQL" 
                    type="success" 
                    @click="openExportDialog(selectedSQL)" 
                    :loading="isExecuting"
                    style="margin-right: 10px;"
                  >
                    导出选中
                  </el-button>

                  <el-button 
                    type="warning" 
                    @click="clearResults"
                  >
                    清空结果
                  </el-button>
                </div>
              </el-form>
            </el-col>
          </el-row>
          <!-- 查询结果显示区域 -->
          <el-row :gutter="100" style="margin-top: 20px;">
            <el-col :span="24">
              <div v-if="showResult">
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
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 右侧：AI SQL 助手 -->
      <el-col v-if="showAIAssistant" :span="4">
        <el-card style="height: calc(100vh - 250px);">
          <template #header>
            <div class="card-header">AI SQL 助手</div>
          </template>
          
          <div class="chat-container" ref="chatContainer">
            <el-row :gutter="18">
            <div class="chat-messages">
              <div 
                v-for="(message, index) in chatMessages" 
                :key="index"
                :class="['message', message.role]"
              >
                <el-tag :type="message.role === 'user' ? 'primary' : 'success'" size="small">
                  {{ message.role === 'user' ? '用户' : 'AI助手' }}
                </el-tag>
                <div class="message-content">
                  {{ message.content }}
                  <!-- 为AI生成的SQL添加执行按钮和复制按钮 -->
                  <div v-if="message.role === 'assistant' && message.content"
                       style="margin-top: 10px;">
                    <el-button 
                      type="success" 
                      size="small" 
                      @click="executeAIGeneratedSQL(message.content)"
                      style="margin-right: 10px;"
                    >
                      执行
                    </el-button>
                    <el-button 
                      type="primary" 
                      size="small" 
                      @click="copyAISQLToClipboard(message.content)"
                    >
                      复制
                    </el-button>
                    <el-button 
                      type="info" 
                      size="small" 
                      @click="executeAIGeneratedSQLInNewWindow(message.content)"
                    >
                      执行PAGE
                    </el-button>
                    <el-button 
                      type="warning" 
                      size="small" 
                      @click="exportAIGeneratedSQL(message.content)"
                    >
                      导出
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
            </el-row>
            
            
            <div class="chat-input-container">
              <el-input
                v-model="userQuestion"
                placeholder="输入你的SQL问题..."
              />
              <el-button 
                type="primary" 
                @click="sendQuestion" 
                :loading="isChatLoading"
                style="margin-left: 10px;"
              >
                发送
              </el-button>
            </div>
            <!-- Limit 控制组件 -->
            <div class="limit-control-container" style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee;">
              <el-checkbox v-model="limitFlag" style="margin-right: 10px;">启用 LIMIT</el-checkbox>
              <el-input-number 
                v-model="limitValue" 
                :min="1" 
                :max="1000"
                size="small"
                style="width: 120px;"
                v-show="limitFlag"
              />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

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
  </div>
</template>

<script>
import { ElAlert, ElButton, ElCard, ElRow, ElCol, ElForm, ElFormItem, ElInput, ElTable, ElTableColumn, ElScrollbar, ElTag } from 'element-plus'

export default {
  name: 'SQLExecutor',
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
    ElTableColumn,
    ElScrollbar,
    ElTag
  },
  props: {
    connectionInfo: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      sqlQuery: '',
      isExecuting: false,
      showResult: false,
      error: null,
      resultHeaders: [],
      resultData: null,
      notification: {
        message: '',
        type: '' // 'success', 'error', 'warning'
      },
      selectedSQL: '',
      tables: [],
      userQuestion: '',
      chatMessages: [],
      isChatLoading: false,
      tooltipVisible: false,
      tooltipText: '',
      // 添加AI助手显示控制
      showAIAssistant: true,
      // limit 控制相关属性
      limitFlag: true,  // 默认勾选启用limit
      limitValue: 10,   // 默认值为10
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
      exportTableName: '',
      // 显示区的SQL语句列表
      displayedSQLs: []
    }
  },
  mounted() {
    this.fetchTables();
  },
  methods: {
    handleBack() {
      this.$emit('back');
    },
    
    async refreshTables() {
      await this.fetchTables();
      this.showNotification('表列表已刷新', 'success');
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
    
    handleTextSelect() {
      const selection = window.getSelection().toString().trim();
      
      // 获取选中的文本
      if (selection) {
        this.selectedSQL = selection;
      } else {
        this.selectedSQL = '';
      }
    },
    
    async fetchTables() {
      if (!this.connectionInfo) return;
      
      try {
        const response = await fetch(`http://localhost:5000/api/databases/${this.connectionInfo.name}/tables`)
        
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
            console.error('获取表列表失败:', result.error)
          }
        } else {
          const errorData = await response.json()
          console.error('HTTP错误获取表列表:', errorData.error || `HTTP错误: ${response.status}`)
        }
      } catch (error) {
        console.error('获取表列表失败:', error)
      }
    },
    
    async insertTableName(tableName) {
      // 检查当前是否已连接数据库
      if (!this.connectionInfo) {
        // 如果未连接数据库，直接覆盖SQL内容为表名
        this.sqlQuery = `\`${tableName}\``;
        
        return;
      }
      
      try {
        // 获取表结构信息，以生成包含具体字段的SELECT语句
        const response = await fetch(`http://localhost:5000/api/databases/${this.connectionInfo.name}/tables/${tableName}`);
        
        if (response.ok) {
          const result = await response.json();
          
          if (result.success && result.data) {
            // 提取字段名并生成基础SELECT语句
            const fields = result.data.map(field => field.Field);
            
            // 如果获取到表结构，使用包含字段的查询语句覆盖当前内容
            this.sqlQuery = `SELECT ${fields.join(', ')} FROM \`${tableName}\` limit 10;`;
          } else {
            // 如果获取结构失败，回退到简单的表名插入方式
            this.sqlQuery = `\`${tableName}\``;
          }
        } else {
          // 如果获取结构失败，回退到简单的表名插入方式
          this.sqlQuery = `\`${tableName}\``;
        }
      } catch (error) {
        console.error('获取表结构失败:', error);
        
        // 如果获取结构失败，使用默认的表名插入方式
        this.sqlQuery = `\`${tableName}\``;
      }
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

    async executeAIGeneratedSQL(sqlQuery) {
      if (!sqlQuery.trim()) {
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
        const cleanSQL = this.removeComments(sqlQuery.trim());
        
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
    
    clearResults() {
      this.showResult = false;
      this.error = null;
      this.resultHeaders = [];
      this.resultData = null;
      this.clearNotification();
    },
    
    // 发送问题到AI聊天接口
    async sendQuestion() {
      if (!this.userQuestion.trim()) return;
      if (!this.connectionInfo) {
        this.showNotification('请先选择数据库连接', 'error');
        return;
      }
      
      const question = this.userQuestion.trim();
      this.isChatLoading = true;
      
      // 添加用户消息到聊天记录
      this.chatMessages.push({
        role: 'user',
        content: question
      });
      
      try {
        // 调用AI聊天接口
        const response = await fetch(`http://localhost:5000/api/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            database_name: this.connectionInfo.name,
            question: question,
            limit_flag: this.limitFlag,
            limit: this.limitValue
          })
        });
        
        const result = await response.json();
        
        if (result.success && result.sql) {
          // 添加AI回复消息到聊天记录
          this.chatMessages.push({
            role: 'assistant',
            content: result.sql
          });
          
          // 将SQL直接覆盖到textarea中（而不是追加）
          this.sqlQuery = result.sql;
          
          this.showNotification('已获取SQL语句', 'success');
        } else {
          const errorMessage = result.error || '无法生成SQL语句';
          this.chatMessages.push({
            role: 'assistant',
            content: `错误：${errorMessage}`
          });
          this.showNotification(errorMessage, 'error');
        }
      } catch (error) {
        console.error('发送问题到AI接口时出错:', error);
        this.chatMessages.push({
          role: 'assistant',
          content: '错误：网络连接失败'
        });
        this.showNotification('网络错误，请稍后重试', 'error');
      } finally {
        this.isChatLoading = false;
        this.userQuestion = '';
        
        // 滚动到底部
        this.$nextTick(() => {
          const chatContainer = this.$refs.chatContainer;
          if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
          }
        });
      }
    },
    
    // 将SQL语句插入到textarea末尾，另起一行
    insertSQLAtEnd(sql) {
      if (!sql.trim()) return;
      
      // 如果当前文本不为空，在前面加一个换行符
      if (this.sqlQuery.length > 0 && !this.sqlQuery.endsWith('\n')) {
        this.sqlQuery += '\n';
      }
      
      // 添加新的SQL语句（每条语句前添加注释）
      const formattedSQL = `-- AI生成的SQL:\n${sql}\n`;
      this.sqlQuery += formattedSQL;
    },
    
    // 判断是否为长文本（超过50个字符）
    isLongText(text) {
      if (text === null || text === undefined) return false;
      return String(text).length > 10;
    },
    
    // 截断长文本
    truncateText(text, maxLength = 10) {
      if (!text) return text;
      const str = String(text);
      if (str.length <= maxLength) return str;
      return str.substring(0, maxLength) + '...';
    },
    
    // 显示完整文本（用于弹窗或详情查看）
    showFullText(text) {
      alert('完整内容:\n' + text);
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
    },
    
    // 复制AI生成的SQL到剪贴板
    copyAISQLToClipboard(sql) {
      if (!sql.trim()) {
        this.showNotification('没有可复制的SQL', 'warning');
        return;
      }
      
      navigator.clipboard.writeText(sql)
        .then(() => {
          this.showNotification('已复制AI生成的SQL到剪贴板', 'success');
        })
        .catch(err => {
          console.error('复制AI SQL失败:', err);
          this.showNotification('复制失败，请重试', 'error');
        });
    },
    
    // 在新窗口中执行AI生成的SQL语句
    executeAIGeneratedSQLInNewWindow(sqlQuery) {
      if (!sqlQuery.trim()) {
        this.showNotification('没有可执行的 SQL 语句', 'error');
        return;
      }

      // 检查是否已连接数据库
      if (!this.connectionInfo) {
        this.showNotification('未选择数据库连接', 'error');
        return;
      }

      try {
        // 构造新窗口URL，传递必要的参数
        const url = new URL(window.location.origin + window.location.pathname);
        url.searchParams.set('db', this.connectionInfo.name);
        url.searchParams.set('sql', sqlQuery.trim());
        
        // 在新窗口中打开SQL执行页面
        const newWindow = window.open(url.toString(), '_blank');
        
        if (!newWindow) {
          this.showNotification('无法打开新窗口，请检查浏览器弹窗设置', 'error');
        } else {
          this.showNotification('已在新窗口中打开SQL执行器', 'success');
        }
      } catch (error) {
        console.error('在新窗口中执行SQL时出错:', error);
        this.showNotification('打开新窗口失败，请重试', 'error');
      }
    },
    
    // 切换AI助手显示状态
    toggleAIAssistant() {
      this.showAIAssistant = !this.showAIAssistant;
    },
    
    // 导出AI生成的SQL
    async exportAIGeneratedSQL(sql) {
      if (!sql) {
        sql = this.selectedSQL
      }
      if (!sql) {
        this.showNotification('没有可导出的SQL', 'warning');
        return;
      }
      
      // 使用与选中导出一致的方式，打开弹窗对话框
      this.exportDialogVisible = true;
      this.exportSQL = sql;
    },
    
    // 打开导出对话框
    openExportDialog(sql) {
      if (!sql) {
        sql = this.selectedSQL;
      }
      
      if (!sql) {
        this.showNotification('没有可导出的SQL', 'warning');
        return;
      }
      
      this.exportDialogVisible = true;
      this.exportSQL = sql;
    },
    
    // 确认导出
    async confirmExport() {
      if (!this.exportSQL) {
        this.showNotification('没有可导出的SQL', 'warning');
        return;
      }
      
      // 检查是否已连接数据库
      if (!this.connectionInfo) {
        this.showNotification('未选择数据库连接', 'error');
        return;
      }
      
      try {
        // 构建请求参数
        const exportParams = {
          format: this.selectedExportFormatForDialog,
          sql: this.exportSQL
        };
        
        // 如果选择了insert_sql格式并且用户输入了表名，则添加table_name参数
        if (this.selectedExportFormatForDialog === 'insert_sql' && this.exportTableName) {
          exportParams.table_name = this.exportTableName;
        }
        
        // 调用后端导出接口
        const response = await fetch(`http://localhost:5000/api/databases/${this.connectionInfo.name}/export`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(exportParams)
        });
        
        if (response.ok) {
          // 获取文件名和数据
          const contentDisposition = response.headers.get('content-disposition');
          let filename = 'export';
          
          if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch && filenameMatch[1]) {
              filename = filenameMatch[1];
            }
          }
          
          // 如果用户指定了文件名，则使用它
          if (this.exportFileName) {
            filename = this.exportFileName;
          }
          if (this.selectedExportFormatForDialog == "csv") {
            filename = filename + ".csv"
          } else {
            filename = filename + ".sql"
          }
          
          // 读取响应数据并下载文件
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', filename); 
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          this.showNotification(`导出成功: ${filename}`, 'success');
        } else {
          const errorData = await response.json();
          this.showNotification(`导出失败: ${errorData.error || '未知错误'}`, 'error');
        }
      } catch (error) {
        console.error('导出SQL时发生错误:', error);
        this.showNotification('导出过程中出现错误，请重试', 'error');
      } finally {
        // 关闭对话框
        this.exportDialogVisible = false;
        this.exportFileName = '';
        this.exportTableName = '';  // 清空表名输入框
      }
    },
    
    // 显示SQL到显示区域
    showSQL() {
      if (!this.sqlQuery.trim()) {
        this.showNotification('请输入 SQL 语句', 'error');
        return;
      }
      
      // 将当前sqlQuery添加到显示区数组的末尾
      this.displayedSQLs.push(this.sqlQuery);
      
      // 清空编辑框内容（可选）
      // this.sqlQuery = '';
      
      this.showNotification('SQL已添加到显示区域', 'success');
    },
    
    // 执行指定的SQL语句
    async executeSpecificSQL(sql) {
      if (!sql.trim()) {
        this.showNotification('没有可执行的 SQL 语句', 'error');
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
        const cleanSQL = this.removeComments(sql.trim());
        
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
    
    // 导出指定的SQL语句
    exportSpecificSQL(sql) {
      if (!sql) {
        this.showNotification('没有可导出的SQL', 'warning');
        return;
      }
      
      // 使用与选中导出一致的方式，打开弹窗对话框并传入要导出的SQL
      this.exportDialogVisible = true;
      this.exportSQL = sql;
    },
    
    // 复制指定的SQL到编辑框（替换内容）
    copySpecificSQL(sql) {
      if (!sql) {
        this.showNotification('没有可复制的SQL', 'warning');
        return;
      }
      
      // 将SQL内容复制到编辑框
      this.sqlQuery = sql;
      
      this.showNotification('SQL已复制到编辑区', 'success');
    },
    
    // 删除指定索引的SQL语句
    removeSQL(index) {
      if (index >= 0 && index < this.displayedSQLs.length) {
        this.displayedSQLs.splice(index, 1);
        this.showNotification('SQL已删除', 'success');
      }
    }
  }
}
</script>

<style scoped>
.sql-executor {
  padding: 20px;
}

.long-text-cell {
  position: relative;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.long-text-cell:hover {
  background-color: #f5f5f5;
}

.long-text-tooltip {
  position: absolute;
  top: -10px;
  left: 0;
  background-color: #333;
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  z-index: 9999;
  max-width: 300px;
  word-wrap: break-word;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  white-space: normal;
  line-height: 1.4;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.main-content {
  margin-top: 20px;
}

.chat-container {
  height: calc(100% - 40px);
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  height: 500px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f5f5;
  margin-bottom: 10px;
  overflow-y: auto;
}

.message {
  margin-bottom: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
  background-color: #e3f2fd;
  text-align: right;
}

.message.assistant {
  align-self: flex-start;
  background-color: #f5f5f5;
}

.message-content {
  margin-top: 5px;
  word-wrap: break-word;
  white-space: pre-wrap;
}

.chat-input-container {
  display: flex;
  gap: 10px;
}

.button-group {
  margin-top: 20px;
}

/* SQL显示区域样式 */
.sql-display-area {
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: #f9f9f9;
  overflow-y: auto;
  padding: 10px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.sql-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 覆盖Element Plus的样式 */
.el-card__header {
  padding: 12px 15px !important;
}

.el-form-item__label {
  font-weight: bold;
}
</style>
