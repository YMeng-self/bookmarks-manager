<template>
  <el-container class="app-container">
    <el-header>
      <div class="header-left">
        <h1>书签管理器</h1>
        <el-button-group>
          <el-button type="primary" @click="importBookmarks('chrome')">
            <el-icon><ChromeFilled /></el-icon> 导入Chrome书签
          </el-button>
          <el-button type="primary" @click="importBookmarks('edge')">
            <el-icon><Monitor /></el-icon> 导入Edge书签
          </el-button>
          <el-button type="success" @click="exportBookmarks">
            <el-icon><Upload /></el-icon> 导出书签
          </el-button>
        </el-button-group>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索书签..."
          class="search-input"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </el-header>
    
    <el-container>
      <el-aside width="300px">
        <div class="tree-toolbar">
          <el-button-group>
            <el-button type="primary" size="small" @click="addFolder">
              <el-icon><FolderAdd /></el-icon> 新建文件夹
            </el-button>
            <el-button type="danger" size="small" @click="deleteSelected" :disabled="!selectedNode">
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </el-button-group>
        </div>
        <el-tree
          ref="treeRef"
          :data="bookmarks"
          :props="defaultProps"
          node-key="id"
          draggable
          @node-drop="handleDrop"
          @node-click="handleNodeClick"
          :filter-node-method="filterNode"
        >
          <template #default="{ node, data }">
            <div class="bookmark-node">
              <span v-if="data.type === 'folder'">
                <el-icon><Folder /></el-icon> {{ node.label }}
              </span>
              <span v-else class="bookmark-item">
                <el-icon><Link /></el-icon>
                <a :href="data.url" target="_blank" @click.stop>{{ node.label }}</a>
                <div class="bookmark-tags">
                  <el-tag
                    v-for="tag in data.tags"
                    :key="tag"
                    size="small"
                    :type="getTagType(tag)"
                    class="ml-2"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
              </span>
            </div>
          </template>
        </el-tree>
      </el-aside>
      
      <el-main>
        <div v-if="selectedBookmark" class="bookmark-detail">
          <el-form label-width="100px">
            <el-form-item label="标题">
              <el-input v-model="selectedBookmark.title" @change="updateBookmark" />
            </el-form-item>
            <el-form-item label="URL">
              <el-input v-model="selectedBookmark.url" @change="updateBookmark" />
            </el-form-item>
            <el-form-item label="标签">
              <div class="tags-section">
                <el-tag
                  v-for="tag in selectedBookmark.tags"
                  :key="tag"
                  closable
                  :type="getTagType(tag)"
                  @close="removeTag(tag)"
                >
                  {{ tag }}
                </el-tag>
                <el-input
                  v-if="inputVisible"
                  ref="tagInput"
                  v-model="inputValue"
                  class="tag-input"
                  size="small"
                  @keyup.enter="handleInputConfirm"
                  @blur="handleInputConfirm"
                />
                <el-button v-else class="button-new-tag" size="small" @click="showInput">
                  + 新标签
                </el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </el-main>
    </el-container>

    <!-- 新建文件夹对话框 -->
    <el-dialog
      v-model="folderDialogVisible"
      title="新建文件夹"
      width="30%"
    >
      <el-form>
        <el-form-item label="文件夹名称">
          <el-input v-model="newFolderName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="folderDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createFolder">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChromeFilled,
  Monitor,
  Upload,
  Search,
  FolderAdd,
  Delete,
  Folder,
  Link
} from '@element-plus/icons-vue'
import axios from 'axios'

// 配置axios基础URL
axios.defaults.baseURL = 'http://localhost:8000'

const bookmarks = ref([])
const selectedBookmark = ref(null)
const selectedNode = ref(null)
const inputVisible = ref(false)
const inputValue = ref('')
const tagInput = ref(null)
const searchQuery = ref('')
const treeRef = ref(null)
const folderDialogVisible = ref(false)
const newFolderName = ref('')

const defaultProps = {
  children: 'children',
  label: (data) => data.type === 'folder' ? data.name : data.title
}

// 监听搜索
watch(searchQuery, (val) => {
  treeRef.value?.filter(val)
})

// 搜索过滤
const filterNode = (value, data) => {
  if (!value) return true
  const searchStr = value.toLowerCase()
  if (data.type === 'folder') {
    return data.name.toLowerCase().includes(searchStr)
  }
  return data.title.toLowerCase().includes(searchStr) ||
         data.url.toLowerCase().includes(searchStr) ||
         data.tags.some(tag => tag.toLowerCase().includes(searchStr))
}

// 获取标签类型
const getTagType = (tag) => {
  if (tag === 'chrome') return 'danger'
  if (tag === 'edge') return 'primary'
  return 'info'
}

