import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/atoms/card';
import { Button } from '@/components/atoms/button';
import { Label } from '@/components/atoms/label';
import { Input } from '@/components/atoms/input';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-foreground">設定</h1>

      <Card>
        <CardHeader>
          <CardTitle>メール連携</CardTitle>
          <CardDescription>
            メールアカウントを連携して、自動的にタスクを生成します
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="font-medium text-foreground">Google Workspace</p>
              <p className="text-sm text-foreground/60">Gmailアカウントと連携</p>
            </div>
            <Button variant="outline">連携する</Button>
          </div>

          <div className="flex items-center justify-between rounded-lg border p-4">
            <div>
              <p className="font-medium text-foreground">Microsoft 365</p>
              <p className="text-sm text-foreground/60">Outlookアカウントと連携</p>
            </div>
            <Button variant="outline">連携する</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>除外ドメイン設定</CardTitle>
          <CardDescription>
            タスク生成から除外するメールドメインを設定します
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input placeholder="example.com" />
              <Button>追加</Button>
            </div>
            <p className="text-sm text-foreground/60">
              除外ドメインはまだ設定されていません
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}