"""
This script generates a bible plan from user-defined specifications.

Copyright 2021 David Kim. All rights reserved.
"""

# Imports
import json
import csv
import io
import os

import requests
import argparse
import datetime

import utils.utils
try:
    from utils.secrets import API_KEY
except:
    API_KEY = None

base_url = "https://api.scripture.api.bible"
# KJV version id - hardcoded from API
bible_version = "de4e12af7f28f599-01"
kjv_url = f"/v1/bibles/{bible_version}"


def request_metadata(force, **config) -> list:
    """
    Makes requests to the Bible API to retrieve the metadata for the
    specified books of the Bible.

    Args:
        force (bool): If True, force retrieval from API even if cache exists.
        config (**kwargs): Requires "books" arg; list of books to be processed.
    
    Returns:
        list: The metadata of the processed books, with each element as a dict.
    """

    if "books" not in config:
        raise ValueError("List of books not provided")

    # First, get the list of book objects from the API
    if API_KEY is not None:
        params = {"api-key": API_KEY}
        req0_url = "/books"
        url = f"{base_url}{kjv_url}{req0_url}"
        books_res = requests.get(url, headers=params)
        books = books_res.json()["data"]
        print("Connection established to the Bible API.")
    else:
        with open("books_of_the_bible.json", "r") as bf:
            books = json.load(bf)["data"]
        print("Secrets file not found, so defaulting to prefetched data.")

    books = [d for d in books if d["name"] in config["books"]]

    meta = []

    for book in books:
        book_name = book["name"]
        book_id = book["id"]
        print(f"Gathering statistics for {book_name}...")

        # If we did this before, no need to req it again. Let's skip the API
        book_data_path = os.path.join("utils", "cache", f"{book_id}.txt")
        if not force and os.path.isfile(book_data_path):
            with open(book_data_path, "r") as rf:
                lines = rf.readlines()
                chapter_count = int(lines[1].split(": ")[1])
                verse_count = int(lines[2].split(": ")[1])

        # Otherwise, we will need to retrieve each chapter metadata from the API
        else:
            req1_url = f"/books/{book_id}/chapters"
            url = f"{base_url}{kjv_url}{req1_url}"
            chapters_res = requests.get(url, headers=params)
            chapters = chapters_res.json()["data"]

            chapter_count = 0
            verse_count = 0
            for chapter in chapters:
                chapter_id = chapter["id"]
                # Skip the introductory paragraph, if it exists (KJV specific?)
                if "intro" not in chapter_id:
                    req2_url = f"/chapters/{chapter_id}"
                    url = f"{base_url}{kjv_url}{req2_url}"
                    chapter_res = requests.get(url, headers=params)
                    chapter_data = chapter_res.json()["data"]
                    chapter_count += 1
                    verse_count += chapter_data["verseCount"]

        # Generate book-specific meta and append to the overall meta
        book_meta = {}
        book_meta["name"] = book_name
        book_meta["chapters"] = chapter_count
        book_meta["verses"] = verse_count
        meta.append(book_meta)

        # Generate a file report of the book-specific meta
        with open(book_data_path, "w") as out:
            out.write(f"Book name: {book_name}\n")
            out.write(f"Chapter count: {chapter_count}\n")
            out.write(f"Verse count: {verse_count}\n")

    return meta


def get_day_reading_text(meta, b, curr_chapter, day):
    """
    Generate the text for the day's reading, e.g. "Genesis 48-50; Exodus 1-2".

    Args:
        meta (list): The metadata of the books of the Bible in dict format.
        b (int): The index of the current book in the meta. meta[b] = curr_book.
        curr_chapter (int): The index of the current chapter in curr_book.
        day (int): The number of chapters (still) needed to be read in the day.
    
    Returns:
        str: The complete or partial daily reading text, depending on recursion.
    """

    curr_book = meta[b]
    day_readings = ""

    # Just read the number of chapters in the daily reading
    if curr_chapter + day - 1 <= curr_book["chapters"]:
        day_readings += f"{curr_book['name']} "
        if day != 1:
            day_readings += f"{curr_chapter}-{curr_chapter + day - 1}"
        else:
            day_readings += f"{curr_chapter}"
    # We have finished the book, let's move to the next book
    elif curr_chapter + day - 1 > curr_book["chapters"]:
        day_readings += f"{curr_book['name']} "
        if curr_chapter != curr_book["chapters"]:
            day_readings += f"{curr_chapter}-{curr_book['chapters']}; "
        else:
            day_readings += f"{curr_chapter}; "

        # Recurse to get more books needed to be read to be on schedule
        day_readings += get_day_reading_text(
            meta, b + 1, 1, day - (curr_book["chapters"] - curr_chapter) - 1)

    return day_readings


