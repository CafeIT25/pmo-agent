/**
 * プライバシー保護のためのユーティリティ関数
 */

/**
 * メールアドレスを匿名化
 * @param email メールアドレス
 * @returns 匿名化されたメールアドレス（苗字のみ残す）
 */
export function anonymizeEmail(email: string): string {
  const parts = email.split('@')[0].split('.');
  
  // 日本語名の場合（例: yamada.taro@example.com -> 山田様）
  if (parts.length >= 2) {
    // 最初の部分を苗字として使用
    const lastName = parts[0];
    return `${lastName}様`;
  }
  
  // その他の場合（例: admin@example.com -> 担当者様）
  return '担当者様';
}

/**
 * メール本文からメールアドレスを除去
 * @param content メール本文
 * @returns メールアドレスが除去された本文
 */
export function removeEmailAddresses(content: string): string {
  // メールアドレスパターンを匿名化
  const emailPattern = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  return content.replace(emailPattern, '[メールアドレス]');
}

/**
 * 電話番号を除去
 * @param content コンテンツ
 * @returns 電話番号が除去されたコンテンツ
 */
export function removePhoneNumbers(content: string): string {
  // 日本の電話番号パターン
  const phonePatterns = [
    /\d{2,4}-\d{2,4}-\d{4}/g, // ハイフン区切り
    /\d{10,11}/g, // 連続した数字
    /\+81[- ]?\d{1,4}[- ]?\d{4}/g, // 国際番号
  ];
  
  let result = content;
  phonePatterns.forEach(pattern => {
    result = result.replace(pattern, '[電話番号]');
  });
  
  return result;
}

/**
 * 個人情報を除去してAIに送信可能な形式に変換
 * @param emailThread メールスレッド
 * @returns 匿名化されたメールスレッド
 */
export function sanitizeEmailThread(emailThread: any[]): any[] {
  return emailThread.map(email => ({
    ...email,
    from: anonymizeEmail(email.from),
    to: anonymizeEmail(email.to),
    cc: email.cc ? email.cc.map(anonymizeEmail).join(', ') : undefined,
    bcc: undefined, // BCCは完全に除去
    body: removePhoneNumbers(removeEmailAddresses(email.body)),
    subject: email.subject, // 件名は残す
    date: email.date,
    type: email.type,
  }));
}

/**
 * メール返信用のmailtoリンクを生成
 * @param to 宛先
 * @param cc CC
 * @param subject 件名
 * @param body 本文
 * @returns mailtoリンク
 */
export function generateMailtoLink(
  to: string,
  cc: string = '',
  subject: string = '',
  body: string = ''
): string {
  const params = new URLSearchParams();
  if (cc) params.append('cc', cc);
  if (subject) params.append('subject', subject);
  if (body) params.append('body', body);
  
  const queryString = params.toString();
  return `mailto:${to}${queryString ? '?' + queryString : ''}`;
}

/**
 * Outlook Web用のリンクを生成
 * @param to 宛先
 * @param cc CC
 * @param subject 件名
 * @param body 本文
 * @returns Outlook Webリンク
 */
export function generateOutlookWebLink(
  to: string,
  cc: string = '',
  subject: string = '',
  body: string = ''
): string {
  const params = new URLSearchParams();
  params.append('to', to);
  if (cc) params.append('cc', cc);
  if (subject) params.append('subject', subject);
  if (body) params.append('body', body);
  params.append('cmd', 'new');
  
  return `https://outlook.live.com/mail/0/deeplink/compose?${params.toString()}`;
}

/**
 * Gmail用のリンクを生成
 * @param to 宛先
 * @param cc CC
 * @param subject 件名
 * @param body 本文
 * @returns Gmailリンク
 */
export function generateGmailLink(
  to: string,
  cc: string = '',
  subject: string = '',
  body: string = ''
): string {
  const params = new URLSearchParams();
  params.append('to', to);
  if (cc) params.append('cc', cc);
  if (subject) params.append('su', subject);
  if (body) params.append('body', body);
  
  return `https://mail.google.com/mail/?view=cm&${params.toString()}`;
}