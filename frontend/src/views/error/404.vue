<template>
  <div class="error-page">
    <div class="error-content">
      <h1>404</h1>
      <p>抱歉，您访问的页面不存在</p>
      <el-button type="primary" @click="router.push('/')">返回首页</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<style lang="scss" scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f0f2f5;
  
  .error-content {
    text-align: center;
    
    h1 {
      font-size: 120px;
      color: #409eff;
      margin-bottom: 20px;
    }
    
    p {
      font-size: 18px;
      color: #666;
      margin-bottom: 30px;
    }
  }
}
</style>
