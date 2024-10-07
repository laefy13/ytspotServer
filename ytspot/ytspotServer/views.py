import base64
from itertools import islice
import re
from django.utils import timezone
import random
import string
from urllib.parse import urlencode
import uuid
from django.shortcuts import redirect, render
from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.views import View
import requests
import os
from .models import SpotifyUser, PlaylistsQueries
from dotenv import load_dotenv
from .utils import *

load_dotenv()


# Create your views here.
class Youtube(View):
    def get(self, request):
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE_PATH")

        yt_playlist = request.GET.get("yt_playlist")
        get_time = request.GET.get("get_time")
        is_cache = request.GET.get("is_cache")
        get_time = get_time.lower() == "true" if get_time else None
        is_cache = is_cache.lower() == "true" if is_cache else None

        if (
            not yt_playlist
            or type(is_cache) != bool
            or is_cache == None
            or type(get_time) != bool
            or get_time == None
        ):
            return JsonResponse({"error": "Request Error"}, status=400)
        split_playlist = yt_playlist.split("=")
        playlist_id = split_playlist[len(split_playlist) - 1]

        if is_cache:
            existing_playlist = getMongoItem(playlist_id, get_time)
            if existing_playlist:
                return JsonResponse(
                    {"urls": existing_playlist.first().playlist_items}, status=200
                )

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/youtube.readonly"],
        )
        youtube = build("youtube", "v3", credentials=credentials)
        playlist_items = []
        next_page_token = None
        urls = {}

        try:
            while True:
                playlist_request = youtube.playlistItems().list(
                    part=["snippet"],
                    playlistId=playlist_id,
                    pageToken=next_page_token,
                    maxResults=1000,
                )
                playlist_response = playlist_request.execute()
                playlist_items.extend(playlist_response.get("items", []))
                next_page_token = playlist_response.get("nextPageToken")

                if not next_page_token:
                    break
            for item in playlist_items:
                try:
                    urls[item["snippet"]["resourceId"]["videoId"]] = [
                        item["snippet"]["title"],
                        item["snippet"]["thumbnails"]["default"]["url"],
                    ]
                except:
                    pass
            if get_time:
                getYoutubeTime(urls, youtube)
            savePlaylist(playlist_id, urls, get_time)
            return JsonResponse({"urls": urls}, status=200)
        except Exception as e:
            return JsonResponse({"error": "Youtube playlist error"}, status=400)


class Spotify(View):
    def _msToTime(self, ms: int) -> str:
        total_seconds = ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def get(self, request):
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        spotify_playlist = request.GET.get("spotify_playlist")
        get_time = request.GET.get("get_time")
        is_cache = request.GET.get("is_cache")
        get_time = get_time.lower() == "true" if get_time else None
        is_cache = is_cache.lower() == "true" if is_cache else None

        if (
            not spotify_playlist
            or type(get_time) != bool
            or type(is_cache) != bool
            or get_time == None
            or is_cache == None
        ):
            return JsonResponse({"error": "Request Error"}, status=400)

        if is_cache:
            existing_playlist = getMongoItem(spotify_playlist, get_time)
            if existing_playlist:
                items = {"urls": existing_playlist.first().playlist_items}
                return JsonResponse(items, status=200)

        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

        if not client_id or not client_secret:
            return JsonResponse({"error": "Spotify credentials not set"}, status=400)

        auth_manager = SpotifyClientCredentials()
        sp = spotipy.Spotify(auth_manager=auth_manager)

        try:
            playlist = []
            offset = 0
            while True:

                temp = sp.playlist_items(spotify_playlist, offset=offset)["items"]
                temp_len = len(temp)
                if temp_len < 0:
                    break
                playlist += temp
                offset += 100
                if temp_len < 100:
                    break

            urls = {}
            if get_time:
                for item in playlist:
                    urls[item["track"]["id"]] = [
                        item["track"]["name"],
                        item["track"]["album"]["images"][0]["url"],
                        self._msToTime(item["track"]["duration_ms"]),
                    ]
            else:
                for item in playlist:
                    urls[item["track"]["id"]] = [
                        item["track"]["name"],
                        item["track"]["album"]["images"][0]["url"],
                    ]
            savePlaylist(spotify_playlist, urls, get_time)
            return JsonResponse({"urls": urls}, status=200)
        except Exception as e:
            return JsonResponse({"error": "Spotify playlist error"}, status=400)


