<template>
  <el-dialog
    :model-value="visible"
    title="导入CSV文件"
    width="600px"
    @close="handleClose"
  >
    <div v-if="!fileSelected && !mappingStep">
      <!-- 第一步：选择文件 -->
      <el-form label-position="top" size="small">
        <el-form-item label="请选择要导入的CSV文件">
          <el-upload
            :auto-upload="false"
            :on-change="handleFileChange"
            :limit="1"
            accept=".csv"
            :file-list="fileList"
          >
            <el-button type="primary">选择CSV文件</el-button>
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
    
    <div v-else-if="fileSelected && !mappingStep">
      <!-- 第二步：显示文件预览并确认字段映射 -->
      <div style="margin-bottom: 20px;">
        <h4>文件信息</h4>
        <p><strong>文件名：</strong>{{ selectedFile.name }}</p>
        <p><strong>大小：</strong>{{ formatFileSize(selectedFile.size) }}</p>
        <p><strong>CSV分隔符：</strong>
          <el-select v-model="csvSeparator" size="small">
            <el-option label="逗号 (,)" value="," />
            <el-option label="分号 (;)" value=";" />
            <el-option label="制表符 (Tab)" value="\t" />
          </el-select>
        </p>
      </div>
      
      <div style="margin-bottom: 20px;">
        <h4>数据预览</h4>
        <el-table :data="previewData.slice(0, 5)" border size="small">
          <el-table-column
            v-for="(header, index) in previewHeaders"
            :key="index"
            :prop="header"
            :label="header"
            show-overflow-tooltip
          />
        </el-table>
      </div>
      
      <div style="text-align: center;">
        <el-button @click="resetImport" size="small">重新选择文件</el-button>
        <el-button type="primary" @click="startMapping" size="small">开始字段映射</el-button>
      </div>
    </div>
    
    <div v-else-if="mappingStep">
      <!-- 第三步：字段映射 -->
      <h4>字段映射配置</h4>
      <p>请为CSV列与数据库表字段建立对应关系。如果没有匹配项，请选择"跳过"。</p>
      
      <el-table :data="fieldMappingData" border size="small">
        <el-table-column prop="csvColumn" label="CSV列名" width="150" />
        <el-table-column label="数据库字段" width="200">
          <template #default="scope">
            <el-select
              v-model="scope.row.dbField"
              placeholder="选择字段"
              style="width: 100%"
            >
              <el-option
                v-for="field in dbFields"
                :key="field.name"
                :label="field.name"
                :value="field.name"
              />
              <el-option label="跳过此列" value="__skip__" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" width="200">
          <template #default="scope">
            {{ scope.row.description }}
          </template>
        </el-table-column>
      </el-table>
      
      <div style="margin-top: 20px; text-align: center;">
        <el-button @click="backToPreview" size="small">返回</el-button>
        <el-button type="primary" @click="confirmImport" size="small">确认导入</el-button>
      </div>
    </div>
    
    <template #footer v-if="!mappingStep">
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
import { ElDialog, ElForm, ElFormItem, ElButton, ElUpload, ElSelect, ElInput, ElTable, ElTableColumn } from 'element-plus'

