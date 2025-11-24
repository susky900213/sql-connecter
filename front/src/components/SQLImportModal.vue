<template>
  <el-dialog
    :model-value="visible"
    title="导入SQL文件"
    width="600px"
    @close="handleClose"
  >
    <div v-if="!fileSelected">
      <!-- 第一步：选择文件 -->
      <el-form label-position="top" size="small">
        <el-form-item label="请选择要导入的SQL文件">
          <el-upload
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".sql"
            :file-list="fileList"
          >
            <el-button type="primary">选择SQL文件</el-button>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="目标表名">
          <el-input 
            v-model="targetTableName" 
            placeholder="请输入要导入到的目标表名（可选）"
          />
        </el-form-item>
      </el-form>
    </div>
    
    <div v-else>
      <!-- 第二步：显示文件信息并确认导入 -->
      <div style="margin-bottom: 20px;">
        <h4>文件信息</h4>
        <p><strong>文件名：</strong>{{ selectedFile.name }}</p>
        <p><strong>大小：</strong>{{ formatFileSize(selectedFile.size) }}</p>
        <p><strong>SQL语句数量：</strong>{{ sqlStatements.length }}</p>
      </div>
      
      <div v-if="sqlStatements.length > 0" style="margin-bottom: 20px;">
        <h4>SQL语句预览</h4>
        <el-alert
          v-for="(stmt, index) in sqlStatements.slice(0, 3)"
          :key="index"
          :title="`语句 ${index + 1}`"
          type="info"
          show-icon
          style="margin-bottom: 10px;"
        >
          <div style="max-height: 100px; overflow-y: auto;">
            {{ stmt.substring(0, 200) }}{{ stmt.length > 200 ? '...' : '' }}
          </div>
        </el-alert>
        <p v-if="sqlStatements.length > 3">
          ... 还有 {{ sqlStatements.length - 3 }} 条语句
        </p>
      </div>
      
      <div style="text-align: center;">
        <el-button @click="resetImport" size="small">重新选择文件</el-button>
        <el-button type="primary" @click="confirmImport" size="small">确认导入</el-button>
      </div>
    </div>
    
    <template #footer v-if="!fileSelected">
      <span class="dialog-footer">
        <el-button @click="handleClose" size="small">取消</el-button>
        <el-button 
          type="primary" 
          @click="nextStep"
          :disabled="!fileSelected || !targetTableName"
          size="small"
        >
          下一步
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script>
import { ElDialog, ElForm, ElFormItem, ElButton, ElUpload, ElInput, ElAlert } from 'element-plus'

export default {
  name: 'SQLImportModal',
  components: {
    ElDialog,
    ElForm,
    ElFormItem,
    ElButton,
    ElUpload,
    ElInput,
    ElAlert
  },
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    databaseName: {
      type: String,
      required: true
    },
    tableName: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      selectedFile: null,
      fileSelected: false,
      fileList: [],
      targetTableName: '',
      sqlStatements: []
    }
  },
  watch: {
    visible(newVal) {
      if (newVal) {
        this.resetImport()
      }
    }
  },
  methods: {
    handleClose() {
      this.$emit('update:visible', false)
    },
    
    handleFileChange(file, fileList) {
      this.selectedFile = file.raw
      this.fileSelected = true
      this.fileList = fileList
      
      // 解析SQL文件内容
      this.parseSQLContent()
    },
    
    async parseSQLContent() {
      if (!this.selectedFile) return
      
      try {
        const text = await this.readFileAsText(this.selectedFile)
        
        // 简单的SQL语句分割（根据分号分割）
        // 注意：这个解析器比较基础，实际应用中可能需要更复杂的SQL解析
        const statements = text.split(/;\s*(?=\n|$)/).filter(stmt => stmt.trim())
        this.sqlStatements = statements.map(stmt => stmt.trim()).slice(0, 10) // 只显示前10条语句
        
      } catch (error) {
        console.error('解析SQL文件失败:', error)
        this.$message({
          type: 'error',
          message: '解析SQL文件时发生错误'
        })
      }
    },
    
    readFileAsText(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsText(file)
      })
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    },
    
    nextStep() {
      if (!this.fileSelected || !this.targetTableName) return
      
      // 检查是否已选择目标表名，如果未选择则使用表格名称
      this.targetTableName = this.targetTableName || this.tableName
    },
    
    resetImport() {
      this.selectedFile = null
      this.fileSelected = false
      this.fileList = []
      this.targetTableName = ''
      this.sqlStatements = []
    },
    
    async confirmImport() {
      if (!this.selectedFile) return
      
      try {
        // 构建FormData对象
        const formData = new FormData()
        formData.append('sql_file', this.selectedFile)
        
        // 如果提供了目标表名，添加到参数中
        if (this.targetTableName) {
          formData.append('table_name', this.targetTableName)
        }
        
        // 调用API进行导入
        const response = await fetch(`http://localhost:5000/api/databases/${this.databaseName}/import/sql`, {
          method: 'POST',
          body: formData  // 注意：这里不设置Content-Type，让浏览器自动设置multipart/form-data
        })
        
        if (response.ok) {
          const result = await response.json()
          
          if (result.success) {
            this.$message({
              type: 'success',
              message: 'SQL导入成功'
            })
            this.resetImport()
            this.handleClose()
            // 通知父组件刷新数据
            this.$emit('import-success')
          } else {
            this.$message({
              type: 'error',
              message: result.error || 'SQL导入失败'
            })
          }
        } else {
          const errorData = await response.json()
          this.$message({
            type: 'error',
            message: errorData.error || 'SQL导入失败'
          })
        }
      } catch (error) {
        console.error('SQL导入错误:', error)
        this.$message({
          type: 'error',
          message: '导入过程中发生错误，请重试'
        })
      }
    }
  }
}
</script>

<style scoped>
.dialog-footer {
  text-align: center;
}

.el-alert {
  margin-bottom: 10px;
}
</style>
