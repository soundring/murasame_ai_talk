import os
import subprocess

def generateVoicePeakAudio(script, narrator="Miyamai Moca", bosoboso=0, doyaru=100, honwaka=0, angry=0, teary=0):
    """
    任意のテキストをVOICEPEAKのナレーターに読み上げさせる関数（Mac版）
    script: 読み上げるテキスト（文字列）
    narrator: ナレーターの名前（文字列）
    bosoboso: ぼそぼその度合い
    doyaru: ドヤるの度合い
    honwaka: ほんわかの度合い
    angry: 怒りの度合い
    teary: 泣きの度合い
    """
    exepath = "/Applications/voicepeak.app/Contents/MacOS/voicepeak"
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
        "-e", f"bosoboso={bosoboso},doyaru={doyaru},honwaka={honwaka},angry={angry},teary={teary}"  # 感情の設定
    ]
    
    # subprocess で VOICEPEAK を実行
    process = subprocess.Popen(args)
    process.communicate()  # プロセスが終了するのを待つ
    
    # WAVファイルを読み込んでバイナリデータを返す
    with open(outpath, 'rb') as wav_file:
        audio_data = wav_file.read()

    os.remove(outpath)

    return audio_data