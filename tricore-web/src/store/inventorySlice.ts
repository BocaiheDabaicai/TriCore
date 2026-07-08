import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { inventoryAPI } from '../services/api'

interface InventoryState {
  products: any[]
  stockIn: any[]
  stockOut: any[]
  issues: any[]
  dashboard: any
  loading: boolean
}

const initialState: InventoryState = { products: [], stockIn: [], stockOut: [], issues: [], dashboard: null, loading: false }

export const fetchInvProducts = createAsyncThunk('inventory/fetchProducts', async () => {
  const res: any = await inventoryAPI.listProducts()
  return res?.data || []
})

export const fetchStockIn = createAsyncThunk('inventory/fetchStockIn', async () => {
  const res: any = await inventoryAPI.listStockIn({ per_page: 50 })
  return res?.data?.data || res?.data || []
})

export const fetchStockOut = createAsyncThunk('inventory/fetchStockOut', async () => {
  const res: any = await inventoryAPI.listStockOut({ per_page: 50 })
  return res?.data?.data || res?.data || []
})

export const fetchIssues = createAsyncThunk('inventory/fetchIssues', async () => {
  const res: any = await inventoryAPI.listIssues({ per_page: 50 })
  return res?.data?.data || res?.data || []
})

export const fetchInvDashboard = createAsyncThunk('inventory/fetchDashboard', async () => {
  const res: any = await inventoryAPI.getDashboard()
  return res?.data || res
})

const inventorySlice = createSlice({
  name: 'inventory',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchInvProducts.fulfilled, (s, a) => { s.products = a.payload })
      .addCase(fetchStockIn.fulfilled, (s, a) => { s.stockIn = a.payload })
      .addCase(fetchStockOut.fulfilled, (s, a) => { s.stockOut = a.payload })
      .addCase(fetchIssues.fulfilled, (s, a) => { s.issues = a.payload })
      .addCase(fetchInvDashboard.fulfilled, (s, a) => { s.dashboard = a.payload })
  },
})

export default inventorySlice.reducer
