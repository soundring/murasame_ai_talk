import requests

def generateVoiceVoxAudio(text, speaker=61):
    print('VoiceVoxで音声合成を開始')
    # 1. テキストから音声合成のためのクエリを作成
    params = {'text': text, 'speaker': speaker}
    query_response = requests.post(f'http://127.0.0.1:50021/audio_query', params=params)

    if query_response.status_code != 200:
        print(f"Error in audio_query: {query_response.text}")
        return

    query = query_response.json()

    # 2. クエリを元に音声データを生成
    synthesis_params = {'speaker': speaker}
    synthesis_response = requests.post(f'http://127.0.0.1:50021/synthesis',
                                        params=synthesis_params,
                                        json=query
                                        )

    if synthesis_response.status_code == 200:
        return synthesis_response.content
    else:
        print(f"Error in synthesis: {synthesis_response.text}")