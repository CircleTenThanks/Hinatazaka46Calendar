# Hinatazaka46Calendar
<iframe src="https://calendar.google.com/calendar/embed?&showTitle=0&mode=AGENDA&src=57f2f2a766a36a19faf47870711509914dc87f374fb03c38140e22e06f7ed1c4%40group.calendar.google.com&ctz=Asia%2FTokyo" style="border: 0" width="100%" height="300" frameborder="0" scrolling="no"></iframe>

日向坂46のスケジュールをGoogleカレンダーへ自動追加し、充実したおひさまライフをサポートします。  
[こちら](https://qiita.com/ddn/items/42def5fa721e531eecdb)で紹介されているGoogleカレンダーの共有リンクが2023/02頃から稼働しておらず、勝手ながら本リポジトリを立ち上げました。

## 共有リンク

* Googleカレンダー
  * ご自身のGoogleカレンダーへ追加するには、上記カレンダー右下の `+Googleカレンダー`から設定してください。
  * スマートフォンでうまく設定できない場合は [#1](https://github.com/CircleTenThanks/Hinatazaka46Calendar/issues/1#issuecomment-1783007351) を参考にしてください。
* iCal形式(ICS形式)
  * [こちら](https://calendar.google.com/calendar/ical/57f2f2a766a36a19faf47870711509914dc87f374fb03c38140e22e06f7ed1c4%40group.calendar.google.com/public/basic.ics)のリンクをコピーすると、iCal形式の共有リンクがコピーできます。お使いのカレンダーアプリがiCal形式に対応していれば、Googleカレンダー以外のカレンダーアプリへ追加することも可能です。
  * [iPhoneにインストールされているカレンダーアプリでの設定例](https://support.apple.com/ja-jp/guide/iphone/iph3d1110d4/ios)

## 仕組み

本リポジトリはRender.com の CRON JOB としてデプロイしており、上記Googleカレンダーへ自動的に登録されるようになっています。(3か月先の予定まで)  

日向坂46HPのWebサーバへの負荷を最小限にするためにも、上記のGoogleカレンダーが稼働している限りは、個別に本リポジトリをデプロイさせないでください。

なお、日向坂46HPの仕様変更等に伴って動作しなくなった場合のプルリクは大歓迎です。

## 問い合わせ先

要望などがあれば。

* https://github.com/CircleTenThanks/Hinatazaka46Calendar/issues
* https://twitter.com/CircleTenThanks