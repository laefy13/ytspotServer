from itertools import islice
import re
from .models import PlaylistsQueries


def savePlaylist(id: str, playlist: dict, get_time: bool) -> None:
    playlist_time = 1 if get_time else 0
    existing_playlist = getMongoItem(id, playlist_time)
    if existing_playlist:
        existing_playlist.delete()
    PlaylistsQueries.objects.using("mongodb").create(
        playlist_id=id, playlist_items=playlist, playlist_time=playlist_time
    )


def getMongoItem(id, get_time) -> PlaylistsQueries:
    playlist_time = 1 if get_time else 0

    return PlaylistsQueries.objects.using("mongodb").filter(
        playlist_id=id, playlist_time=playlist_time
    )


def batch_iterable(iterable, batch_size):
    it = iter(iterable)
    for _ in range(0, len(iterable), batch_size):
        yield list(islice(it, batch_size))


def parseISOTime(iso_duration):
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
    if match:
        hour = str(match.group(1) or "00").zfill(2)
        minute = str(match.group(2) or "00").zfill(2)
        second = str(match.group(3) or "00").zfill(2)
        return hour, minute, second
    else:
        raise ValueError("Invalid ISO duration format")


def getYoutubeTime(playlist, youtube) -> None:

    try:
        video_ids = [key for key in playlist.keys()]
        video_batches = list(batch_iterable(video_ids, 15))
        video_all_map = {}
        for batch in video_batches:
            video_ids_str = ",".join(batch)
            video_request = youtube.videos().list(
                part="contentDetails", id=video_ids_str
            )
            video_response = video_request.execute()

            video_map = {
                item["id"]: item["contentDetails"]["duration"]
                for item in video_response["items"]
            }
            video_all_map.update(video_map)

    except Exception as e:
        pass

    for key, values_array in playlist.items():
        if values_array:
            iso_time = video_all_map.get(key, "PT0S")
            hour, minute, second = parseISOTime(iso_time)
            playlist[key].append(f"{hour}:{minute}:{second}")
