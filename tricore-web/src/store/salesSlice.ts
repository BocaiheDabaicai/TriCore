import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { salesAPI } from '../services/api'

export interface SalesOrder {
  id: string
  orderNo: string
  customerName: string
  amount: number
  status: string
}

interface SalesState {
  orders: SalesOrder[]
  loading: boolean
}

const initialState: SalesState = {
  orders: [],
  loading: false,
}

export const fetchOrders = createAsyncThunk('sales/fetchOrders', async () => {
  const res = await salesAPI.healthCheck()
  return res
})

const salesSlice = createSlice({
  name: 'sales',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchOrders.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchOrders.fulfilled, (state) => {
        state.loading = false
      })
      .addCase(fetchOrders.rejected, (state) => {
        state.loading = false
      })
  },
})

export default salesSlice.reducer