class SpotifyLogin(View):

    def get(self, request, browser_id):

        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        self_url = os.getenv("SELF_URL")

        if not client_id or not client_secret or not browser_id:
            return JsonResponse({"error": "Spotify credentials not set"}, status=400)

        request.session["browser-id"] = browser_id

        scope = "streaming \
                user-read-email \
                user-read-private \
                user-modify-playback-state \
                user-read-currently-playing \
                user-read-playback-state"
        state = "".join(random.choices(string.ascii_letters + string.digits, k=16))

        auth_query_parameters = {
            "response_type": "code",
            "client_id": client_id,
            "scope": scope,
            "redirect_uri": f"{self_url}/api/auth/callback",
            "state": state,
        }

        redirect_url = "https://accounts.spotify.com/authorize/?" + urlencode(
            auth_query_parameters
        )

        return redirect(redirect_url)


class SpotifyCallback(View):

    def get(self, request):

        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        self_url = os.getenv("SELF_URL")
        main_url = os.getenv("MAIN_URL")

        if not client_id or not client_secret:
            return JsonResponse({"error": "Spotify credentials not set"}, status=400)
        code = request.GET.get("code")
        auth_options = {
            "url": "https://accounts.spotify.com/api/token",
            "data": {
                "code": code,
                "redirect_uri": f"{self_url}/api/auth/callback",
                "grant_type": "authorization_code",
            },
            "headers": {
                "Authorization": "Basic "
                + base64.b64encode(
                    bytes(f"{client_id}:{client_secret}", "utf-8")
                ).decode("utf-8"),
            },
        }
        response = requests.post(**auth_options)
        if response.status_code == 200:
            res_json = response.json()
            access_token = res_json.get("access_token")
            user_uuid = uuid.uuid4()
            refresh_token = res_json.get("refresh_token")
            browser_id = request.session["browser-id"]

            instance = SpotifyUser(
                uuid=user_uuid,
                token=access_token,
                refresh_token=refresh_token,
                browser_id=browser_id,
            )
            instance.save()
            return redirect(f"{main_url}?id={user_uuid}")
        else:
            return HttpResponse(
                "Error occurred during token retrieval", status=response.status_code
            )


class SpotifyRefresh(View):
    def get(self, request):
        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

        if not client_id or not client_secret:
            return JsonResponse({"error": "Spotify credentials not set"}, status=400)

        code = request.GET.get("code")
        spotify_uuid = request.headers.get("X-Spotify-UUID")
        browser_id = request.headers.get("X-Browser-ID")

        if not code or not spotify_uuid or not browser_id:
            return JsonResponse({"error": "Request Error"}, status=400)

        spotify_user = SpotifyUser.objects.get(
            uuid=spotify_uuid, token=code, browser_id=browser_id
        )
        if not spotify_user:
            return JsonResponse({"error": "No user found"}, status=400)
        auth_options = {
            "url": "https://accounts.spotify.com/api/token",
            "data": {
                "refresh_token": spotify_user.refresh_token,
                "grant_type": "refresh_token",
            },
            "headers": {
                "Authorization": "Basic "
                + base64.b64encode(
                    bytes(f"{client_id}:{client_secret}", "utf-8")
                ).decode("utf-8"),
                "Content-Type": "application/x-www-form-urlencoded",
            },
        }
        response = requests.post(**auth_options)

        if response.status_code == 200:
            spotify_user.delete()
            res_json = response.json()
            access_token = res_json.get("access_token")
            spotify_user.token = access_token
            spotify_user.save()
            return JsonResponse({"token": access_token}, status=200)
        else:
            return HttpResponse(
                "Error occurred during token retrieval", status=response.status_code
            )


class SpotifyLogout(View):

    def get(self, request):
        """
        no browser id in this case losing the spotify is not really big problem

        """
        code = request.GET.get("code")
        spotify_uuid = request.headers.get("X-Spotify-UUID")
        browser_id = request.headers.get("X-Browser-ID")
        if not code or not spotify_uuid:
            return JsonResponse({"error": "Request Error"}, status=400)

        spotify_user = SpotifyUser.objects.get(
            uuid=spotify_uuid, token=code, browser_id=browser_id
        )
        if not spotify_user:
            return JsonResponse({"error": "No user found"}, status=400)
        try:
            spotify_user.delete()
            return JsonResponse({"status": "data deleted from server"}, status=200)
        except:
            return JsonResponse({"error": "error while trying to delete"}, status=400)


def getToken(request):
    try:
        spotify_uuid = request.headers.get("X-Spotify-UUID")
        browser_id = request.headers.get("X-Browser-ID")
        spotify_user = SpotifyUser.objects.get(uuid=spotify_uuid, browser_id=browser_id)
        current_time = timezone.now()
        time_difference = current_time - spotify_user.added_at
        access_token = spotify_user.token
        if time_difference.total_seconds() < 3600:
            return JsonResponse({"token": access_token, "expired": False}, status=200)
        else:
            return JsonResponse({"token": access_token, "expired": True}, status=200)

    except Exception as e:
        return JsonResponse({"token": "", "expired": False}, status=400)
