/**
 * プライバシー保護機能のテスト
 */

import { 
  removeEmailAddresses, 
  removePhoneNumbers, 
  sanitizeEmailThread,
  anonymizeEmail 
} from './privacy';

// テスト用のサンプルデータ
const sampleEmailContent = `
お世話になっております。

プロジェクトの件でご連絡いたします。
詳細については、直接お電話でお話しできればと思います。

何かご質問がございましたら、下記までご連絡ください。

---
田中太郎
株式会社サンプル
Email: tanaka.taro@sample.co.jp
Tel: 03-1234-5678
Mobile: 090-8765-4321
`;

const sampleEmailWithSignature = `
資料を添付いたします。
ご確認のほど、よろしくお願いいたします。

山田花子
sample.company@example.com
`;

// テスト実行
console.log('=== プライバシー保護機能テスト ===\n');

console.log('1. メールアドレス除去テスト:');
console.log('元の内容:', sampleEmailContent);
console.log('処理後:', removeEmailAddresses(sampleEmailContent));
console.log('');

console.log('2. 電話番号除去テスト:');
const phoneTest = removePhoneNumbers(sampleEmailContent);
console.log('処理後:', phoneTest);
console.log('');

console.log('3. メール署名テスト:');
console.log('元の内容:', sampleEmailWithSignature);
console.log('処理後:', removeEmailAddresses(sampleEmailWithSignature));
console.log('');

console.log('4. メールアドレス匿名化テスト:');
const testEmails = [
  'yamada.taro@company.co.jp',
  'admin@server.com',
  'test.user@example.org'
];

testEmails.forEach(email => {
  console.log(`${email} → ${anonymizeEmail(email)}`);
});
console.log('');

console.log('5. 統合テスト（sanitizeEmailThread）:');
const sampleThread = [
  {
    from: 'tanaka.taro@sample.co.jp',
    to: 'yamada.hanako@example.com',
    cc: 'admin@company.co.jp',
    subject: 'プロジェクトについて',
    body: sampleEmailContent,
    date: '2025-08-14',
    type: 'received'
  }
];

const sanitized = sanitizeEmailThread(sampleThread);
console.log('匿名化後:', JSON.stringify(sanitized, null, 2));

export {};