import request from './request'

export const getProductList = (params) => {
  return request.get('/products', { params })
}

export const createProduct = (data) => {
  return request.post('/products', data)
}

export const updateProduct = (id, data) => {
  return request.put(`/products/${id}`, data)
}

export const deleteProduct = (id) => {
  return request.delete(`/products/${id}`)
}

export const getProductDetail = (id) => {
  return request.get(`/products/${id}`)
}

export const importProducts = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/products/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const exportProducts = () => request.get('/products/export', { responseType: 'blob' })

// 分类管理
export const getProductCategories = () => request.get('/product/categories')
export const createProductCategory = (data) => request.post('/product/categories', data)
export const updateProductCategory = (id, data) => request.put(`/product/categories/${id}`, data)
export const deleteProductCategory = (id) => request.delete(`/product/categories/${id}`)

// 单位管理
export const getProductUnits = () => request.get('/product/units')
export const createProductUnit = (data) => request.post('/product/units', data)
export const updateProductUnit = (id, data) => request.put(`/product/units/${id}`, data)
export const deleteProductUnit = (id) => request.delete(`/product/units/${id}`)
