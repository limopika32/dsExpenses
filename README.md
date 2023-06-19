# dsExpenses
金沢工業大学 電子計算機研究会用 会計 兼 出席管理システム

:warning: pip による `pygame nfcpy` のライブラリインストールが必要です。
```
python -m pip install pygame nfcpy
pip install pygame nfcpy
```


## ファイル
+ `stat.csv` に名簿 `{学籍番号,名前,状態(-1)}` を予め登録してください。毎回の起動時に `.old` が付与されバックアップが作成されます。<br>状態の詳細については [状態について](#状態について) を確認してください。
+ `external.csv` に出席確認が任意な学生や事前連絡があった学生を登録しておくと無断欠席の集計対象外とすることが出来ます。登録が完了次第 `external.csv.old` に変更されます。
+ `log/YYYY-MM-DD.log`(実行日付) には操作履歴が随時記録されます。
### 状態について
| 状態 | 値 | 備考 |
|-|-:|-|
| 任意出席済み | 3 | 出席確認が任意な学生(`-3`) が出席操作を行うと設定されます |
| 支払済み | 1 | 支払いが完了すると設定されます |
| 出席済み | 0 | 未払い かつ 出席済 になります |
| 未確認 | -1 | 初期状態です |
| 事前連絡 | -2 | `external.csv` にて記録された学生に設定されます |
| 任意出席 | -3 | 主に4年生などの 支払い義務がない 学生に設定します |


## 使用方法
1. `start.bat` を起動するか `main.py` を実行します。
2. 各々に学生証をかざして貰います。<br>
    状態 `-3` の学生は任意の出席確認となります。
3. 判定ウィンドウにて支払い完了の可否を 「**支払完了**」「**未払い**」 から選択します。
4. ボタンの押し間違えなどでキャンセルする場合は、「**やっぱ 今の無し**」ボタンを押すことで、<br>
    最後に学生証をかざした学生の状態をリセット(`-1`)することが出来ます。
5. ウィンドウを閉じると受付を終了します。
6. 間違えてウィンドウを閉じて終了した後でも、再度 1. からやり直すことで受付を再開することが出来ます。


***
> nakanolab による [NFC対応学生証による出席確認ツール](https://github.com/nakanolab/nfc-attendance) のソースを利用しています。