from enum import Enum


class Codec(str, Enum):
    mkvtools_name: str
    ffmpeg_name: str
    ffmpeg_encoder: str | None
    file_extension: str

    def __new__(cls, mkvtools_name, ffmpeg_name, ffmpeg_encoder, file_extension) -> Codec:
        obj = str.__new__(cls, mkvtools_name)
        obj._value_ = (mkvtools_name, ffmpeg_name)
        obj.mkvtools_name = mkvtools_name
        obj.ffmpeg_name = ffmpeg_name
        obj.ffmpeg_encoder = ffmpeg_encoder
        obj.file_extension = file_extension
        return obj


class VideoCodec(Codec):
    #       MKVTool                FFMPEG  FFMPEG   File
    #       name                   name    encoder  extension
    AV1  = ("AV1",                 "av1",  None,    ".av1") # Optimized
    H265 = ("HEVC/H.265/MPEG-H",   "h265", None,    ".h265")
    H264 = ("AVC/H.264/MPEG-4p10", "h264", None,    ".h264")

    @classmethod
    def by_name(cls, name) -> VideoCodec:
        for codec in cls:
            if codec.mkvtools_name == name:
                return codec
        for codec in cls:
            if codec.ffmpeg_name == name:
                return codec
        raise ValueError(f"Unrecognized codec name: {name}")


class AudioCodec(Codec):
    #         MKVTool    FFMPEG    FFMPEG   File
    #         name       name      encoder  extension
    AAC    = ("AAC",     "aac",    None,    ".aac") # Optimized
    AC3    = ("AC-3",    "ac3",    None,    ".ac3") # Optimized
    EAC3   = ("E-AC-3",  "eac3",   None,    ".aac") # Optimized
    VORBIS = ("Vorbis",  "vorbis", None,    ".ogg")
    FLAC   = ("FLAC",    "flac",   None,    ".flac")

    @classmethod
    def by_name(cls, name) -> AudioCodec:
        for codec in cls:
            if codec.mkvtools_name == name:
                return codec
        for codec in cls:
            if codec.ffmpeg_name == name:
                return codec
        raise ValueError(f"Unrecognized codec name: {name}")


class SubtitlesCodec(Codec):
    #         MKVTool            FFMPEG               FFMPEG   File
    #         name               name                 encoder  extension
    SRT    = ("SubRip/SRT",      "srt",               None,    ".srt") # Optimized
    PGS    = ("HDMV PGS",        "hdmv_pgs_subtitle", None,    ".pgs")
    ASS    = ("SubStationAlpha", "ass",               None,    ".ass")
    TX3G   = ("SubRip/SRT",      "mov_text",          "srt",   ".srt")
    #VOBSUB = ("VobSub",          "dvd_subtitle",      None,    ".idx")* # Paire de fichiers .idx et .sub, MKVTools le prend très mal en charge car 2 fichiers

    @classmethod
    def by_name(cls, name) -> SubtitlesCodec:
        for codec in cls:
            if codec.mkvtools_name == name:
                return codec
        for codec in cls:
            if codec.ffmpeg_name == name:
                return codec
        raise ValueError(f"Unrecognized codec name: {name}")

# *VobSub : PAS PRIS EN CHARGE car STANDARD INTROUVABLE
# TODO: Prendre en charge les VobSub (un jour bien motivé)
# https://wiki.multimedia.cx/index.php?title=VOBsub
# https://www.loc.gov/preservation/digital/formats/fdd/fdd000571.shtml
# https://en.wikipedia.org/wiki/Packetized_elementary_stream
# https://dvd.sourceforge.net/dvdinfo/pes-hdr.html
# https://www.bretl.com/mpeghtml/pespckt.HTM
# https://github.com/wireshark/wireshark/blob/master/epan/dissectors/asn1/mpeg-pes/packet-mpeg-pes-template.c