def generate_plan(meta, duration, start, chapters, write=True) -> str:
    """
    Generate a Bible reading plan from the specified arguments.

    Args:
        meta (list): The metadata of the books of the Bible in dict format.
        duration (int): The number of days for the plan.
        start (datetime.datetime): The start date for the plan.
        chapters (int): The total number of chapters for the planned books.
        write (bool): Whether to write the plan to a file.
    
    Returns:
        str: The plan as text (CSV) output.
    """

    # Retrieve the number of chapters needed to be read per day in list form
    try:
        chapters_per_day = utils.utils.split(chapters, duration)
    # If number of days > number of chapters, default to one chapter per day
    except ValueError:
        chapters_per_day = [1 for _ in range(chapters)]

    # We want a CSV file as output
    if write:
        csvf = open("reading_plan.csv", "w", newline="")
    # Instead, generate the plan as text output
    else:
        from io import StringIO
        csvf = StringIO()

    # Write to the plan
    w = csv.writer(csvf, delimiter=',')
    b = 0
    curr_day = start
    curr_book = meta[b]
    curr_chapter = 1
    for i, day in enumerate(chapters_per_day):
        day_readings = get_day_reading_text(meta, b, curr_chapter, day)
        w.writerow([curr_day.strftime("%m/%d/%Y"), day_readings])

        if i != len(chapters_per_day) - 1:
            curr_day += datetime.timedelta(days=1)
            curr_chapter += day
            while curr_chapter > curr_book["chapters"]:
                b = b + 1
                curr_chapter = curr_chapter - curr_book["chapters"]
                curr_book = meta[b]

    if write:
        plan_csv = "Written to file"
        csvf.close()
    else:
        csvf.seek(0)
        plan_csv = csvf.read()
        csvf.close()

    return plan_csv


def process_meta(meta, write=True, **config) -> dict:
    """
    Process the raw metadata into info we want for generating the reading plan.

    Args:
        meta (list): The metadata of the books of the Bible in dict format.
        write (bool): Whether to write the plan to a file.
        config (**kwargs): If "duration" and "start" specified, generate a plan.
    
    Returns:
        dict: The processed metadata.
    """

    processed_meta = {}
    total_chapter_count = 0
    total_verse_count = 0
    for book in meta:
        total_chapter_count += book["chapters"]
        total_verse_count += book["verses"]

    processed_meta["chapters"] = total_chapter_count
    processed_meta["verses"] = total_verse_count

    if "duration" in config and "start" in config:
        duration = config["duration"]
        processed_meta["chapters_per_day"] = total_chapter_count / duration
        processed_meta["verses_per_day"] = total_verse_count / duration

        plan_csv = generate_plan(meta, duration, config["start"],
                                 total_chapter_count, write)
        processed_meta["plan"] = plan_csv

    return processed_meta


def main() -> None:
    parser = argparse.ArgumentParser(description="This script generates a bible\
         plan from user-defined specifications.")
    parser.add_argument(
        "input",
        nargs="?",
        default="config.json",
        help="Path of input config file with the desired specs for the plan.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force metadata retrieval from the Bible API, regardless of cache."
    )
    args = parser.parse_args()

    with open(args.input) as f:
        config = json.load(f)

    books = config["books"]
    duration = config["duration"]
    start = datetime.datetime.strptime(config["start"], "%b-%d-%Y")
    config["start"] = start

    meta = request_metadata(args.force, **config)
    processed_meta = process_meta(meta, write=True, **config)


def run_from_server(cfg_json) -> dict:
    config = json.loads(json.loads(cfg_json))

    books = config["books"]
    duration = config["duration"]
    start = datetime.datetime.strptime(config["start"], "%b-%d-%Y")
    config["start"] = start

    meta = request_metadata(False, **config)
    processed_meta = process_meta(meta, write=False, **config)

    return processed_meta


if __name__ == "__main__":
    main()