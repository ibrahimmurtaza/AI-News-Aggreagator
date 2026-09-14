from datetime import datetime, timedelta, timezone

import httpx

from app.youtube_service import YouTubeChannel, YouTubeService


RSS = b'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <entry>
    <id>yt:video:recent123</id>
    <yt:videoId>recent123</yt:videoId>
    <title>Recent AI update</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=recent123" />
    <published>2026-09-14T09:00:00+00:00</published>
  </entry>
  <entry>
    <id>yt:video:old123</id>
    <yt:videoId>old123</yt:videoId>
    <title>Old AI update</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=old123" />
    <published>2026-09-12T09:00:00+00:00</published>
  </entry>
</feed>'''


class FakeTranscriptClient:
    def fetch(self, video_id: str, languages: tuple[str, ...]):
        assert video_id == "recent123"
        assert languages == ("en",)
        return [Snippet("Hello"), Snippet("from the video.")]


class Snippet:
    def __init__(self, text: str):
        self.text = text


def test_get_recent_videos_filters_by_cutoff_and_adds_transcript():
    request = httpx.Request(
        "GET", "https://www.youtube.com/feeds/videos.xml?channel_id=UC123"
    )
    response = httpx.Response(200, content=RSS, request=request)
    client = httpx.Client(transport=httpx.MockTransport(lambda _: response))
    service = YouTubeService(
        [YouTubeChannel(name="AI channel", channel_id="UC123")],
        http_client=client,
        transcript_client=FakeTranscriptClient(),
    )

    videos = service.get_recent_videos(
        within=timedelta(hours=24),
        now=datetime(2026, 9, 14, 12, tzinfo=timezone.utc),
        include_transcripts=True,
    )

    assert len(videos) == 1
    assert videos[0].video_id == "recent123"
    assert videos[0].transcript == "Hello from the video."