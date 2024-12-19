import requests
import os
import tempfile

def generateVoiceVoxAudio(text, speaker=14):
    # 1. テキストから音声合成のためのクエリを作成
    params = {'text': text, 'speaker': speaker}
    query_response = requests.post(f'http://127.0.0.1:50021/audio_query', params=params)

    if query_response.status_code != 200:
        print(f"Error in audio_query: {query_response.text}")
        return

    query = query_response.json()

    # 2. クエリを元に音声データを生成
    synthesis_params = {'speaker': speaker}
    synthesis_response = requests.post(f'http://127.0.0.1:50021/synthesis', params=synthesis_params, json=query)

    if synthesis_response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(synthesis_response.content)
            temp_filename = temp_file.name

        return os.path.basename(temp_filename)
    else:
        print(f"Error in synthesis: {synthesis_response.text}")