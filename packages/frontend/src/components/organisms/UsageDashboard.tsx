import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../atoms/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../atoms/tabs'
import { Badge } from '../atoms/badge'
import { useToast } from '../atoms/use-toast'
// recharts は後でインストールが必要
// import { 
//   BarChart, 
//   Bar, 
//   XAxis, 
//   YAxis, 
//   CartesianGrid, 
//   Tooltip, 
//   ResponsiveContainer,
//   PieChart,
//   Pie,
//   Cell,
//   LineChart,
//   Line
// } from 'recharts'
import { 
  TrendingUp, 
  DollarSign, 
  Activity, 
  Zap,
  Calendar,
  Clock,
  Brain
} from 'lucide-react'
import apiClient from '../../api/client'
import { useDemoData } from '@/hooks/useDemoData'

interface UsageStats {
  summary: {
    total_input_tokens: number
    total_output_tokens: number
    total_tokens: number
    total_cost_usd: number
    total_cost_jpy: number
    request_count: number
    average_cost_per_request: number
  }
  model_breakdown: Array<{
    model: string
    input_tokens: number
    output_tokens: number
    cost_usd: number
    cost_jpy: number
    requests: number
  }>
  purpose_breakdown: Array<{
    purpose: string
    input_tokens: number
    output_tokens: number
    cost_usd: number
    cost_jpy: number
    requests: number
  }>
  daily_usage: Array<{
    date: string
    cost_usd: number
    cost_jpy: number
    tokens: number
    requests: number
  }>
}

interface RecentUsage {
  id: string
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost_usd: number
  cost_jpy: number
  purpose: string
  verbosity?: string
  reasoning_effort?: string
  created_at: string
}

