import os
import subprocess

def playVoicePeak(script, narrator="Japanese Female 1", happy=50, sad=50, angry=50, fun=50):
    """
    任意のテキストをVOICEPEAKのナレーターに読み上げさせる関数（Mac版）
    script: 読み上げるテキスト（文字列）
    narrator: ナレーターの名前（文字列）
    happy: 嬉しさの度合い
    sad: 悲しさの度合い
    angry: 怒りの度合い
    fun: 楽しさの度合い
    """


    exepath = "/Applications/voicepeak.app/Contents/MacOS/voicepeak"  # VOICEPEAKのインストールパスを指定
    # wav出力先
    outdir = "一時ファイル保管場所"
    outpath = os.path.join(outdir, "output.wav")
    
    # 出力先ディレクトリが存在しない場合は作成
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # 引数を作成 (VOICEPEAK コマンドに渡す引数)
    args = [
        exepath,
        "-s", script,          # 読み上げるスクリプト
        "-n", narrator,        # ナレーターの名前
        "-o", outpath,         # 出力先のファイル
        "-e", f"happy={happy},sad={sad},angry={angry},fun={fun}"  # 感情の設定
    ]
    
    # subprocess で VOICEPEAK を実行
    process = subprocess.Popen(args)
    process.communicate()  # プロセスが終了するのを待つ
    
    
    os.system(f"afplay {outpath}")
    
    # wav ファイルを削除
    os.remove(outpath)