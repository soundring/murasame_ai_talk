import requests
import os
import tempfile

# 音声合成を行う関数
def playCoeiroink(text, filename="output.wav"):
    
    request_body = {
        "styleId": '100',  # 必要なスタイルID
        'speakerUuid': 'b28bb401-bc43-c9c7-77e4-77a2bbb4b283',
        'text': text,
        "speedScale": 1.0,           # 話速の倍率
        "volumeScale": 1.0,          # 音量の倍率
        "pitchScale": 1.0,           # ピッチの倍率
        "intonationScale": 1.0,      # 抑揚の倍率
        "prePhonemeLength": 0.1,     # 前音素の長さ
        "postPhonemeLength": 0.1,    # 後音素の長さ
        "outputSamplingRate": 22050  # 出力サンプリングレート
    }

    synthesis_response = requests.post(f'http://localhost:50032/v1/synthesis', json=request_body)

    if synthesis_response.status_code == 200:
        # 音声ファイルとして一時保存
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(synthesis_response.content)
            temp_filename = temp_file.name

        print(f"音声が一時ファイル {temp_filename} に保存されました。")

        os.system(f"afplay {temp_filename}")

        # 再生後に一時ファイルを削除
        os.remove(temp_filename)
        print(f"一時ファイル {temp_filename} を削除しました。")
    else:
        print(f"Error in synthesis: {synthesis_response.text}")