export const UsageDashboard: React.FC = () => {
  const [monthlyStats, setMonthlyStats] = useState<UsageStats | null>(null)
  const [recentUsage, setRecentUsage] = useState<RecentUsage[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1)
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const { toast } = useToast()
  const { fetchUsageData, isDemoMode } = useDemoData()

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

  const loadUsageData = async () => {
    setIsLoading(true)
    try {
      const data = await fetchUsageData({
        year: selectedYear, 
        month: selectedMonth
      })

      setMonthlyStats(data.monthly)
      setRecentUsage(data.recent)
    } catch (error: any) {
      if (!isDemoMode) {
        toast({
          title: '使用量データの取得に失敗',
          description: error.response?.data?.detail || 'データの取得中にエラーが発生しました',
          variant: 'destructive'
        })
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadUsageData()
  }, [selectedMonth, selectedYear, isDemoMode])

  const formatCurrency = (amount: number, currency: 'USD' | 'JPY' = 'USD') => {
    if (currency === 'USD') {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 4,
        maximumFractionDigits: 6
      }).format(amount)
    } else {
      return new Intl.NumberFormat('ja-JP', {
        style: 'currency',
        currency: 'JPY'
      }).format(amount)
    }
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ja-JP').format(num)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ja-JP', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getModelBadgeColor = (model: string) => {
    if (model.includes('gpt-5-mini')) return 'default'
    if (model.includes('gpt-5-nano')) return 'secondary'
    if (model.includes('gpt-5')) return 'destructive'
    return 'outline'
  }

  const getPurposeIcon = (purpose: string) => {
    if (purpose.includes('email')) return <Activity className="h-4 w-4" />
    if (purpose.includes('task')) return <Brain className="h-4 w-4" />
    return <Zap className="h-4 w-4" />
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">AI使用量ダッシュボード</h2>
          <p className="text-muted-foreground">
            OpenAI API の使用状況とコストを確認できます
            {isDemoMode && (
              <span className="ml-2 inline-flex items-center px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-800">
                デモモード
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            className="px-3 py-2 border rounded-md"
          >
            {[2024, 2025].map(year => (
              <option key={year} value={year}>{year}年</option>
            ))}
          </select>
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(Number(e.target.value))}
            className="px-3 py-2 border rounded-md"
          >
            {Array.from({ length: 12 }, (_, i) => (
              <option key={i + 1} value={i + 1}>{i + 1}月</option>
            ))}
          </select>
        </div>
      </div>

      {/* サマリーカード */}
      {monthlyStats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">総コスト</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatCurrency(monthlyStats.summary.total_cost_usd)}
              </div>
              <p className="text-xs text-muted-foreground">
                {formatCurrency(monthlyStats.summary.total_cost_jpy, 'JPY')}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">総トークン数</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(monthlyStats.summary.total_tokens)}
              </div>
              <p className="text-xs text-muted-foreground">
                入力: {formatNumber(monthlyStats.summary.total_input_tokens)} / 
                出力: {formatNumber(monthlyStats.summary.total_output_tokens)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">リクエスト数</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {formatNumber(monthlyStats.summary.request_count)}
              </div>
              <p className="text-xs text-muted-foreground">
                平均単価: {formatCurrency(monthlyStats.summary.average_cost_per_request)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">今月の期間</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {selectedYear}/{selectedMonth}
              </div>
              <p className="text-xs text-muted-foreground">
                日平均: {formatCurrency(monthlyStats.summary.total_cost_usd / new Date().getDate())}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 詳細タブ */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">概要</TabsTrigger>
          <TabsTrigger value="models">モデル別</TabsTrigger>
          <TabsTrigger value="daily">日別推移</TabsTrigger>
          <TabsTrigger value="recent">最近の使用</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* 用途別円グラフ */}
            <Card>
              <CardHeader>
                <CardTitle>用途別使用量</CardTitle>
                <CardDescription>機能別のコスト分布</CardDescription>
              </CardHeader>
              <CardContent>
                {(monthlyStats?.purpose_breakdown || []).length > 0 ? (
                  <div className="space-y-3">
                    {monthlyStats?.purpose_breakdown?.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
                        <span className="font-medium">{item.purpose}</span>
                        <span className="text-right">
                          <div className="font-semibold">{formatCurrency(item.cost_usd)}</div>
                          <div className="text-sm text-muted-foreground">{formatCurrency(item.cost_jpy, 'JPY')}</div>
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">データがありません</div>
                )}
              </CardContent>
            </Card>

            {/* モデル別棒グラフ */}
            <Card>
              <CardHeader>
                <CardTitle>モデル別コスト</CardTitle>
                <CardDescription>使用モデルの比較</CardDescription>
              </CardHeader>
              <CardContent>
                {(monthlyStats?.model_breakdown || []).length > 0 ? (
                  <div className="space-y-3">
                    {monthlyStats?.model_breakdown?.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
                        <Badge variant={getModelBadgeColor(item.model)}>
                          {item.model}
                        </Badge>
                        <span className="text-right">
                          <div className="font-semibold">{formatCurrency(item.cost_usd)}</div>
                          <div className="text-sm text-muted-foreground">{item.requests}件</div>
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">データがありません</div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>モデル別詳細統計</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">モデル</th>
                      <th className="text-right p-2">リクエスト数</th>
                      <th className="text-right p-2">入力トークン</th>
                      <th className="text-right p-2">出力トークン</th>
                      <th className="text-right p-2">コスト (USD)</th>
                      <th className="text-right p-2">コスト (JPY)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monthlyStats?.model_breakdown.map((model, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-2">
                          <Badge variant={getModelBadgeColor(model.model)}>
                            {model.model}
                          </Badge>
                        </td>
                        <td className="text-right p-2">{formatNumber(model.requests)}</td>
                        <td className="text-right p-2">{formatNumber(model.input_tokens)}</td>
                        <td className="text-right p-2">{formatNumber(model.output_tokens)}</td>
                        <td className="text-right p-2">{formatCurrency(model.cost_usd)}</td>
                        <td className="text-right p-2">{formatCurrency(model.cost_jpy, 'JPY')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="daily" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>日別使用量推移</CardTitle>
              <CardDescription>1ヶ月間のコスト推移</CardDescription>
            </CardHeader>
            <CardContent>
              {(monthlyStats?.daily_usage || []).length > 0 ? (
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {monthlyStats?.daily_usage?.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-2 hover:bg-muted/50 rounded">
                      <span className="text-sm font-medium">
                        {new Date(item.date).getDate()}日
                      </span>
                      <div className="text-right">
                        <div className="text-sm font-semibold">{formatCurrency(item.cost_usd)}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatNumber(item.tokens)} tokens・{item.requests}件
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">データがありません</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recent" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>最近の使用履歴</CardTitle>
              <CardDescription>直近7日間の API使用履歴</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentUsage.map((usage) => (
                  <div 
                    key={usage.id} 
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {getPurposeIcon(usage.purpose)}
                      <div>
                        <div className="font-medium">{usage.purpose}</div>
                        <div className="text-sm text-muted-foreground">
                          {formatDate(usage.created_at)}
                        </div>
                      </div>
                      <Badge variant={getModelBadgeColor(usage.model)}>
                        {usage.model}
                      </Badge>
                      {usage.verbosity && (
                        <Badge variant="outline">
                          verbosity: {usage.verbosity}
                        </Badge>
                      )}
                    </div>
                    <div className="text-right">
                      <div className="font-medium">
                        {formatCurrency(usage.cost_usd)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {formatNumber(usage.total_tokens)} tokens
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}