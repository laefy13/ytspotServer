import base64
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
from .models import SpotifyUser
from dotenv import load_dotenv

load_dotenv()


# Create your views here.
class Youtube(View):
    def get(self, request):
        from googleapiclient.discovery import build
        from google.oauth2 import service_account

        SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE_PATH")

        yt_playlist = request.GET.get("yt_playlist")
        include_images = request.GET.get("images")
        if not yt_playlist or not include_images:
            return JsonResponse({"error": "Request Error"}, status=400)
        split_playlist = yt_playlist.split("=")
        playlist_id = split_playlist[len(split_playlist) - 1]
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
                    part="snippet",
                    playlistId=playlist_id,
                    pageToken=next_page_token,
                    maxResults=1000,
                )
                playlist_response = playlist_request.execute()

                playlist_items.extend(playlist_response["items"])
                next_page_token = playlist_response.get("nextPageToken")

                if not next_page_token:
                    break
            if include_images != "0":
                for item in playlist_items:
                    video_title = item["snippet"]["title"]
                    try:
                        video_id = [
                            item["snippet"]["resourceId"]["videoId"],
                            item["snippet"]["thumbnails"]["default"]["url"],
                        ]
                    except:
                        pass
                    urls[video_title] = video_id
            else:
                for item in playlist_items:

                    video_title = item["snippet"]["title"]
                    video_id = [item["snippet"]["resourceId"]["videoId"]]
                    urls[video_title] = video_id
            return JsonResponse({"urls": urls}, status=200)
        except Exception as e:
            return JsonResponse({"error": "Youtube playlist error"}, status=400)


class Spotify(View):
    def get(self, request):
        import spotipy
        from spotipy.oauth2 import SpotifyClientCredentials

        spotify_playlist = request.GET.get("spotify_playlist")
        include_images = request.GET.get("images")

        if not spotify_playlist or not include_images:
            return JsonResponse({"error": "Request Error"}, status=400)

        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

        if not client_id or not client_secret:
            return JsonResponse({"error": "Spotify credentials not set"}, status=400)

        auth_manager = SpotifyClientCredentials()
        sp = spotipy.Spotify(auth_manager=auth_manager)

        try:
            playlist = sp.playlist_items(spotify_playlist)["items"]
            urls = {}
            if include_images != "0":
                for item in playlist:
                    urls[item["track"]["name"]] = [
                        item["track"]["external_urls"]["spotify"],
                        item["track"]["album"]["images"][0]["url"],
                    ]
            else:
                for item in playlist:
                    urls[item["track"]["name"]] = [
                        item["track"]["external_urls"]["spotify"],
                    ]
            print("should send urls")
            return JsonResponse({"urls": urls}, status=200)
        except:
            return JsonResponse({"error": "Spotify playlist error"}, status=400)


class SpotifyLogin(View):

    def get(self, request):

        client_id = os.getenv("SPOTIPY_CLIENT_ID")
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        self_url = "https://ytspotserver.azurewebsites.net"

        if not client_id or not client_secret:
            return JsonResponse({"error": "Spotify credentials not set"}, status=400)

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
        self_url = "https://ytspotserver.azurewebsites.net"
        main_url = "https://lemon-grass-0b1c6b800.5.azurestaticapps.net/"

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
            access_token = response.json().get("access_token")
            user_uuid = uuid.uuid4()
            instance = SpotifyUser(uuid=user_uuid, token=access_token)
            instance.save()
            return redirect(f"{main_url}?id={user_uuid}")
            return JsonResponse({"token": access_token})
        else:
            return HttpResponse(
                "Error occurred during token retrieval", status=response.status_code
            )


def getToken(request):
    try:
        spotify_uuid = request.headers.get("X-Spotify-UUID")
        spotify_user = SpotifyUser.objects.get(uuid=spotify_uuid)
        current_time = timezone.now()
        time_difference = current_time - spotify_user.added_at
        if time_difference.total_seconds() < 3600:
            access_token = spotify_user.token
            return JsonResponse({"token": access_token}, status=200)
        else:

            return HttpResponseRedirect(f"/api/auth/login")
    except Exception as e:
        return JsonResponse({"token": "Spotify user not found"}, status=400)
