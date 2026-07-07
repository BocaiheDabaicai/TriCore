import { configureStore } from '@reduxjs/toolkit'
import salesReducer from './salesSlice'
import oaReducer from './oaSlice'
import inventoryReducer from './inventorySlice'

const store = configureStore({
  reducer: {
    sales: salesReducer,
    oa: oaReducer,
    inventory: inventoryReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
export default store
