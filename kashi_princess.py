#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from mutagen import MutagenError
from mutagen.easymp4 import MP4
from mutagen.mp4 import MP4StreamInfoError
import click
from searcher import (
    LyricsNotFoundError,
    MutipleLyricsSearcher,
    JLyricSearcher,
    UtanetSearcher,
    PetitLyricsSearcher,
    JLyricTitleSearcher
)


class TrackInfo:
    def __init__(self, path):
        try:
            self.tags = MP4(path)
        except MP4StreamInfoError:
            self.artist = None
            self.title = None
            self.shorten_lyrics = None
            self.message = f"Not a mp4 file: {path}"
            return

        self.artist = self.tags.get("\xa9ART", [None])[0]
        self.title = self.tags.get("\xa9nam", [None])[0]
        self.genre = self.tags.get("\xa9gen", [None])[0]

        if not self.artist or not self.title:
            self.shorten_lyrics = None
            self.message = f"Incomplete track: {path}"
            return

        if "\xa9lyr" in self.tags:
            lyrics = self.tags['\xa9lyr'][0][:20]
            self.shorten_lyrics = lyrics.replace('\n', ' ')
            self.message = f"Lyrics are already embeded: {self.shorten_lyrics}"
        else:
            # default value
            self.shorten_lyrics = None
            self.message = "Lyrics not found."

    def set_skipped(self):
        self.shorten_lyrics = None
        self.message = f"Skipped."

    def set_lyrics(self, lyrics, dry_run=False):
        if not dry_run:
            self.tags['\xa9lyr'] = lyrics
            self.tags.save()
        self.shorten_lyrics = lyrics[:20].replace('\n', ' ')
        self.message = f"Lyrics found: {self.shorten_lyrics}……"

    def delete_lyrics(self, dry_run=False):
        if not dry_run:
            lyrics = self.tags.pop('\xa9lyr', None)
            self.tags.save()
        self.shorten_lyrics = None
        if lyrics:
            self.message = f"Lyrics deleted."

    def print(self, separator=True, shorten=False, show_message=True):
        if self.artist and self.title:
            if shorten and self.shorten_lyrics:
                print(f"{self.artist} - {self.title}  {self.shorten_lyrics}……")
            elif shorten and not self.shorten_lyrics:
                print(f"{self.artist} - {self.title}")
            else:
                print(f"artist : {self.artist}")
                print(f"title  : {self.title}")
        if show_message:
            print(f"{self.message}")
        if separator:
            print("--------------------------------")


def create_lyrics_in_mp4(path, lyrics, force=False):
    tags = MP4(path)
    if '\xa9lyr' in tags and not force:
        return
    tags['\xa9lyr'] = lyrics
    tags.save()


@click.command()
@click.argument('root')
@click.option('--strict/--no-strict',
              is_flag=True,
              default=False,
              help="Check artist name strictly or not.")
@click.option('--dry-run',
              is_flag=True,
              default=False,
              help="Do not actutually embed lyrics.")
@click.option('--force',
              is_flag=True,
              default=False,
              help="Force overwrite lyrics.")
@click.option('--verbose',
              is_flag=True,
              default=False,
              help="Show detailed informations.")
@click.option('--exclude-title',
              default=["off vocal", "instrumental"],
              multiple=True,
              help="Title to execlude (Partial match).")
@click.option('--exclude-genre',
              default=[],
              multiple=True,
              help="Genre to execlude (Partial match).")
@click.option('--delete-excluded',
              is_flag=True,
              default=False,
              help="Delete lyrics of excluded songs.")
def kashi_princess(root,
                   strict=True,
                   dry_run=False,
                   force=False,
                   verbose=False,
                   exclude_title=["off vocal", "instrumental"],
                   exclude_genre=[],
                   delete_excluded=False):
    searcher = MutipleLyricsSearcher([
        JLyricSearcher,
        UtanetSearcher,
        PetitLyricsSearcher,
        JLyricTitleSearcher
    ], strict)

    results_not_mp4 = []
    results_skipped = []
    results_embeded = []
    results_not_found = []
    results_found = []

    rootPath = Path(root).expanduser().resolve()
    for f in rootPath.glob("**/*.m4a"):
        try:
            info = TrackInfo(f)
        except MutagenError:
            print("Mutagen error occured. Skipping")
            continue

        if not info.artist or not info.title:
            if verbose:
                info.print()
            continue

        # check skip
        title_check = [kw.lower() in info.title.lower()
                       for kw in exclude_title]
        if info.genre:
            genre_check = [kw.lower() in info.genre.lower()
                           for kw in exclude_genre]
        else:
            genre_check = []

        if (any(title_check + genre_check)):
            info.set_skipped()
            if delete_excluded:
                info.delete_lyrics()
            results_skipped.append(info)
            if verbose:
                info.print()
            continue

        if info.shorten_lyrics and not force:
            results_embeded.append(info)
            if verbose:
                info.print()
            continue

        try:
            lyrics = searcher.fuzzy_title_search(info.artist, info.title)
        except LyricsNotFoundError:
            if info.shorten_lyrics and force:
                info.delete_lyrics(dry_run)
            results_not_found.append(info)
            if verbose:
                info.print()
            continue

        info.set_lyrics(lyrics)
        if not dry_run:
            info.set_lyrics(lyrics, dry_run)
        if verbose:
            info.print()
        results_found.append(info)

    if dry_run:
        print(f"Lyrics found ({len(results_found)}):")
    else:
        print(f"Lyrics embeded ({len(results_found)}):")
    print("=================================")
    for info in results_found:
        info.print()
    print("=================================")
    print(f"Lyrics not found ({len(results_not_found)}):")
    print("=================================")
    for info in results_not_found:
        info.print(separator=False, shorten=True, show_message=False)
    print("=================================")
    print(f"Already embeded ({len(results_embeded)}):")
    print("=================================")
    for info in results_embeded:
        info.print(separator=False, shorten=True, show_message=False)
    print("=================================")
    print(f"{len(results_skipped)} file(s) are skipped.")
    print(f"{len(results_not_mp4)} file(s) are not mp4.")


kashi_princess()
