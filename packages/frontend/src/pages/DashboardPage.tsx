import { Routes, Route } from 'react-router-dom';
import DashboardLayout from '@/components/templates/DashboardLayout';
import TasksPage from './TasksPage';
import TaskDetailPage from './TaskDetailPage';
import SettingsPage from './SettingsPage';
import UsagePage from './UsagePage';

export default function DashboardPage() {
  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<TasksPage />} />
        <Route path="/tasks" element={<TasksPage />} />
        <Route path="/tasks/:id" element={<TaskDetailPage />} />
        <Route path="/usage" element={<UsagePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </DashboardLayout>
  );
}