import os
import subprocess
import psutil
import time

# 既存のVOICEPEAKプロセスを終了させる
def terminate_existing_voicepeak_process():
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if proc.info['name'] == "voicepeak":
            print(f"VOICEPEAKプロセス (PID: {proc.info['pid']}) を終了します。")
            proc.terminate()
            try:
                proc.wait(timeout=3)  # 3秒待機
            except psutil.TimeoutExpired:
                print("プロセスが終了しないため、強制終了します。")
                proc.kill()
            finally:
                # プロセスが終了するのを確認
                proc.wait()

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
      os.makedirs(outdir, exist_ok=True)

    terminate_existing_voicepeak_process()

    # 引数を作成 (VOICEPEAK コマンドに渡す引数)
    args = [
        exepath,
        "-s", script,          # 読み上げるスクリプト
        "-n", narrator,        # ナレーターの名前
        "-o", outpath,         # 出力先のファイル
        "-e", f"bosoboso={bosoboso},doyaru={doyaru},honwaka={honwaka},angry={angry},teary={teary}"  # 感情の設定
    ]
    
    # subprocess で VOICEPEAK を実行
    max_retries=3
    for attempt in range(max_retries):
      try:
          subprocess.run(args, check=True, timeout=20)
          break
      except subprocess.TimeoutExpired:
          print("タイムアウトが発生しました。VOICEPEAKプロセスを終了します。")
          terminate_existing_voicepeak_process()
          if attempt < max_retries - 1:
            print(f"リトライします... (試行回数: {attempt + 1})")
            time.sleep(1)
          else:
            raise RuntimeError("最大リトライ回数に達しました。")
      except subprocess.CalledProcessError as e:
            print(f"VOICEPEAKの実行に失敗しました。エラー: {e}")
            if attempt < max_retries - 1:
              print(f"リトライします... (試行回数: {attempt + 1})")
              time.sleep(1)
            else:
                raise RuntimeError("最大リトライ回数に達しました。")

    # WAVファイルを読み込んでバイナリデータを返す
    with open(outpath, 'rb') as wav_file:
        audio_data = wav_file.read()

    os.remove(outpath)

    return audio_data