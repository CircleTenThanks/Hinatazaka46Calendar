# Hinatazaka46Calendar
<iframe src="https://calendar.google.com/calendar/embed?&showTitle=0&mode=AGENDA&src=57f2f2a766a36a19faf47870711509914dc87f374fb03c38140e22e06f7ed1c4%40group.calendar.google.com&ctz=Asia%2FTokyo" style="border: 0" width="100%" height="300" frameborder="0" scrolling="no"></iframe>

日向坂46のスケジュールをGoogleカレンダーへ自動追加し、充実したおひさまライフをサポートします。  
[こちら](https://qiita.com/ddn/items/42def5fa721e531eecdb)で紹介されているGoogleカレンダーの共有リンクが2023/02頃から稼働しておらず、勝手ながら本リポジトリを立ち上げました。

## 共有リンク

* ご自身のGoogleカレンダーへ自動追加するには、 [こちらのGoogleカレンダー共有リンク](https://calendar.google.com/calendar/u/0?cid=NTdmMmYyYTc2NmEzNmExOWZhZjQ3ODcwNzExNTA5OTE0ZGM4N2YzNzRmYjAzYzM4MTQwZTIyZTA2ZjdlZDFjNEBncm91cC5jYWxlbmRhci5nb29nbGUuY29t) から設定してください。
    * PCのブラウザからGoogleアカウントにログインした状態でクリックすると、簡単に設定できます。
    * スマートフォンから設定する場合は [#1](https://github.com/CircleTenThanks/Hinatazaka46Calendar/issues/1#issuecomment-1783007351) を参考にしてください。


## 仕組み

本リポジトリはRender.com の CRON JOB としてデプロイしており、上記Googleカレンダーへ自動的に登録されるようになっています。(3か月先の予定まで)  

日向坂46HPのWebサーバへの負荷を最小限にするためにも、上記のGoogleカレンダーが稼働している限りは、個別に本リポジトリをデプロイさせないでください。

なお、日向坂46HPの仕様変更等に伴って動作しなくなった場合のプルリクは大歓迎です。
