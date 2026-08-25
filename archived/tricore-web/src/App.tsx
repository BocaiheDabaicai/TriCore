import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import Dashboard from './pages/dashboard'
import SalesDashboard from './pages/sales'
import OADashboard from './pages/oa'
import InventoryDashboard from './pages/inventory'

function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="sales" element={<SalesDashboard />} />
        <Route path="oa" element={<OADashboard />} />
        <Route path="inventory" element={<InventoryDashboard />} />
      </Route>
    </Routes>
  )
}

export default App
