from .views import (
    Youtube,
    Spotify,
    SpotifyCallback,
    SpotifyLogin,
    SpotifyRefresh,
    SpotifyLogout,
    getToken,
)
from django.urls import path, re_path

urlpatterns = [
    path("youtube", Youtube.as_view(), name="youtube"),
    path("spotify", Spotify.as_view(), name="spotify"),
    re_path(
        r"^auth/login/(?P<browser_id>[\w\-]+)$",
        SpotifyLogin.as_view(),
        name="spotifyLogin",
    ),
    re_path(
        r"auth/callback",
        SpotifyCallback.as_view(),
        name="spotifyCallback",
    ),
    path("auth/refresh", SpotifyRefresh.as_view(), name="spotifyRefresh"),
    path("auth/logout", SpotifyLogout.as_view(), name="logout"),
    path("token", getToken, name="getToken"),
]
