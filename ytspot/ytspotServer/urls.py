from .views import Youtube, Spotify, SpotifyCallback, SpotifyLogin, getToken
from django.urls import path

urlpatterns = [
    path("youtube", Youtube.as_view(), name="youtube"),
    path("spotify", Spotify.as_view(), name="spotify"),
    path("auth/login", SpotifyLogin.as_view(), name="spotifyLogin"),
    path("auth/callback", SpotifyCallback.as_view(), name="spotifyCallback"),
    path("token", getToken, name="getToken"),
]
