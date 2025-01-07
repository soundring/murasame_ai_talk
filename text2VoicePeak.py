import os
import subprocess
import time
from functools import wraps
import threading
import queue

class VoicePeakIOError(Exception):
    """VOICEPEAK の I/O 関連のエラー"""
    pass

class VoicePeakRetryError(Exception):
    """リトライ失敗時のエラー"""
    pass

def retry_on_error(max_attempts=3, initial_delay=1, backoff_factor=2, max_delay=10):
    """
    エラー時にリトライを行うデコレータ
    
    Parameters:
    - max_attempts: 最大試行回数
    - initial_delay: 初回リトライまでの待機時間（秒）
    - backoff_factor: 待機時間の増加倍率
    - max_delay: 最大待機時間（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (VoicePeakIOError, subprocess.TimeoutExpired) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        print(f"試行 {attempt + 1}/{max_attempts} が失敗しました: {str(e)}")
                        print(f"{delay}秒後にリトライします...")
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    continue
                except Exception as e:
                    # 想定外のエラーは即座に再送出
                    raise
            
            # 全てのリトライが失敗
            raise VoicePeakRetryError(f"最大試行回数（{max_attempts}回）を超えました。最後のエラー: {str(last_exception)}")
        
        return wrapper
    return decorator

voicepeak_queue = queue.Queue()

def voicepeak_worker():
    while True:
        task = voicepeak_queue.get()
        if task is None:
            break  # 終了信号
        script, narrator, bosoboso, doyaru, honwaka, angry, teary, result_queue = task
        try:
            outdir = "一時ファイル保管場所"
            outpath = os.path.join(outdir, f"output_{int(time.time())}_{os.getpid()}.wav")
            
            if not os.path.exists(outdir):
                os.makedirs(outdir, exist_ok=True)
        
            args = [
                "/Applications/voicepeak.app/Contents/MacOS/voicepeak",
                "-s", script,
                "-n", narrator,
                "-o", outpath,
                "-e", f"bosoboso={bosoboso},doyaru={doyaru},honwaka={honwaka},angry={angry},teary={teary}"
            ]
        
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
                
            stdout, stderr = process.communicate(timeout=30)
                
            if process.returncode != 0:
                raise VoicePeakIOError(f"VOICEPEAK実行エラー: {stderr.decode('utf-8', errors='ignore')}")
                
            if os.path.exists(outpath):
                with open(outpath, 'rb') as f:
                    data = f.read()
                result_queue.put(data)
            else:
                result_queue.put(None)
        except Exception as e:
            result_queue.put(e)
        finally:
            if os.path.exists(outpath):
                os.remove(outpath)
            voicepeak_queue.task_done()


worker_thread = threading.Thread(target=voicepeak_worker, daemon=True)
worker_thread.start()

@retry_on_error(max_attempts=3, initial_delay=1, backoff_factor=2)
def generateVoicePeakAudio(script, narrator="Miyamai Moca", bosoboso=0, doyaru=50, honwaka=25, angry=0, teary=0):
    print('VOICEPEAKで音声合成を開始')
    result_queue = queue.Queue()
    voicepeak_queue.put((script, narrator, bosoboso, doyaru, honwaka, angry, teary, result_queue))
    result = result_queue.get()
    if isinstance(result, Exception):
        raise result
    return result