// 导入书签
const importBookmarks = async (browserType) => {
  try {
    const response = await axios.get(`/api/bookmarks/${browserType}`)
    // 为新导入的书签添加浏览器标签
    const newBookmarks = response.data.map(bookmark => {
      if (bookmark.type === 'url') {
        bookmark.tags = [...new Set([...bookmark.tags, browserType])]
      }
      return bookmark
    })
    
    // 合并现有书签
    bookmarks.value = mergeBookmarks(bookmarks.value, newBookmarks)
    ElMessage.success('书签导入成功')
  } catch (error) {
    ElMessage.error('书签导入失败：' + error.message)
  }
}

// 合并书签，处理重复项
const mergeBookmarks = (existing, newBookmarks) => {
  const merged = [...existing]
  
  newBookmarks.forEach(newBookmark => {
    if (newBookmark.type === 'url') {
      const existingIndex = merged.findIndex(b => 
        b.type === 'url' && b.url === newBookmark.url
      )
      
      if (existingIndex >= 0) {
        // 合并标签
        merged[existingIndex].tags = [...new Set([
          ...merged[existingIndex].tags,
          ...newBookmark.tags
        ])]
      } else {
        merged.push(newBookmark)
      }
    } else {
      merged.push(newBookmark)
    }
  })
  
  return merged
}

// 导出书签
const exportBookmarks = async () => {
  try {
    await axios.post('/api/bookmarks/export')
    ElMessage.success('书签导出成功')
  } catch (error) {
    ElMessage.error('书签导出失败：' + error.message)
  }
}

// 处理拖拽
const handleDrop = async (draggingNode, dropNode, dropType, ev) => {
  try {
    await axios.put('/api/bookmarks/reorder', {
      draggingId: draggingNode.data.id,
      dropId: dropNode.data.id,
      dropType
    })
    ElMessage.success('书签位置更新成功')
  } catch (error) {
    ElMessage.error('书签位置更新失败：' + error.message)
  }
}

// 处理节点点击
const handleNodeClick = (data) => {
  selectedNode.value = data
  if (data.type === 'url') {
    selectedBookmark.value = data
  }
}

// 更新书签
const updateBookmark = async () => {
  try {
    await axios.put(`/api/bookmarks/${selectedBookmark.value.id}`, selectedBookmark.value)
    ElMessage.success('书签更新成功')
  } catch (error) {
    ElMessage.error('书签更新失败：' + error.message)
  }
}

// 删除选中项
const deleteSelected = async () => {
  if (!selectedNode.value) return
  
  try {
    await ElMessageBox.confirm(
      '确定要删除这个项目吗？',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await axios.delete(`/api/bookmarks/${selectedNode.value.id}`)
    // 从树中移除节点
    const parent = treeRef.value.getNode(selectedNode.value.id).parent
    const index = parent.data.children.findIndex(child => child.id === selectedNode.value.id)
    parent.data.children.splice(index, 1)
    
    selectedNode.value = null
    selectedBookmark.value = null
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error.message)
    }
  }
}

// 新建文件夹
const addFolder = () => {
  folderDialogVisible.value = true
  newFolderName.value = ''
}

const createFolder = async () => {
  if (!newFolderName.value) {
    ElMessage.warning('请输入文件夹名称')
    return
  }
  
  try {
    const response = await axios.post('/api/bookmarks/folder', {
      name: newFolderName.value,
      parentId: selectedNode.value?.id
    })
    
    // 添加到树中
    if (selectedNode.value?.type === 'folder') {
      selectedNode.value.children.push(response.data)
    } else {
      bookmarks.value.push(response.data)
    }
    
    folderDialogVisible.value = false
    ElMessage.success('文件夹创建成功')
  } catch (error) {
    ElMessage.error('文件夹创建失败：' + error.message)
  }
}

// 标签相关方法
const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    tagInput.value.focus()
  })
}

const handleInputConfirm = () => {
  if (inputValue.value) {
    selectedBookmark.value.tags.push(inputValue.value)
    updateBookmark()
  }
  inputVisible.value = false
  inputValue.value = ''
}

const removeTag = (tag) => {
  selectedBookmark.value.tags = selectedBookmark.value.tags.filter(t => t !== tag)
  updateBookmark()
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.el-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-right {
  display: flex;
  align-items: center;
}

.search-input {
  width: 300px;
}

.tree-toolbar {
  padding: 10px;
  border-bottom: 1px solid #e6e6e6;
}

.el-aside {
  border-right: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;
}

.bookmark-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.bookmark-item {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.bookmark-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.bookmark-detail {
  padding: 20px;
}

.tags-section {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-input {
  width: 100px;
  margin-left: 10px;
  vertical-align: bottom;
}

.button-new-tag {
  margin-left: 10px;
  height: 32px;
  line-height: 30px;
  padding-top: 0;
  padding-bottom: 0;
}

.el-tag {
  margin-right: 10px;
  margin-bottom: 10px;
}
</style> 