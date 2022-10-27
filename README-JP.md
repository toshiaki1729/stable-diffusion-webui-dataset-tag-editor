# Dataset Tag Editor

[English Readme](README.md)

[Stable Diffusion web UI by AUTOMATIC1111](https://github.com/AUTOMATIC1111/stable-diffusion-webui)用の拡張機能です。

web UI 上で学習用データセットのキャプションを編集できるようにします。

![](ss01.png)

DeepBooru interrogator で生成したような、カンマ区切り形式のキャプションを編集するのに適しています。

キャプションとして画像ファイル名を利用している場合も読み込むことができますが、保存はテキストファイルのみ対応しています。

## インストール方法
web UI の `extensions` フォルダにリポジトリのクローンを作成し再起動してください。

web UI のフォルダで以下のコマンドを実行することによりインストールできます。
```commandline
git clone https://github.com/toshiaki1729/stable-diffusion-webui-dataset-tag-editor.git extensions/dataset-tag-editor
```

## 特徴
以下、「タグ」はカンマ区切りされたキャプションの各部分を意味します。
- 画像を見ながらキャプションの編集ができます
- タグの検索ができます
- 複数タグで絞り込んでキャプションの編集ができます
- タグを一括で置換・削除・追加できます


## 使い方
1. web UI でデータセットを作成する
2. データセットを読み込む
3. "Filter and Edit Tags" タブで編集したいタグを選択する
4. それらを置換・削除したり新しいタグを追加する
5. キャプションを個別に編集したい場合は "Edit Caption of Selected Image" タブを使用する
6. "Save all changes" ボタンをクリックして保存する


## 表示内容

### 共通
- "Save all changes" ボタン
  - キャプションをテキストファイルに保存します。このボタンを押すまで全ての変更は適用されません。
  - "Backup original text file" にチェックを入れることで、保存時にオリジナルのテキストファイル名をバックアップします。
    - バックアップファイル名は、filename.000、 -.001、 -.002、…、のように付けられます。
  - 画像ファイル名をキャプションとしている場合、キャプションを含む新しいテキストファイルが作成されます。
- "Results" テキストボックス
  - 保存した結果が表示されます。
- "Dataset Directory" テキストボックス
  - 学習データセットのあるディレクトリを入力してください。
- "Dataset Images" ギャラリー
  - 教師画像の確認と選択ができます。


### "Filter and Edit Tags" タブ
![](ss02.png)

- "Search Tags" テキストボックス
  - 入力した文字で下に表示されているタグを検索し絞り込みます。
- "Clear all filters" ボタン
  - タグや画像の絞り込みを取り消します。
- "Sort by / Sort order" ラジオボタン
  - 下に表示されているタグの並び順を切り替えます。
    - Alphabetical Order / Frequency : アルファベット順／出現頻度順
    - Ascending / Descending : 昇順／降順
- "Filter Images by Tags" チェックボックス
  - 選択したタグによって左の画像を絞り込みます。絞り込まれた画像のキャプションの内容に応じて、タグも絞り込まれます。
- "Selected Tags" テキストボックス (編集不可)
  - 選択したタグをカンマ区切りで表示します。
- "Edit Tags" テキストボックス
  - 選択したタグを編集します。編集内容は絞り込まれている画像にのみ適用されます。選択されていないタグには影響しません。
    - 編集すると、カンマ区切りで同じ場所にあるタグを置換できます。
    - タグを空白に変えることで削除できます。
    - 末尾にタグを追加することでキャプションに新たなタグを追加できます。
      - タグが追加される位置はキャプションの先頭もしくは末尾で、下のチェックボックスで変更できます。
- "Apply changes to filtered images" ボタン
  - 絞り込まれている画像に、タグの変更を適用します。



### "Edit Caption of Selected Image" タブ
![](ss03.png)

- "Caption of Selected Image" テキストボックス
  - 左で選択した画像のキャプションを表示します。
- "Copy caption" ボタン
  - 上のキャプションを下のテキストボックスにコピーします。
- "Edit Caption" テキストボックス
  - ここでキャプションの編集が可能です。
- "Apply changes to selected image" ボタン
  - 選択している画像のキャプションを "Edit Tags" の内容に変更します。