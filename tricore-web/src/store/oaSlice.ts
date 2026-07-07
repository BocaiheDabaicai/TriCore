import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { oaAPI } from '../services/api'

export interface Employee {
  id: string
  name: string
  department: string
  position: string
  email: string
}

interface OAState {
  employees: Employee[]
  loading: boolean
}

const initialState: OAState = {
  employees: [],
  loading: false,
}

export const fetchEmployees = createAsyncThunk('oa/fetchEmployees', async () => {
  const res = await oaAPI.healthCheck()
  return res
})

const oaSlice = createSlice({
  name: 'oa',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchEmployees.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchEmployees.fulfilled, (state) => {
        state.loading = false
      })
      .addCase(fetchEmployees.rejected, (state) => {
        state.loading = false
      })
  },
})

export default oaSlice.reducer
