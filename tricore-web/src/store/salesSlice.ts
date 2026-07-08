import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { salesAPI } from '../services/api'

export interface SalesOrder {
  id: string; order_no: string; customer_id: string; total_amount: number;
  final_amount: number; status: string; created_at: string;
}

interface SalesState {
  orders: SalesOrder[]
  products: any[]
  users: any[]
  dashboard: any
  loading: boolean
}

const initialState: SalesState = { orders: [], products: [], users: [], dashboard: null, loading: false }

export const fetchOrders = createAsyncThunk('sales/fetchOrders', async () => {
  const res: any = await salesAPI.listOrders({ per_page: 50 })
  return res?.data?.data || res?.data || []
})

export const fetchProducts = createAsyncThunk('sales/fetchProducts', async () => {
  const res: any = await salesAPI.listProducts({ per_page: 100 })
  return res?.data?.data || res?.data || []
})

export const fetchDashboard = createAsyncThunk('sales/fetchDashboard', async () => {
  const res: any = await salesAPI.getDashboard()
  return res?.data || res
})

const salesSlice = createSlice({
  name: 'sales',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrders.pending, (s) => { s.loading = true })
      .addCase(fetchOrders.fulfilled, (s, a) => { s.orders = a.payload; s.loading = false })
      .addCase(fetchOrders.rejected, (s) => { s.loading = false })
      .addCase(fetchProducts.fulfilled, (s, a) => { s.products = a.payload })
      .addCase(fetchDashboard.fulfilled, (s, a) => { s.dashboard = a.payload })
  },
})

export default salesSlice.reducer
