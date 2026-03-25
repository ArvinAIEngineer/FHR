def test_tts_payload_with_message_id():
    response = client.post("/api/tts/synthesize", json={
        "messageID": "msg123",
        "text": "Testing new structure",
        "language": "en",
        "gender": "female"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["messageID"] == "msg123"
    assert "audio_base64" in data
    assert data["content_type"] == "wav"
