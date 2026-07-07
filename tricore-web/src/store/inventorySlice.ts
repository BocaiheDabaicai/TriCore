import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { inventoryAPI } from '../services/api'

export interface Product {
  id: string
  sku: string
  name: string
  quantity: number
  price: number
}

interface InventoryState {
  products: Product[]
  loading: boolean
}

const initialState: InventoryState = {
  products: [],
  loading: false,
}

export const fetchProducts = createAsyncThunk('inventory/fetchProducts', async () => {
  const res = await inventoryAPI.healthCheck()
  return res
})

const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProducts.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchProducts.fulfilled, (state) => {
        state.loading = false
      })
      .addCase(fetchProducts.rejected, (state) => {
        state.loading = false
      })
  },
})

export default inventorySlice.reducer
