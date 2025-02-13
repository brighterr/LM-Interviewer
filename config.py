class Config:
    """ Fill configs below in config.py """

    # app.py 配置项
    default_port = 8000  # 例如设置默认端口为 8000

    # asr.py, audio_service.py 配置项
    audio_appid = 'your_audio_appid_here'  # 替换为实际的 audio_appid
    audio_token = 'your_audio_token_here'  # 替换为实际的 audio_token
    asr_cluster = 'your_asr_cluster_here'  # 替换为实际的 ASR 集群地址
    tts_cluster = 'your_tts_cluster_here'  # 替换为实际的 TTS 集群地址
    tts_uid = 'your_tts_uid_here'  # 替换为实际的 TTS 用户 ID

    # query_gpt.py 配置项
    gpt_key = 'your_gpt_key_here'  # 替换为实际的 GPT API 密钥
    gpt_endpoint = 'https://api.openai.com/v1/completions'  # 替换为实际的 GPT API 端点
