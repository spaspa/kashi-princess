#! /usr/bin/env python3
import sys
import click
from searcher import (
    LyricsNotFoundError,
    MutipleLyricsSearcher,
    JLyricSearcher,
    UtanetSearcher,
    PetitLyricsSearcher,
    JLyricTitleSearcher
)

@click.command()
@click.argument('title')
@click.argument('artist')
@click.option('--strict/--no-strict',
              is_flag=True,
              default=False,
              help="Check artist name strictly or not.")
def kashi_searcher(title,
                   artist="",
                   strict=False):
    searcher = MutipleLyricsSearcher([
        JLyricSearcher,
        UtanetSearcher,
        PetitLyricsSearcher,
        JLyricTitleSearcher
    ], strict)
    try:
        lyrics = searcher.fuzzy_title_search(artist, title)
    except LyricsNotFoundError:
        print("Lyrics not found.")
        sys.exit()
    print(lyrics)

kashi_searcher()
