from ynca.constants import Playback, PlaybackInfo, Repeat
from ynca.function_mixins import Shuffle
from ynca.mediaplayback_subunits import MediaPlaybackSubunitBase

SYS = "SYS"
SUBUNIT = "SUBUNIT"

INITIALIZE_FULL_RESPONSES = [
    (
        (SUBUNIT, "METAINFO"),
        [
            (SUBUNIT, "ALBUM", "Album"),
            (SUBUNIT, "ARTIST", "Artist"),
            (SUBUNIT, "SONG", "Song"),
        ],
    ),
    (
        (SUBUNIT, "AVAIL"),
        [
            (SUBUNIT, "AVAIL", "Ready"),
        ],
    ),
    (
        (SUBUNIT, "PLAYBACKINFO"),
        [
            (SUBUNIT, "PLAYBACKINFO", "Pause"),
        ],
    ),
    (
        (SUBUNIT, "REPEAT"),
        [
            (SUBUNIT, "REPEAT", "Single"),
        ],
    ),
    (
        (SUBUNIT, "SHUFFLE"),
        [
            (SUBUNIT, "SHUFFLE", "On"),
        ],
    ),
    (
        (SYS, "VERSION"),
        [
            (SYS, "VERSION", "Version"),
        ],
    ),
]


class DummyMediaPlaybackSubunit(MediaPlaybackSubunitBase):
    id = "SUBUNIT"


def test_initialize(connection, update_callback):

    connection.get_response_list = INITIALIZE_FULL_RESPONSES

    dmps = DummyMediaPlaybackSubunit(connection)
    dmps.register_update_callback(update_callback)

    dmps.initialize()

    assert dmps.repeat is Repeat.SINGLE
    assert dmps.shuffle is Shuffle.ON
    assert dmps.album == "Album"
    assert dmps.artist == "Artist"
    assert dmps.song == "Song"
    assert dmps.playbackinfo is PlaybackInfo.PAUSE

    dmps.repeat = Repeat.ALL
    connection.put.assert_called_with(SUBUNIT, "REPEAT", "All")
    dmps.shuffle = Shuffle.OFF
    connection.put.assert_called_with(SUBUNIT, "SHUFFLE", "Off")
    dmps.playback(Playback.PLAY)
    connection.put.assert_called_with(SUBUNIT, "PLAYBACK", "Play")
