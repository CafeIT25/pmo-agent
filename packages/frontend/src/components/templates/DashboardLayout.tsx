import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { Button } from '@/components/atoms/button';
import { useAuthStore } from '@/store/authStore';
import { useDemoStore } from '@/store/demoStore';
import {
  LayoutDashboard,
  Settings,
  LogOut,
  Mail,
  CheckSquare,
  TrendingUp,
  TestTube,
} from 'lucide-react';

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const location = useLocation();
  const logout = useAuthStore((state) => state.logout);
  const user = useAuthStore((state) => state.user);
  const { isDemoMode, toggleDemoMode } = useDemoStore();

  const navigation = [
    { name: 'タスク', href: '/tasks', icon: CheckSquare },
    { name: '使用量', href: '/usage', icon: TrendingUp },
    { name: '設定', href: '/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-background">
      {/* サイドバー */}
      <div className="flex w-64 flex-col bg-card shadow-xl">
        <div className="flex h-16 items-center justify-center border-b border-border/50">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">PMO Agent</h1>
        </div>

        <nav className="flex-1 space-y-2 p-4">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  'flex items-center rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200 group',
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-soft'
                    : 'text-foreground/60 hover:bg-accent hover:text-accent-foreground hover:translate-x-1'
                )}
              >
                <Icon className={cn(
                  "mr-3 h-5 w-5 transition-transform duration-200",
                  isActive ? "scale-110" : "group-hover:scale-110"
                )} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-border/50 p-4">
          <div className="mb-4 rounded-lg bg-muted/50 p-3">
            <p className="font-semibold text-foreground">{user?.name || 'ユーザー'}</p>
            <p className="text-sm text-foreground/60">{user?.email}</p>
          </div>
          <Button
            variant="outline"
            className="w-full justify-start text-foreground border-border hover:bg-destructive hover:text-destructive-foreground hover:border-destructive"
            onClick={logout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            ログアウト
          </Button>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="flex flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-border/50 bg-card/50 backdrop-blur-sm px-8 shadow-soft">
          <h2 className="text-xl font-semibold text-foreground animate-fade-in">
            {navigation.find((item) => item.href === location.pathname)?.name ||
              'ダッシュボード'}
          </h2>

          <div className="flex items-center space-x-4">
            {/* デモモード切り替えボタン */}
            <Button
              variant={isDemoMode ? "destructive" : "outline"}
              size="sm"
              onClick={toggleDemoMode}
              className={`shadow-soft ${!isDemoMode ? 'text-foreground border-foreground/20 hover:bg-foreground/10 focus:text-foreground focus:border-foreground' : ''}`}
            >
              <TestTube className="mr-2 h-4 w-4" />
              {isDemoMode ? "デモモード" : "本番モード"}
            </Button>
            
            <Button variant="gradient" size="sm" className="shadow-medium">
              <Mail className="mr-2 h-4 w-4" />
              メール同期
            </Button>
          </div>
        </header>

        <main className="flex-1 overflow-auto bg-background p-8">
          <div className="mx-auto max-w-7xl animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}