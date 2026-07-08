import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { oaAPI } from '../services/api'

interface OAState {
  employees: any[]
  workflows: any[]
  dashboard: any
  loading: boolean
}

const initialState: OAState = { employees: [], workflows: [], dashboard: null, loading: false }

export const fetchEmployees = createAsyncThunk('oa/fetchEmployees', async () => {
  const res: any = await oaAPI.listEmployees({ per_page: 100 })
  return res?.data?.data || res?.data || []
})

export const fetchWorkflows = createAsyncThunk('oa/fetchWorkflows', async () => {
  const res: any = await oaAPI.listWorkflows({ per_page: 50 })
  return res?.data?.data || res?.data || []
})

export const fetchOADashboard = createAsyncThunk('oa/fetchDashboard', async () => {
  const res: any = await oaAPI.getDashboard()
  return res?.data || res
})

const oaSlice = createSlice({
  name: 'oa',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchEmployees.fulfilled, (s, a) => { s.employees = a.payload })
      .addCase(fetchWorkflows.fulfilled, (s, a) => { s.workflows = a.payload })
      .addCase(fetchOADashboard.fulfilled, (s, a) => { s.dashboard = a.payload })
  },
})

export default oaSlice.reducer
