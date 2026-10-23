# kometa-config

Collection and poster files for [Kometa](https://kometa.wiki) (formerly Plex Meta Manager), running in Docker on Unraid with its config at `/mnt/user/appdata/plex_meta_manager`. `config.yml` holds API keys and tokens and is not kept here.

| File here | On the server | Library |
|---|---|---|
| `movie_collections.yml` | `Movie_collections.yml` | Movies collections |
| `movie_posters_tmdb.yml` | `Movie_posters_tmdb.yml` | Movies posters |
| `tv_collections.yml` | `TV_collections.yml` | TV Shows collections |
| `tv_posters.yml` | `TV_posters.yml` | TV Shows posters |

## Movie posters

`movie_posters_tmdb.yml` keys every movie by its TMDb id, with the title and year in a comment, sorted by that title:

```yaml
  16314: # 3 Ninjas (1992)
    url_poster: https://theposterdb.com/api/assets/18125/view
```

Every other movie in Plex has a commented-out placeholder in its place in the list. To give one a poster, replace `replaceMe` with the ThePosterDB asset id and remove the leading `# ` from both lines:

```yaml
  # 389: # 12 Angry Men (1957)
  #   url_poster: https://theposterdb.com/api/assets/replaceMe/view
```

Editions of the same movie share a TMDb id, so they use a key like `120 Extended` with a `match:` block on the id and edition.

## Placeholder true-up

`scripts/posters_trueup/` keeps the placeholders in step with Plex. It runs daily at 15:45, before Kometa's 16:00 run, as the Unraid User Script `kometa_posters_trueup` (`/boot/config/plugins/user.scripts/scripts/kometa_posters_trueup/`). `script` is the User Script; it runs `trueup.py` inside the Kometa container, which reads the Plex URL and token from Kometa's own `config.yml` and finds the library named `Movies` there (set `LIBRARY` at the top of the script for another name).

Each run adds a placeholder for every Plex movie whose TMDb id is not in the file and removes placeholders for movies no longer in Plex. Entries with a poster are never changed. It writes only when something changed, keeps the last 7 dated backups, and changes nothing if Plex returns fewer than 1,000 movies; if it would remove more than 25 placeholders, it skips the removals.

### Setting it up on Unraid

You need Kometa running in Docker with its config folder mounted at `/config` (the standard template does this), and the **User Scripts** plugin (install it from the Apps tab).

1. **Check the settings at the top of `trueup.py`.**
   - `LIBRARY` is your movie library's name as it appears under `libraries:` in Kometa's `config.yml` (default `Movies`).
   - `MIN_MOVIES` is a safety floor: if Plex returns fewer movies than this, the script assumes something is wrong and changes nothing. Set it to well under the size of your library (default 1,000).
   - The posters file defaults to `/config/Movie_posters_tmdb.yml`, which is `Movie_posters_tmdb.yml` in Kometa's appdata folder.

2. **Create the posters file**, if you are not starting from this repo's. A file containing only this line is enough; the first run fills in a placeholder for every movie:

   ```yaml
   metadata:
   ```

   Save it as `Movie_posters_tmdb.yml` in Kometa's appdata folder (for example `/mnt/user/appdata/kometa/`).

3. **Add the User Script.** In Settings > User Scripts, choose **Add New Script** and name it `kometa_posters_trueup`. Click the gear icon next to it, choose **Edit Script**, and paste the contents of [`scripts/posters_trueup/script`](scripts/posters_trueup/script). If your Kometa container is not named `Kometa`, change `docker exec -i Kometa` to its name (as shown on the Docker tab).

4. **Put `trueup.py` next to the script.** User Scripts keeps each script in a folder on the flash drive, and `script` reads `trueup.py` from that folder. In the Unraid terminal:

   ```sh
   wget -O /boot/config/plugins/user.scripts/scripts/kometa_posters_trueup/trueup.py \
     https://raw.githubusercontent.com/notryanfraser/kometa-config/main/scripts/posters_trueup/trueup.py
   ```

   If you named the script something else in step 3, use that name in the path here and in `script`.

5. **Run it once.** Back in User Scripts, choose **Run Script**. It should print how many placeholders it added (or `No changes`), and the posters file should now list your movies.

6. **Schedule it.** Set the script's schedule to **Custom** with a cron expression a little before Kometa runs, for example `45 15 * * *` for 15:45 every day when Kometa runs at 16:00, and choose **Apply**.

7. **Point Kometa at the file.** Under your movie library in `config.yml`:

   ```yaml
   libraries:
     Movies:
       metadata_files:
       - file: config/Movie_posters_tmdb.yml
   ```

   Do this once at least one movie has a poster (an uncommented entry). Until then the file has no live entries, and Kometa may report the empty `metadata:` as an error.

To see what a run did, choose **Show Log** next to the script in User Scripts. Backups are saved next to the posters file as `Movie_posters_tmdb.yml.bak-<date>`.