export default {
  name: 'CSVImportModal',
  components: {
    ElDialog,
    ElForm,
    ElFormItem,
    ElButton,
    ElUpload,
    ElSelect,
    ElInput,
    ElTable,
    ElTableColumn
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
      mappingStep: false,
      fileList: [],
      csvSeparator: ',',
      previewData: [],
      previewHeaders: [],
      fieldMappingData: [],
      dbFields: [], // 数据库字段信息
      targetTableName: ''
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
      
      // 获取数据库表结构来获取字段信息
      this.fetchTableStructure()
      
      // 预览CSV内容
      this.previewCSVContent()
    },
    
    async fetchTableStructure() {
      try {
        const response = await fetch(`http://localhost:5000/api/databases/${this.databaseName}/tables/${this.tableName}`)
        
        if (response.ok) {
          const result = await response.json()
          
          if (result.success && result.data) {
            // 根据API文档，将字段信息转换为我们需要的格式
            this.dbFields = result.data.map(field => ({
              name: field.Field,
              type: field.Type,
              description: `${field.Null === 'NO' ? '非空' : '可为空'} - ${field.Type}`
            }))
          }
        }
      } catch (error) {
        console.error('获取表结构失败:', error)
        // 如果获取表结构失败，使用默认字段
        this.dbFields = [
          { name: 'column1', type: 'varchar(255)', description: '第一列' },
          { name: 'column2', type: 'int(11)', description: '第二列' }
        ]
      }
    },
    
    async previewCSVContent() {
      if (!this.selectedFile) return
      
      try {
        const text = await this.readFileAsText(this.selectedFile)
        const lines = text.split('\n').filter(line => line.trim())
        
        if (lines.length === 0) return
        
        // 解析第一行作为列名
        const headers = this.parseCSVLine(lines[0], this.csvSeparator)
        this.previewHeaders = headers
        
        // 预览前5行数据（不含标题）
        const dataLines = lines.slice(1, 6)
        this.previewData = dataLines.map(line => {
          const values = this.parseCSVLine(line, this.csvSeparator)
          const row = {}
          headers.forEach((header, index) => {
            row[header] = values[index] || ''
          })
          return row
        })
        
        // 初始化字段映射数据
        this.fieldMappingData = headers.map(header => ({
          csvColumn: header,
          dbField: '',  // 默认未映射
          description: '无描述'
        }))
      } catch (error) {
        console.error('预览CSV文件失败:', error)
      }
    },
    
    parseCSVLine(line, separator) {
      const regex = new RegExp(`"(.*?)"|([^${separator}]+)|(${separator})`, 'g')
      let matches
      const results = []
      
      while ((matches = regex.exec(line)) !== null) {
        if (matches[1] !== undefined) {
          // 处理引号内的内容
          results.push(matches[1])
        } else if (matches[2] !== undefined) {
          // 处理无引号的内容
          results.push(matches[2])
        }
      }
      
      return results.filter(item => item !== separator)
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
      this.mappingStep = true
    },
    
    startMapping() {
      this.mappingStep = true
    },
    
    backToPreview() {
      this.mappingStep = false
    },
    
    resetImport() {
      this.selectedFile = null
      this.fileSelected = false
      this.mappingStep = false
      this.fileList = []
      this.previewData = []
      this.previewHeaders = []
      this.fieldMappingData = []
      this.targetTableName = ''
    },
    
    async confirmImport() {
      if (!this.selectedFile) return
      
      try {
        // 构建FormData对象
        const formData = new FormData()
        formData.append('csv_file', this.selectedFile)
        
        // 如果提供了目标表名，添加到参数中
        if (this.targetTableName) {
          formData.append('table_name', this.targetTableName)
        }
        
        // 处理字段映射（如果需要）
        const mapping = {}
        this.fieldMappingData.forEach(item => {
          if (item.dbField !== '__skip__') {
            mapping[item.csvColumn] = item.dbField
          }
        })
        
        if (Object.keys(mapping).length > 0) {
          formData.append('field_mapping', JSON.stringify(mapping))
        }
        
        // 调用API进行导入
        const response = await fetch(`http://localhost:5000/api/databases/${this.databaseName}/import/csv`, {
          method: 'POST',
          body: formData  // 注意：这里不设置Content-Type，让浏览器自动设置multipart/form-data
        })
        
        if (response.ok) {
          const result = await response.json()
          
          if (result.success) {
            this.$message({
              type: 'success',
              message: 'CSV导入成功'
            })
            this.resetImport()
            this.handleClose()
            // 通知父组件刷新数据
            this.$emit('import-success')
          } else {
            this.$message({
              type: 'error',
              message: result.error || 'CSV导入失败'
            })
          }
        } else {
          const errorData = await response.json()
          this.$message({
            type: 'error',
            message: errorData.error || 'CSV导入失败'
          })
        }
        
      } catch (error) {
        console.error('CSV导入错误:', error)
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

.el-table .cell {
  padding: 8px;
}
</style>
